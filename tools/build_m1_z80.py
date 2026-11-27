"""Neo Geo Z80 + YM2610 sound driver ROM builder (`m1.bin`).

The driver lives in `src/audio/z80_driver.s` (sdasz80 syntax). When ngdevkit's
`z80-neogeo-ihx-sdasz80` / `sdldz80` are on PATH the source is assembled and
`src/audio/z80_driver.bin` (the code below the cue table) is refreshed; without
them that committed blob is used as-is. The cue count and the cue table
(start/end ADPCM-A pages per cue) are then patched in from
`assets/generated/asset_manifest.json`.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = ROOT / "assets" / "generated" / "asset_manifest.json"
DRIVER_SRC = ROOT / "src" / "audio" / "z80_driver.s"
DRIVER_BLOB = ROOT / "src" / "audio" / "z80_driver.bin"

M1_SIZE = 128 * 1024
CUE_COUNT_ADDR = 0x03FF
CUE_TABLE_ADDR = 0x0400


def _parse_ihx(text: str) -> bytearray:
    image = bytearray(CUE_COUNT_ADDR)
    for line in text.splitlines():
        if not line.startswith(":"):
            continue
        raw = bytes.fromhex(line[1:])
        count, addr, rtype = raw[0], (raw[1] << 8) | raw[2], raw[3]
        if rtype != 0x00:
            continue
        if addr + count > CUE_COUNT_ADDR:
            raise AssertionError(f"driver code at {addr:#06x}+{count} overlaps the cue table")
        image[addr:addr + count] = raw[4:4 + count]
    return image


def assemble_driver() -> bytes | None:
    """Assemble the driver source; returns the code image or None without tools."""
    sdas = shutil.which("z80-neogeo-ihx-sdasz80") or shutil.which("sdasz80")
    sdld = shutil.which("z80-neogeo-ihx-sdldz80") or shutil.which("sdldz80")
    if not sdas or not sdld:
        return None
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        src = tmp_path / "z80_driver.s"
        shutil.copyfile(DRIVER_SRC, src)
        subprocess.run([sdas, "-g", "-o", "z80_driver.rel", "z80_driver.s"], cwd=tmp, check=True)
        subprocess.run([sdld, "-i", "z80_driver.ihx", "z80_driver.rel"], cwd=tmp, check=True,
                       capture_output=True)
        return bytes(_parse_ihx((tmp_path / "z80_driver.ihx").read_text()))


def driver_code() -> bytes:
    code = assemble_driver()
    if code is None:
        if not DRIVER_BLOB.is_file():
            raise FileNotFoundError(
                "No Z80 assembler found and src/audio/z80_driver.bin is missing; "
                "install ngdevkit (z80-neogeo-ihx-sdasz80)."
            )
        return DRIVER_BLOB.read_bytes()
    if not DRIVER_BLOB.is_file() or DRIVER_BLOB.read_bytes() != code:
        DRIVER_BLOB.write_bytes(code)
    return code


def build_m1_rom(out_path: Path | None = None) -> bytes:
    rom = bytearray(M1_SIZE)
    code = driver_code()
    rom[:len(code)] = code

    cues = []
    if MANIFEST_PATH.is_file():
        cues = json.loads(MANIFEST_PATH.read_text())["audio_cues"]
    if len(cues) > 255:
        raise AssertionError("cue table supports at most 255 entries")
    rom[CUE_COUNT_ADDR] = len(cues)
    pos = CUE_TABLE_ADDR
    for cue in cues:
        start = int(cue["start_page_256"]) & 0xFFFF
        end = int(cue["end_page_256"]) & 0xFFFF
        rom[pos:pos + 4] = bytes((start & 0xFF, start >> 8, end & 0xFF, end >> 8))
        pos += 4

    rom_bytes = bytes(rom)
    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(rom_bytes)
    return rom_bytes


if __name__ == "__main__":
    data = build_m1_rom(ROOT / "build" / "m1.bin")
    print(f"[m1] wrote build/m1.bin ({len(data) // 1024} KB)")
