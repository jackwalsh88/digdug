#!/usr/bin/env python3
"""Scripted, headless MAME runs for Super Dig Dug.

A scenario is a list of timed events (frame numbers count from machine start):
    ("press", frame, field, hold_frames)   hold an input for N frames
    ("snap",  frame)                       save a PNG snapshot
    ("peek",  frame, label, address, size) log a main-CPU memory value; the
                                           address may be a linker symbol name
The run ends after the last event. Snapshots, the memory log and an optional
WAV capture land in build/smoke/<scenario>/.

Usage:
    python3 tools/mame_smoke.py boot
    python3 tools/mame_smoke.py play --wav
    python3 tools/mame_smoke.py play --avi     (large file; compress with ffmpeg)
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# MAME field name -> I/O port tag for the neogeo (MVS) driver.
FIELDS = {
    "Coin 1": ":AUDIO_COIN",
    "Coin 2": ":AUDIO_COIN",
    "1 Player Start": ":edge:joy:START",
    "2 Players Start": ":edge:joy:START",
    "Next Game": ":SYSTEM",
    "Previous Game": ":SYSTEM",
    **{f"P1 {b}": ":edge:joy:JOY1" for b in ("Up", "Down", "Left", "Right", "A", "B", "C", "D")},
    **{f"P2 {b}": ":edge:joy:JOY2" for b in ("Up", "Down", "Left", "Right", "A", "B", "C", "D")},
}

BIOS_USER_MODE = 0x10FDAF
BRAM_CREDITS = 0xD00034

SCENARIOS: dict[str, list[tuple]] = {
    # Cold boot, title screen, then the attract demo.
    "boot": [
        ("snap", 120),
        ("snap", 300),
        ("snap", 600),
        ("snap", 900),
        ("peek", 900, "vblanks", "g_vblank_counter", 4),
        ("peek", 900, "ticks", "g_tick_counter", 4),
        ("peek", 900, "missed_frames", "g_missed_frames", 4),
    ],
    # Coin, 1P start, dig down and right, pump.
    "play": [
        ("snap", 150),
        ("peek", 199, "credits_before_coin", BRAM_CREDITS, 1),
        ("press", 200, "Coin 1", 6),
        ("peek", 260, "credits_after_coin", BRAM_CREDITS, 1),
        ("peek", 260, "user_mode_title", BIOS_USER_MODE, 1),
        ("snap", 280),
        ("press", 300, "1 Player Start", 6),
        ("peek", 330, "credits_after_start", BRAM_CREDITS, 1),
        ("peek", 330, "user_mode_game", BIOS_USER_MODE, 1),
        ("snap", 340),
        ("press", 420, "P1 Down", 120),
        ("snap", 520),
        ("press", 545, "P1 Right", 90),
        ("snap", 620),
        ("press", 640, "P1 A", 6),
        ("press", 660, "P1 A", 6),
        ("press", 680, "P1 A", 6),
        ("snap", 700),
        ("press", 720, "P1 Left", 200),
        ("snap", 900),
        ("peek", 900, "vblanks_a", "g_vblank_counter", 4),
        ("peek", 900, "ticks_a", "g_tick_counter", 4),
        ("peek", 1500, "vblanks_b", "g_vblank_counter", 4),
        ("peek", 1500, "ticks_b", "g_tick_counter", 4),
        ("peek", 1500, "missed_frames", "g_missed_frames", 4),
        ("snap", 1500),
    ],
    # Open the art viewer from the title with P1 SELECT ("Next Game").
    "viewer": [
        ("press", 150, "Next Game", 6),
        ("snap", 200),
        ("press", 210, "P1 Down", 4),
        ("press", 230, "P1 A", 4),
        ("snap", 260),
        ("press", 270, "P1 D", 4),
        ("snap", 300),
        ("press", 310, "Next Game", 6),
        ("snap", 360),
    ],
}


def _soak(frames: int = 18000) -> list[tuple]:
    """Five emulated minutes: coin + start whenever idle, constant stick and pump input."""
    events: list[tuple] = []
    moves = ["P1 Down", "P1 Right", "P1 Up", "P1 Left", "P1 Right", "P1 Down", "P1 Left", "P1 Up"]
    for i, start in enumerate(range(240, frames - 200, 97)):
        events.append(("press", start, moves[i % len(moves)], 70))
        events.append(("press", start + 75, "P1 A", 5))
        events.append(("press", start + 85, "P1 A", 5))
    for start in range(200, frames - 200, 1500):
        events.append(("press", start, "Coin 1", 6))
        events.append(("press", start + 60, "1 Player Start", 6))
    for frame in range(3000, frames, 3000):
        events.append(("snap", frame))
        events.append(("peek", frame, "vblanks", "g_vblank_counter", 4))
        events.append(("peek", frame, "ticks", "g_tick_counter", 4))
        events.append(("peek", frame, "missed_frames", "g_missed_frames", 4))
    return events


SCENARIOS["soak"] = _soak()


def _symbols(cart: str) -> dict[str, int]:
    """Read symbol addresses from the linker map's ELF (build/<cart>.elf)."""
    elf = ROOT / "build" / f"{cart}.elf"
    nm = next((t for t in ("m68k-neogeo-elf-nm", "m68k-elf-nm", "m68k-linux-gnu-nm") if shutil.which(t)), None)
    if not nm or not elf.is_file():
        return {}
    out = subprocess.run([nm, str(elf)], capture_output=True, text=True, check=False).stdout
    table = {}
    for line in out.splitlines():
        parts = line.split()
        if len(parts) == 3:
            table[parts[2]] = int(parts[0], 16)
    return table


