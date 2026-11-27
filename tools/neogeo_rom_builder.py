"""Neo Geo MVS Cartridge ROM Builder, Software-List Hash Generator & Packaging Tool.

Supports building both:
  - `art-viewer` (`-DSDD_ART_VIEWER_ONLY`) -> standalone M0/B0 hardware & sprite diagnostics cart
  - `rom` -> full Phase 1 (1982 Dig Dug Replica) + embedded Art Viewer Neo Geo MVS cart

Toolchain auto-detection (works seamlessly on Linux/WSL2 and macOS Apple Silicon/Intel):
  - `m68k-neogeo-elf-gcc` (ngdevkit) OR `m68k-elf-gcc` (e.g. `brew install m68k-elf-gcc`)
  - Pure-Python Z80 + YM2610 M1 driver builder (`tools/build_m1_z80.py`)
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
import zipfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

C_AND_ASM_SOURCES = [
    "src/platform/neogeo/crt0_mvs.S",
    "src/platform/neogeo/neogeo_platform.c",
    "src/platform/neogeo/rt_mem.c",
    "src/audio/sdd_audio.c",
    "src/world/sdd_world.c",
    "src/score/sdd_score.c",
    "src/actors/sdd_player.c",
    "src/actors/sdd_rocks.c",
    "src/actors/sdd_enemies.c",
    "src/combat/sdd_pump.c",
    "src/render/sdd_render.c",
    "src/game/art_viewer.c",
    "src/game/sdd_game.c",
    "src/game/main.c",
    "assets/generated/sdd_assets.c",
]


def find_m68k_toolchain() -> tuple[str | None, str | None]:
    for prefix in ("m68k-neogeo-elf", "m68k-elf", "m68k-linux-gnu"):
        gcc = shutil.which(f"{prefix}-gcc")
        objcopy = shutil.which(f"{prefix}-objcopy")
        if gcc and objcopy:
            return gcc, objcopy
    return None, None


def _pad_pow2(data: bytes, min_bytes: int, fill: int = 0x00) -> bytes:
    target = max(min_bytes, 1)
    while target < len(data):
        target <<= 1
    if len(data) == target:
        return data
    return data + bytes([fill]) * (target - len(data))


def _swap_16bit_pairs(data: bytes) -> bytes:
    if len(data) % 2 != 0:
        data = data + b"\xFF"
    out = bytearray(len(data))
    out[0::2] = data[1::2]
    out[1::2] = data[0::2]
    return bytes(out)


def _crc_sha1(data: bytes) -> tuple[str, str]:
    crc = f"{zlib.crc32(data) & 0xFFFFFFFF:08x}"
    sha = hashlib.sha1(data).hexdigest()
    return crc, sha


def build_cartridge(viewer_only: bool = False) -> int:
    from assets.pack_pipeline import GENERATED_DIR, build_all_assets
    from build_m1_z80 import build_m1_rom

    if not (GENERATED_DIR / "c1.bin").is_file():
        print("[rom] Generated assets missing; compiling asset catalog first...")
        build_all_assets(None)

    build_dir = ROOT / "build"
    build_dir.mkdir(parents=True, exist_ok=True)

    # Always build Z80 M1 driver first (pure Python, works in every environment)
    m1_bytes = build_m1_rom(build_dir / "m1.bin")
    print(f"[rom] Assembled Z80 + YM2610 M1 sound ROM ({len(m1_bytes) // 1024} KB)")

    gcc, objcopy = find_m68k_toolchain()
    if not gcc or not objcopy:
        tag = "art-viewer" if viewer_only else "rom"
        print(
            f"[{tag}] Blocked in current environment: missing 68000 cross-compiler "
            "(install `ngdevkit` or `brew install m68k-elf-gcc` on macOS)."
        )
        return 2

    shortname = "sddview" if viewer_only else "superdigdug"
    elf_path = build_dir / f"{shortname}.elf"
    raw_bin_path = build_dir / f"{shortname}_be.bin"

    cmd = [
        gcc,
        "-m68000",
        "-Os",
        "-std=c99",
        "-Wall",
        "-Wextra",
        "-ffreestanding",
        "-fno-builtin",
        "-fno-tree-loop-distribute-patterns",
        "-fomit-frame-pointer",
        "-nostdlib",
        f"-T{ROOT / 'src/platform/neogeo/mvs_cart.ld'}",
        "-Wl,--build-id=none",
        f"-Wl,-Map={build_dir / (shortname + '.map')}",
    ]
    if viewer_only:
        cmd.append("-DSDD_ART_VIEWER_ONLY=1")
    cmd.extend(str(ROOT / src) for src in C_AND_ASM_SOURCES)
    cmd.extend(["-lgcc", "-o", str(elf_path)])

    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        print(proc.stderr or proc.stdout, file=sys.stderr)
        return proc.returncode

    proc2 = subprocess.run(
        [objcopy, "-O", "binary", str(elf_path), str(raw_bin_path)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc2.returncode != 0:
        print(proc2.stderr or proc2.stdout, file=sys.stderr)
        return proc2.returncode

    p1_be = _pad_pow2(raw_bin_path.read_bytes(), 512 * 1024, fill=0xFF)
    p1_swapped = _swap_16bit_pairs(p1_be)
    s1_padded = _pad_pow2((GENERATED_DIR / "s1.bin").read_bytes(), 128 * 1024, fill=0x00)
    c1_padded = _pad_pow2((GENERATED_DIR / "c1.bin").read_bytes(), 1024 * 1024, fill=0x00)
    c2_padded = _pad_pow2((GENERATED_DIR / "c2.bin").read_bytes(), 1024 * 1024, fill=0x00)
    v1_padded = _pad_pow2((GENERATED_DIR / "v1.bin").read_bytes(), 1024 * 1024, fill=0x80)

    chips = {
        "0482-p1.p1": p1_swapped,
        "0482-s1.s1": s1_padded,
        "0482-m1.m1": m1_bytes,
        "0482-v1.v1": v1_padded,
        "0482-c1.c1": c1_padded,
        "0482-c2.c2": c2_padded,
    }

    roms_dir = ROOT / "mame" / "roms"
    hash_dir = ROOT / "mame" / "hash"
    roms_dir.mkdir(parents=True, exist_ok=True)
    hash_dir.mkdir(parents=True, exist_ok=True)

    zip_path = roms_dir / f"{shortname}.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for fname, blob in chips.items():
            zf.writestr(fname, blob)

    # Emit isolated MAME software-list XML in mame/hash/neogeo.xml
    p1_crc, p1_sha = _crc_sha1(p1_swapped)
    s1_crc, s1_sha = _crc_sha1(s1_padded)
    m1_crc, m1_sha = _crc_sha1(m1_bytes)
    v1_crc, v1_sha = _crc_sha1(v1_padded)
    c1_crc, c1_sha = _crc_sha1(c1_padded)
    c2_crc, c2_sha = _crc_sha1(c2_padded)

    xml_text = f"""<?xml version="1.0"?>
