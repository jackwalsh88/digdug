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

    gen_h = ROOT / "assets" / "generated" / "sdd_assets.h"
    reviews = sorted((ROOT / "assets" / "review").glob("*.png"))
    print(
        f"\nAssets summary: pack_catalog.jsonl={'present' if (ROOT / 'assets' / 'pack_catalog.jsonl').is_file() else 'missing'}, "
        f"sdd_assets.h={'generated' if gen_h.is_file() else 'pending'}, "
        f"{len(reviews)} review sheet(s)"
    )
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
    if not result.wasSuccessful():
        return 1

    # Also compile & execute native C99 engine unit tests when gcc or clang is available
    host_cc = shutil.which("gcc") or shutil.which("clang")
    if host_cc:
        build_dir = ROOT / "build"
        build_dir.mkdir(parents=True, exist_ok=True)
        out_bin = build_dir / "c_test_phase1"
        c_sources = [
            "tests/c_test_phase1.c",
            "src/platform/neogeo/neogeo_platform.c",
            "src/audio/sdd_audio.c",
            "src/world/sdd_world.c",
            "src/data/dd1982_tables.c",
            "src/score/sdd_score.c",
            "src/actors/sdd_player.c",
            "src/actors/sdd_rocks.c",
            "src/actors/sdd_enemies.c",
            "src/combat/sdd_pump.c",
            "src/render/sdd_render.c",
            "src/game/art_viewer.c",
            "src/game/sdd_game.c",
            "assets/generated/sdd_assets.c",
        ]
        compile_cmd = [
            host_cc,
            "-std=c99",
            "-O2",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-DSDD_HOST_TEST=1",
            *[str(ROOT / s) for s in c_sources],
            "-o",
            str(out_bin),
        ]
        proc = subprocess.run(compile_cmd, cwd=str(ROOT), capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            print(proc.stderr or proc.stdout, file=sys.stderr)
            return proc.returncode
        run_proc = subprocess.run([str(out_bin)], cwd=str(ROOT), check=False)
        if run_proc.returncode != 0:
            return run_proc.returncode
    else:
        print("[test] Host C compiler (gcc/clang) not installed in container; Python parity & Z80 tests passed.")
    return 0


def cmd_disasm(args: argparse.Namespace) -> int:
    import disasm_digdug1982

    rom_path = Path(args.rom).resolve()
    if not rom_path.exists():
        print(f"[disasm] ROM input not found: {rom_path}", file=sys.stderr)
        return 1
    return disasm_digdug1982.run_disassembly(rom_path, ROOT / "build" / "disasm_1982")


def cmd_assets(args: argparse.Namespace) -> int:
    from assets.pack_pipeline import build_all_assets

    manifest = build_all_assets(getattr(args, "pack", None))
    counts = manifest["counts"]
    print(
        f"[assets] Mode: {manifest['asset_source_mode']} "
        f"(approval_status={manifest['approval_status']})"
    )
    print(
        f"[assets] Compiled {counts['families']} families, "
        f"{counts['frames']} frames -> "
        f"{counts['c_tiles_16x16']} C-ROM tiles ({counts['c1_bytes'] // 1024} KB C1 + {counts['c2_bytes'] // 1024} KB C2), "
        f"{counts['s_tiles_8x8']} S-ROM tiles ({counts['s1_bytes'] // 1024} KB S1), "
        f"{counts['runtime_audio_cues']} V-ROM ADPCM-A cues ({counts['v1_bytes'] // 1024} KB V1)."
    )
    return 0


def cmd_asset_check(_args: argparse.Namespace) -> int:
    from assets.pack_pipeline import GENERATED_DIR, build_all_assets, run_asset_check

    if not (GENERATED_DIR / "asset_manifest.json").is_file():
        print("[asset-check] Generated assets not found; building from catalog first...")
        build_all_assets(None)
    passed, report = run_asset_check()
    if passed:
        print(
            f"[asset-check] PASS — {report['c_tiles_verified']} C-ROM 16x16 tiles, "
            f"{report['s_tiles_verified']} S-ROM 8x8 tiles, "
            f"{report['occupancy_tiles_verified']} terrain occupancy masks, "
            f"{report['intentional_blank_frames']} intentional blanks, and "
            f"{report['audio_cues_verified']} 256B-aligned V-ROM cues verified."
        )
        return 0
    print(f"[asset-check] FAIL — {len(report['errors'])} error(s):", file=sys.stderr)
    for err in report["errors"][:25]:
        print(f"  - {err}", file=sys.stderr)
    return 1


def cmd_asset_preview(_args: argparse.Namespace) -> int:
    from assets.pack_pipeline import GENERATED_DIR, build_all_assets, run_asset_preview

    if not (GENERATED_DIR / "asset_manifest.json").is_file():
        build_all_assets(None)
    written = run_asset_preview()
    print(f"[asset-preview] Wrote {len(written)} 1x/8x decoded review sheet(s) to assets/review/:")
    for p in written:
        print(f"  - {p.relative_to(ROOT)}")
    return 0


def cmd_budgets(_args: argparse.Namespace) -> int:
    from assets.pack_pipeline import GENERATED_DIR, build_all_assets, run_budgets

    if not (GENERATED_DIR / "asset_manifest.json").is_file():
        build_all_assets(None)
    rep = run_budgets()
    crom = rep["rom_regions"]["C1_C2_sprites_16x16"]
    srom = rep["rom_regions"]["S1_fix_8x8"]
    vrom = rep["rom_regions"]["V1_ym2610_adpcm"]
    ram = rep["work_ram"]
    strips = rep["scanline_sprite_strips"]
    print("=== Super Dig Dug — Neo Geo MVS Hardware Budget Report ===")
    print(
        f"  C1/C2 Sprite ROM : {crom['used_tiles']} / 16384 tiles "
        f"({crom['c1_used_bytes'] // 1024} KB / {crom['c1_chip_bytes'] // 1024} KB per chip, {crom['utilization_pct']}%)"
    )
    print(
        f"  S1 FIX ROM       : {srom['used_tiles']} / 4096 tiles "
        f"({srom['used_bytes'] // 1024} KB / {srom['chip_bytes'] // 1024} KB, {srom['utilization_pct']}%)"
    )
    print(
        f"  V1 ADPCM-A ROM   : {vrom['cues']} cues "
        f"({vrom['used_bytes'] // 1024} KB / {vrom['chip_bytes'] // 1024} KB)"
    )
    print(
        f"  68000 Work RAM   : {ram['total_estimated_bytes']} / 62208 bytes ({ram['utilization_pct']}%)"
    )
    print(
        f"  Worst Scanline   : {strips['worst_case_strips']} / 84 eng ceiling (96 hw max) -> "
        f"{'PASS' if strips['within_eng_ceiling_84'] else 'OVER BUDGET'}"
    )
    return 0 if strips["within_eng_ceiling_84"] else 1


def cmd_rom(viewer_only: bool) -> int:
    from neogeo_rom_builder import build_cartridge

    return build_cartridge(viewer_only=viewer_only)


def cmd_run(debug_mode: bool) -> int:
    if not shutil.which("mame"):
        return unimplemented_stage(
            "debug" if debug_mode else "run",
            "Emulator launch requires MAME and neogeo.zip BIOS (see MAME-SETUP.md).",
            need_tools=["mame"],
        )
    rom_zip = ROOT / "mame" / "roms" / "superdigdug.zip"
    if not rom_zip.is_file():
        rc = cmd_rom(viewer_only=False)
        if rc != 0:
            return rc
    launcher = ROOT / "mame" / "run_mame.sh"
    extra = "-debug" if debug_mode else ""
    return subprocess.call(["bash", str(launcher), "superdigdug", extra], cwd=str(ROOT))


def cmd_package(_args: argparse.Namespace) -> int:
    import zipfile

    dist_dir = ROOT / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)
    archive = dist_dir / "super-dig-dug-phase1-src-and-tools.zip"
    tracked = subprocess.run(
        ["git", "ls-files"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for rel in tracked:
            p = ROOT / rel
            if p.is_file():
                zf.write(p, arcname=f"super-dig-dug/{rel}")
        rom_zip = ROOT / "mame" / "roms" / "superdigdug.zip"
        hash_xml = ROOT / "mame" / "hash" / "neogeo.xml"
        if rom_zip.is_file():
            zf.write(rom_zip, arcname="super-dig-dug/mame/roms/superdigdug.zip")
        if hash_xml.is_file():
            zf.write(hash_xml, arcname="super-dig-dug/mame/hash/neogeo.xml")
    print(f"[package] Created clean distribution archive -> {archive.relative_to(ROOT)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sdd.py",
        description="Super Dig Dug build, asset, validation, and test CLI.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    dis_p = sub.add_parser("disasm", help="Disassemble 1982 Dig Dug Z80 ROMs into build/disasm_1982/")
    dis_p.add_argument("--rom", required=True, help="Path to digdug.zip, extracted dir, or digdug_b64.txt")

    assets_p = sub.add_parser(
        "assets",
        help="Compile all 65 asset families & 53 audio cues into Neo Geo C/S/V-ROM data and C headers",
    )
    assets_p.add_argument(
        "--pack",
        default=None,
        help="Optional path to Super-Dig-Dug-Complete-Asset-Pack.zip or Super-Dig-Dug-Art/ directory",
    )

    for name, help_text in [
        ("status", "Inspect repository layout and installed toolchain versions"),
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
    if cmd == "assets":
        return cmd_assets(args)
    if cmd == "asset-check":
        return cmd_asset_check(args)
    if cmd == "asset-preview":
        return cmd_asset_preview(args)
    if cmd == "budgets":
        return cmd_budgets(args)
    if cmd == "test":
        return cmd_test(args)
    if cmd == "art-viewer":
        return cmd_rom(viewer_only=True)
    if cmd == "rom":
        return cmd_rom(viewer_only=False)
    if cmd == "run":
        return cmd_run(debug_mode=False)
    if cmd == "debug":
        return cmd_run(debug_mode=True)
    if cmd == "package":
        return cmd_package(args)
    return 1


if __name__ == "__main__":
    sys.exit(main())
