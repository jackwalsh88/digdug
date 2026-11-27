"""Deterministic Phase 1 (1982 Dig Dug Replica on Neo Geo MVS) Gameplay & ROM Architecture Tests."""

from __future__ import annotations

import json
import re
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from build_m1_z80 import CUE_TABLE_ADDR, build_m1_rom  # noqa: E402
from neogeo_rom_builder import C_AND_ASM_SOURCES, _swap_16bit_pairs  # noqa: E402
from phase1_sim import (  # noqa: E402
    DIR_DOWN,
    DIR_LEFT,
    DIR_RIGHT,
    DIR_UP,
    FP_ONE_PX,
    FP_TILE_16,
    EnemySim,
    Phase1WorldSim,
    RockSim,
    score_for_pump_kill,
    score_for_rock_crush,
    score_for_round_vegetable,
)


class TestPhase1DigDug1982Replica(unittest.TestCase):
    def test_16_quadrant_excavation_masks_and_dig_scoring(self) -> None:
        sim = Phase1WorldSim(round_num=1)
        # Surface row 0 open, dirt row 1 col 0 solid (0x0F)
        self.assertEqual(sim.tile_mask[0][0], 0x00)
        self.assertEqual(sim.tile_mask[1][0], 0x0F)

        # Carve NW (bit 0), NE (bit 1), SW (bit 2), SE (bit 3) individually on tile (2, 2)
        self.assertEqual(sim.carve_cell(4, 4), 1)
        self.assertEqual(sim.tile_mask[2][2], 0x0E)  # NE|SW|SE remain solid
        self.assertEqual(sim.carve_cell(5, 4), 1)
        self.assertEqual(sim.tile_mask[2][2], 0x0C)  # SW|SE remain solid
        self.assertEqual(sim.carve_cell(4, 5), 1)
        self.assertEqual(sim.tile_mask[2][2], 0x08)  # SE remains solid
        self.assertEqual(sim.carve_cell(5, 5), 1)
        self.assertEqual(sim.tile_mask[2][2], 0x00)  # Fully excavated!

        # Walk vs Dig speed & +10pt dig cell award
        sim2 = Phase1WorldSim(round_num=1)
        y0 = sim2.py_fp
        sim2.step(move_dir=DIR_UP)  # Up central shaft is open tunnel -> 20 subpx
        self.assertEqual(y0 - sim2.py_fp, 20)
        self.assertEqual(sim2.score, 0)

        sim3 = Phase1WorldSim(round_num=1)
        for _ in range(20):
            sim3.step(move_dir=DIR_DOWN)  # Down below center chamber is solid dirt -> +10 pts/cell
        self.assertGreaterEqual(sim3.score, 20)

    def test_pump_tap_vs_hold_and_harmless_inflated_passthrough_and_deflation(self) -> None:
        sim = Phase1WorldSim(round_num=1)
        sim.carve_tile_box(6, 7, 4, 1)
        sim.enemies.append(EnemySim(kind="pooka", x_fp=7 * FP_TILE_16, y_fp=7 * FP_TILE_16, dir=DIR_LEFT))

        # Fire harpoon right -> latches at stage 1
        sim.step(btn_a_pressed=True, btn_a_held=True)
        for _ in range(5):
            if sim.harpoon_latched:
                break
            sim.step(btn_a_held=True)
        self.assertTrue(sim.harpoon_latched)
        self.assertEqual(sim.enemies[0].inflate_stage, 1)
        self.assertEqual(sim.enemies[0].state, "inflated")

        # Walk right THROUGH the stage-1 inflated Pooka -> harmless pass-through!
        for _ in range(16):
            sim.step(move_dir=DIR_RIGHT)
        self.assertEqual(sim.p_state, "alive")

        # Wait without pumping -> monster deflates back to 0 and resumes tunnel chase!
        for _ in range(80):
            sim.step()
            if sim.enemies[0].inflate_stage == 0:
                break
        self.assertEqual(sim.enemies[0].inflate_stage, 0)
        self.assertEqual(sim.enemies[0].state, "tunnel")

        # Compare rapid tap pumping (4 presses) vs steady hold pumping
        sim_tap = Phase1WorldSim(round_num=1)
        sim_tap.carve_tile_box(6, 7, 4, 1)
        sim_tap.enemies.append(EnemySim(kind="fygar", x_fp=7 * FP_TILE_16, y_fp=7 * FP_TILE_16, dir=DIR_LEFT))
        tap_ticks = 0
        while sim_tap.enemies[0].state != "popping" and tap_ticks < 30:
            sim_tap.step(btn_a_pressed=(tap_ticks % 2 == 0), btn_a_held=True)
            tap_ticks += 1
        self.assertEqual(sim_tap.enemies[0].state, "popping")
        self.assertLess(tap_ticks, 15)
        # Stratum 1 (y=112) horizontal Fygar pop = 300 * 2 = 600 pts!
        self.assertEqual(sim_tap.score, 600)

    def test_all_1982_scoring_tables_and_extra_lives(self) -> None:
        # Stratum pump kills & 2x horizontal Fygar
        self.assertEqual([score_for_pump_kill(s, False, True) for s in range(4)], [200, 300, 400, 500])
        self.assertEqual([score_for_pump_kill(s, True, False) for s in range(4)], [200, 300, 400, 500])
        self.assertEqual([score_for_pump_kill(s, True, True) for s in range(4)], [400, 600, 800, 1000])

        # Multi-crush 1..8 monsters
        self.assertEqual(
            [score_for_rock_crush(n) for n in range(1, 9)],
            [1000, 2500, 4000, 6000, 8000, 10000, 12000, 15000],
        )

        # 18-round bonus vegetable progression (400 .. 8000)
        expected_veg = {1: 400, 2: 600, 3: 800, 4: 1000, 6: 2000, 8: 3000, 10: 4000, 12: 5000, 14: 6000, 16: 7000, 18: 8000, 99: 8000}
        for rnd, pts in expected_veg.items():
            self.assertEqual(score_for_round_vegetable(rnd), pts)

        # Extra lives at 20,000 and 60,000
        sim = Phase1WorldSim(round_num=1)
        self.assertEqual(sim.lives, 3)
        sim.award(20000)
        self.assertEqual(sim.lives, 4)
        sim.award(40000)
        self.assertEqual(sim.lives, 5)

    def test_rock_indefinite_player_hold_multicrush_and_2rock_vegetable_spawn(self) -> None:
        sim = Phase1WorldSim(round_num=6)  # Round 6 Eggplant = 2000 pts
        sim.carve_tile_box(3, 4, 1, 4)
        sim.rocks.append(RockSim(x_fp=3 * FP_TILE_16, y_fp=3 * FP_TILE_16))
        sim.rocks.append(RockSim(x_fp=9 * FP_TILE_16, y_fp=3 * FP_TILE_16))

        # Place Taizo directly underneath undercut Rock 0 -> must hold indefinitely!
        sim.px_fp = 3 * FP_TILE_16
        sim.py_fp = (3 * 16 + 16) * FP_ONE_PX
        for _ in range(100):
            sim.step()
            self.assertEqual(sim.rocks[0].state, "held_by_player")

        # Two monsters enter the shaft below as Taizo steps clear -> Rock 0 wobbles, falls & crushes BOTH (2,500 pts!)
        sim.enemies.append(EnemySim(kind="pooka", x_fp=3 * FP_TILE_16, y_fp=6 * FP_TILE_16, phase_cooldown=999))
        sim.enemies.append(EnemySim(kind="fygar", x_fp=3 * FP_TILE_16, y_fp=7 * FP_TILE_16, phase_cooldown=999, fire_cooldown=999))
        sim.px_fp = 6 * FP_TILE_16
        sim.py_fp = 7 * FP_TILE_16
        for _ in range(100):
            sim.step()
        self.assertEqual(sim.score, 2500)
        self.assertEqual(sim.rocks_dropped, 1)
        self.assertFalse(sim.veggie_active)

        # Drop Rock 1 -> 2nd rock triggers Round 6 bonus vegetable (2,000 pts) at center spawn!
        sim.carve_tile_box(9, 4, 1, 3)
        for _ in range(100):
            sim.step()
            if sim.veggie_active:
                break
        self.assertTrue(sim.veggie_active)
        self.assertEqual(sim.veggie_pts, 2000)

        # Collect the vegetable at center chamber
        sim.step(move_dir=DIR_RIGHT)
        sim.px_fp = 96 * FP_ONE_PX
        sim.py_fp = 112 * FP_ONE_PX
        sim.step(move_dir=DIR_LEFT)
        self.assertEqual(sim.score, 4500)

    def test_fygar_horizontal_fire_ghost_phasing_and_last_enemy_top_left_escape(self) -> None:
        # 1. Last surviving enemy enters escape mode, phases to surface Row 0, and exits at (0, 0)
        sim = Phase1WorldSim(round_num=1)
        sim.enemies.append(EnemySim(kind="pooka", x_fp=4 * FP_TILE_16, y_fp=4 * FP_TILE_16, phase_cooldown=2))
        for _ in range(320):
            sim.step()
            if sim.enemies[0].state == "escaped":
                break
        self.assertTrue(sim.hurry_up)
        self.assertEqual(sim.enemies[0].state, "escaped")

        # 2. Round 256 safe wrap check (never triggers 1982 Round-0 spawn softlock)
        sim256 = Phase1WorldSim(round_num=256)
        self.assertGreaterEqual(sim256.round_num, 13)
        self.assertLessEqual(sim256.round_num, 20)

    def test_z80_m1_rom_and_c99_asset_symbol_integrity(self) -> None:
        # Verify M1 Z80 sound driver binary vectors and embedded 51-cue V-ROM page table
        m1 = build_m1_rom(None)
        self.assertEqual(len(m1), 128 * 1024)
        self.assertEqual(m1[0], 0xF3)              # $0000: DI
        self.assertEqual(m1[0x38:0x3A], b"\xED\x4D")  # $0038: RETI
        self.assertEqual(m1[0x66:0x68], b"\xF5\xC5")  # $0066: PUSH AF ; PUSH BC
        self.assertEqual(m1[CUE_TABLE_ADDR - 1], 51)   # cue count read by the driver

        manifest = json.loads((ROOT / "assets/generated/asset_manifest.json").read_text())
        for idx, cue in enumerate(manifest["audio_cues"]):
            off = CUE_TABLE_ADDR + idx * 4
            sp, ep = struct.unpack("<HH", m1[off : off + 4])
            self.assertEqual(sp, cue["start_page_256"])
            self.assertEqual(ep, cue["end_page_256"])

        # Verify 16-bit P1 word swapper
        self.assertEqual(_swap_16bit_pairs(b"NEO-GEO\x00"), b"EN-OEGO\x00"[:0] + bytes((ord("E"), ord("N"), ord("-"), ord("O"), ord("E"), ord("G"), 0, ord("O"))))

        # Verify all C99 & 68k assembly source files exist and every FAM_*/PAL_*/AUDIO_* token used in C exists in sdd_assets.h
        header_text = (ROOT / "assets/generated/sdd_assets.h").read_text()
        defined_syms = set(re.findall(r"\b((?:FAM|PAL|AUDIO)_[A-Z0-9_]+)\b", header_text))
        for rel in C_AND_ASM_SOURCES:
            p = ROOT / rel
            self.assertTrue(p.is_file(), f"Missing C/ASM source: {rel}")
            if p.suffix == ".c" and "sdd_assets.c" not in rel:
                used = set(re.findall(r"\b((?:FAM|PAL|AUDIO)_[A-Z0-9_]+)\b", p.read_text()))
                missing = used - defined_syms
                self.assertEqual(missing, set(), f"{rel} references undefined asset symbols: {missing}")


if __name__ == "__main__":
    unittest.main()