<!DOCTYPE softwarelist SYSTEM "softwarelist.dtd">
<softwarelist name="neogeo" description="Super Dig Dug Custom MVS Development Software List">
  <software name="{shortname}">
    <description>Super Dig Dug ({'M0/B0 Art Viewer' if viewer_only else '1982 Replica + MVS Engine'})</description>
    <year>2026</year>
    <publisher>Homebrew MVS</publisher>
    <part name="cart" interface="neo_cart">
      <dataarea name="maincpu" width="16" endianness="big" size="0x{len(p1_swapped):x}">
        <rom loadflag="load16_word_swap" name="0482-p1.p1" offset="0x000000" size="0x{len(p1_swapped):x}" crc="{p1_crc}" sha1="{p1_sha}"/>
      </dataarea>
      <dataarea name="fixed" size="0x{len(s1_padded):x}">
        <rom offset="0x000000" size="0x{len(s1_padded):x}" name="0482-s1.s1" crc="{s1_crc}" sha1="{s1_sha}"/>
      </dataarea>
      <dataarea name="audiocpu" size="0x{len(m1_bytes):x}">
        <rom offset="0x000000" size="0x{len(m1_bytes):x}" name="0482-m1.m1" crc="{m1_crc}" sha1="{m1_sha}"/>
      </dataarea>
      <dataarea name="ymsnd:adpcma" size="0x{len(v1_padded):x}">
        <rom offset="0x000000" size="0x{len(v1_padded):x}" name="0482-v1.v1" crc="{v1_crc}" sha1="{v1_sha}"/>
      </dataarea>
      <dataarea name="sprites" size="0x{len(c1_padded) + len(c2_padded):x}">
        <rom loadflag="load16_byte" name="0482-c1.c1" offset="0x000000" size="0x{len(c1_padded):x}" crc="{c1_crc}" sha1="{c1_sha}"/>
        <rom loadflag="load16_byte" name="0482-c2.c2" offset="0x000001" size="0x{len(c2_padded):x}" crc="{c2_crc}" sha1="{c2_sha}"/>
      </dataarea>
    </part>
  </software>
</softwarelist>
"""
    (hash_dir / "neogeo.xml").write_text(xml_text)
    print(f"[rom] Built Neo Geo MVS cartridge -> {zip_path.relative_to(ROOT)} + mame/hash/neogeo.xml")
    return 0