def _lua(events: list[tuple], symbols: dict[str, int]) -> str:
    last = max(e[1] + (e[3] if e[0] == "press" else 0) for e in events) + 2
    lines = [
        "local cpu = manager.machine.devices[':maincpu']",
        "local mem = cpu.spaces['program']",
        "local ports = manager.machine.ioport.ports",
        "local frame = 0",
        "local function field(tag, name) return ports[tag].fields[name] end",
        "local actions = {}",
        "local function at(f, fn) actions[f] = actions[f] or {}; table.insert(actions[f], fn) end",
    ]
    for ev in events:
        kind, frame = ev[0], ev[1]
        if kind == "press":
            name, hold = ev[2], ev[3]
            tag = FIELDS[name]
            lines.append(f"at({frame}, function() field('{tag}', '{name}'):set_value(1) end)")
            lines.append(f"at({frame + hold}, function() field('{tag}', '{name}'):set_value(0) end)")
        elif kind == "snap":
            lines.append(f"at({frame}, function() manager.machine.video:snapshot() end)")
        elif kind == "peek":
            label, addr, size = ev[2], ev[3], ev[4]
            if isinstance(addr, str):
                addr = symbols[addr]
            reader = {1: "read_u8", 2: "read_u16", 4: "read_u32"}[size]
            lines.append(
                f"at({frame}, function() print(string.format('PEEK {label} frame={frame} "
                f"value=0x%X', mem:{reader}(0x{addr:X}))) end)"
            )
    lines += [
        "emu.register_frame_done(function()",
        "  frame = frame + 1",
        "  local list = actions[frame]",
        "  if list then for _, fn in ipairs(list) do fn() end end",
        f"  if frame >= {last} then manager.machine:exit() end",
        "end)",
    ]
    return "\n".join(lines) + "\n"


def run(name: str, wav: bool, cart: str, avi: bool = False) -> int:
    mame = shutil.which("mame") or ("/usr/games/mame" if Path("/usr/games/mame").exists() else None)
    if not mame:
        print("[smoke] mame not found on PATH", file=sys.stderr)
        return 2
    out = ROOT / "build" / "smoke" / name
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    script = out / "scenario.lua"
    script.write_text(_lua(SCENARIOS[name], _symbols(cart)))

    cmd = [
        mame, "neogeo", cart,
        "-hashpath", str(ROOT / "mame" / "hash"),
        "-rompath", str(ROOT / "mame" / "roms"),
        "-cfg_directory", str(out / "cfg"),
        "-nvram_directory", str(out / "nvram"),
        "-snapshot_directory", str(out / "snap"),
        "-video", "none", "-nothrottle", "-skip_gameinfo",
        "-autoboot_script", str(script),
    ]
    cmd += ["-sound", "none"]
    if wav:
        cmd += ["-wavwrite", str(out / "audio.wav")]
    if avi:
        # MAME resolves -aviwrite relative to the snapshot directory.
        cmd += ["-aviwrite", "capture.avi"]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    log = proc.stdout + proc.stderr
    (out / "mame.log").write_text(log)
    for line in log.splitlines():
        if line.startswith("PEEK"):
            print(line)
    snaps = sorted((out / "snap").rglob("*.png"))
    print(f"[smoke] {name}: exit={proc.returncode}, {len(snaps)} snapshots in {out.relative_to(ROOT)}/snap")
    return proc.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("scenario", choices=sorted(SCENARIOS))
    parser.add_argument("--wav", action="store_true", help="record emulated audio to audio.wav")
    parser.add_argument("--avi", action="store_true", help="record uncompressed video+audio to snap/capture.avi")
    parser.add_argument("--cart", default="superdigdug")
    args = parser.parse_args()
    return run(args.scenario, args.wav, args.cart, args.avi)


if __name__ == "__main__":
    sys.exit(main())
