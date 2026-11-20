#!/usr/bin/env python3
"""Super Dig Dug — Unified build, asset, test, and environment CLI.

Provides the canonical entry points referenced by Makefile:
  status, assets, asset-check, asset-preview, art-viewer,
  rom, test, run, debug, budgets, package, clean
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REQUIRED_TOOLS = {
    "python3": "Host scripting, asset conversion, and pure simulation tests",
    "git": "Version control and build provenance",
    "make": "GNU Make wrapper convenience (optional when invoking tools/sdd.py directly)",
    "gcc": "Host C compiler for native C unit tests",
    "m68k-neogeo-elf-gcc": "ngdevkit 68000 cross-compiler for Neo Geo P-ROM",
    "z80-neogeo-ihx-sdcc": "ngdevkit Z80 compiler (or sdcc) for Neo Geo M-ROM",
    "mame": "Target Neo Geo MVS emulator for runtime verification",
    "aseprite": "Optional pixel-art editor CLI (indexed PNG + JSON fallback supported)",
}


def probe_tool(binary: str) -> dict[str, str | bool | None]:
    path = shutil.which(binary)
    if not path:
        return {"found": False, "path": None, "version": None}
    version = None
    for flag in ("--version", "-version", "-v"):
        try:
            proc = subprocess.run(
                [path, flag],
                capture_output=True,
                text=True,
                timeout=3,
                check=False,
            )
            out = (proc.stdout or proc.stderr or "").strip().splitlines()
            if out:
                version = out[0].strip()
                break
        except Exception:
            continue
    return {"found": True, "path": path, "version": version}


def cmd_status(_args: argparse.Namespace) -> int:
    print("=== Super Dig Dug — Environment & Repository Status ===")
    print(f"Workspace root: {ROOT}")
    print("\nToolchain probe:")
    results = {}
    for binary, role in REQUIRED_TOOLS.items():
        info = probe_tool(binary)
        results[binary] = info
        mark = "OK     " if info["found"] else "MISSING"
        ver = f" ({info['version']})" if info["version"] else ""
        print(f"  [{mark}] {binary:<22} - {role}{ver}")

    palettes = sorted((ROOT / "assets" / "palettes").glob("*.json"))
    exports = sorted((ROOT / "assets" / "export").glob("*.png"))
    print(f"\nAssets summary: {len(palettes)} palette(s), {len(exports)} exported sheet(s)")
    if not results["m68k-neogeo-elf-gcc"]["found"] or not results["mame"]["found"]:
        print(
            "\nNote: Target 68000/MAME tools are not installed in this environment.\n"
            "Host-side asset generation, validation, C/S-ROM bitplane packing, and pure\n"
            "gameplay tests can run here; MAME boot/runtime checks must run on a machine\n"
            "configured per MAME-SETUP.md."
        )
    return 0


def unimplemented_stage(name: str, detail: str, need_tools: list[str] | None = None) -> int:
    missing = [t for t in (need_tools or []) if not shutil.which(t)]
    print(f"[{name}] {detail}")
    if missing:
        print(f"[{name}] Blocked in current environment by missing binary(s): {', '.join(missing)}")
        return 2
    return 0


def cmd_clean(_args: argparse.Namespace) -> int:
    for rel in ("build", "dist"):
        target = ROOT / rel
        if target.is_dir():
            for child in target.iterdir():
                if child.name == ".gitkeep":
                    continue
                if child.is_dir():
                    shutil.rmtree(child)
                else:
                    child.unlink()
    print("[clean] Cleared build/ and dist/ artifacts.")
    return 0


def cmd_test(_args: argparse.Namespace) -> int:
    import unittest

    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1


def cmd_disasm(args: argparse.Namespace) -> int:
    import disasm_digdug1982

    rom_path = Path(args.rom).resolve()
    if not rom_path.exists():
        print(f"[disasm] ROM input not found: {rom_path}", file=sys.stderr)
        return 1
    return disasm_digdug1982.run_disassembly(rom_path, ROOT / "build" / "disasm_1982")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sdd.py",
        description="Super Dig Dug build, asset, validation, and test CLI.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    dis_p = sub.add_parser("disasm", help="Disassemble 1982 Dig Dug Z80 ROMs into build/disasm_1982/")
    dis_p.add_argument("--rom", required=True, help="Path to digdug.zip, extracted dir, or digdug_b64.txt")

    for name, help_text in [
        ("status", "Inspect repository layout and installed toolchain versions"),
        ("assets", "Export editable masters, generate terrain masks, and pack C-ROM/S-ROM data"),
        ("asset-check", "Validate palettes, transparency, bounds, masks, and round-trip tile decoding"),
        ("asset-preview", "Render 1x and 8x nearest-neighbor contact sheets and animation previews"),
        ("art-viewer", "Build the Neo Geo MVS diagnostics & art-viewer ROM"),
        ("rom", "Build the Super Dig Dug Neo Geo MVS development ROM"),
        ("test", "Run host-side unit, asset, and deterministic simulation tests"),
        ("run", "Launch the built ROM in MAME using isolated config/NVRAM paths"),
        ("debug", "Launch the built ROM in MAME with debugger enabled"),
        ("budgets", "Report static RAM, ROM size, tile counts, and scanline sprite-strip maxima"),
        ("package", "Assemble a clean versioned distribution archive in dist/"),
        ("clean", "Remove generated artifacts in build/ and dist/"),
    ]:
        sub.add_parser(name, help=help_text)

    return parser


def main(argv: list[str] | None = None) -> int:
    sys.path.insert(0, str(ROOT / "tools"))
    parser = build_parser()
    args = parser.parse_args(argv)
    cmd = args.command

    if cmd == "status":
        return cmd_status(args)
    if cmd == "clean":
        return cmd_clean(args)
    if cmd == "disasm":
        return cmd_disasm(args)
    if cmd == "test":
        return cmd_test(args)
    if cmd in ("assets", "asset-check", "asset-preview"):
        return unimplemented_stage(
            cmd,
            "Repository bootstrapped (M0/B0 scaffold). Next step: implement tools/assets/ pipeline.",
        )
    if cmd == "budgets":
        return unimplemented_stage(
            cmd,
            "Repository bootstrapped. Next step: add RAM/ROM map & scanline strip budget reporter.",
        )
    if cmd in ("art-viewer", "rom"):
        return unimplemented_stage(
            cmd,
            "Target ROM build requires ngdevkit 68000/Z80 toolchain and M0/art-viewer C sources.",
            need_tools=["m68k-neogeo-elf-gcc"],
        )
    if cmd in ("run", "debug"):
        return unimplemented_stage(
            cmd,
            "Emulator launch requires a proven MAME setup (see MAME-SETUP.md).",
            need_tools=["mame"],
        )
    if cmd == "package":
        return unimplemented_stage(
            cmd,
            "Packaging awaits M0/B0 build outputs.",
        )
    return 1


if __name__ == "__main__":
    sys.exit(main())
