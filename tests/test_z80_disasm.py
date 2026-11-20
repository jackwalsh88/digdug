"""Unit tests for the 1982 Dig Dug Z80 disassembler and PROM/WSG decoders."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import disasm_digdug1982 as d82  # noqa: E402


class TestZ80Disassembler(unittest.TestCase):
    def test_unprefixed_and_namco_hw_symbols(self) -> None:
        # DI ; LD SP,$8FFF ; XOR A ; LD ($6820),A ; JP $0100
        code = bytes([0xF3, 0x31, 0xFF, 0x8F, 0xAF, 0x32, 0x20, 0x68, 0xC3, 0x00, 0x01])
        m0, l0, t0 = d82.decode_z80_instruction(code, 0)
        self.assertEqual((m0, l0, t0), ("DI", 1, None))

        m1, l1, t1 = d82.decode_z80_instruction(code, 1)
        self.assertEqual((m1, l1, t1), ("LD SP,$8FFF", 3, None))

        m2, l2, t2 = d82.decode_z80_instruction(code, 4)
        self.assertEqual((m2, l2, t2), ("XOR A", 1, None))

        m3, l3, t3 = d82.decode_z80_instruction(code, 5)
        self.assertEqual((m3, l3, t3), ("LD (LAT_IRQ_ENABLE_CPU0 ($6820)),A", 3, None))

        m4, l4, t4 = d82.decode_z80_instruction(code, 8)
        self.assertEqual((m4, l4, t4), ("JP $0100", 3, 0x0100))

    def test_ed_cb_and_indexed_opcodes(self) -> None:
        # IM 1 ; LDIR ; BIT 7,(HL) ; LD A,(IX+$04) ; SET 3,(IY-$02)
        code = bytes([
            0xED, 0x56,
            0xED, 0xB0,
            0xCB, 0x7E,
            0xDD, 0x7E, 0x04,
            0xFD, 0xCB, 0xFE, 0xDE,
        ])
        self.assertEqual(d82.decode_z80_instruction(code, 0)[:2], ("IM 1", 2))
        self.assertEqual(d82.decode_z80_instruction(code, 2)[:2], ("LDIR", 2))
        self.assertEqual(d82.decode_z80_instruction(code, 4)[:2], ("BIT 7,(HL)", 2))
        self.assertEqual(d82.decode_z80_instruction(code, 6)[:2], ("LD A,(IX+$04)", 3))
        self.assertEqual(d82.decode_z80_instruction(code, 9)[:2], ("SET 3,(IY-$02)", 4))

    def test_relative_branches_and_two_pass_labels(self) -> None:
        # 0000: LD B,$04 ; 0002: NOP ; 0003: DJNZ $0002 ; 0005: RET
        code = bytes([0x06, 0x04, 0x00, 0x10, 0xFD, 0xC9])
        listing = d82.disassemble_region(code, 0x0000, "CPU0_TEST")
        self.assertIn("CPU0_TEST_RESET_0000:", listing)
        self.assertIn("L_0002:", listing)
        self.assertIn("DJNZ L_0002", listing)

    def test_palette_and_wsg_prom_decoders(self) -> None:
        pal = d82.decode_namco_palette_prom(bytes([0x00, 0xFF] + [0x07] * 30))
        self.assertEqual(len(pal), 32)
        self.assertEqual(pal[0]["hex"], "#000000")
        self.assertEqual(pal[1]["hex"], "#FFFFFF")
        self.assertEqual(pal[2]["hex"], "#FF0000")

        wsg = d82.decode_wsg_wavetables(bytes(range(256)))
        self.assertEqual(len(wsg), 8)
        self.assertEqual(len(wsg[0]), 32)
        self.assertEqual(wsg[0][:4], [0, 1, 2, 3])
        self.assertEqual(wsg[0][16], 0)


if __name__ == "__main__":
    unittest.main()
