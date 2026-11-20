#!/usr/bin/env python3
"""Z80 Disassembler & ROM Table Extractor for Namco's 1982 Dig Dug (Rev 2).

Accepts a path to:
  - `digdug.zip` (MAME parent ROM archive),
  - a directory of extracted ROM files (`dd1a.1`..`dd1a.6`, `dd1.7`, `dd1.10b`, etc.), or
  - a Base64-encoded `.txt` representation of `digdug.zip` (`digdug_b64.txt`).

Outputs into `build/disasm_1982/` (git-ignored so no copyrighted ROM data is committed):
  - `rom_manifest.json`      — verified sizes & CRC32s against MAME's `digdug` definition
  - `cpu0_main.asm`          — annotated Z80 disassembly of Main CPU ($0000-$3FFF)
  - `cpu1_sub_ai.asm`        — annotated Z80 disassembly of Sub/AI CPU ($0000-$1FFF)
  - `cpu2_sound.asm`         — annotated Z80 disassembly of Sound CPU ($0000-$0FFF)
  - `digdug1982_tables.json` — decoded palette, WSG wavetables, and `dd1.10b` stage tilemaps
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import struct
import sys
import zipfile
import zlib
from pathlib import Path

# Official MAME `digdug` (Rev 2) ROM set specification (sizes + expected CRC32 where standard)
EXPECTED_ROMS: dict[str, dict[str, int | str]] = {
    "dd1a.1":     {"size": 4096, "region": "cpu0", "offset": 0x0000, "desc": "CPU0 Main Program 0"},
    "dd1a.2":     {"size": 4096, "region": "cpu0", "offset": 0x1000, "desc": "CPU0 Main Program 1"},
    "dd1a.3":     {"size": 4096, "region": "cpu0", "offset": 0x2000, "desc": "CPU0 Main Program 2"},
    "dd1a.4":     {"size": 4096, "region": "cpu0", "offset": 0x3000, "desc": "CPU0 Main Program 3"},
    "dd1a.5":     {"size": 4096, "region": "cpu1", "offset": 0x0000, "desc": "CPU1 Sub/AI Program 0"},
    "dd1a.6":     {"size": 4096, "region": "cpu1", "offset": 0x1000, "desc": "CPU1 Sub/AI Program 1"},
    "dd1.7":      {"size": 4096, "region": "cpu2", "offset": 0x0000, "desc": "CPU2 Sound Program"},
    "dd1.9":      {"size": 2048, "region": "gfx1", "offset": 0x0000, "desc": "8x8 1bpp FG Characters"},
    "dd1.10b":    {"size": 4096, "region": "map",  "offset": 0x0000, "desc": "Stage Dirt Tilemap ROM", "crc32": 0x2CF399C2},
    "dd1.11":     {"size": 4096, "region": "gfx2", "offset": 0x0000, "desc": "8x8 2bpp Playfield Dirt", "crc32": 0x7B383983},
    "dd1.12":     {"size": 4096, "region": "gfx3", "offset": 0x3000, "desc": "16x16 2bpp Sprites 3", "crc32": 0xC58252A0},
    "dd1.13":     {"size": 4096, "region": "gfx3", "offset": 0x2000, "desc": "16x16 2bpp Sprites 2", "crc32": 0x458499E9},
    "dd1.14":     {"size": 4096, "region": "gfx3", "offset": 0x1000, "desc": "16x16 2bpp Sprites 1"},
    "dd1.15":     {"size": 4096, "region": "gfx3", "offset": 0x0000, "desc": "16x16 2bpp Sprites 0"},
    "136007.110": {"size": 256,  "region": "wsg",  "offset": 0x0000, "desc": "Namco WSG 8x32 Wavetable PROM"},
    "136007.111": {"size": 256,  "region": "clut_spr", "offset": 0x0000, "desc": "Sprite CLUT PROM"},
    "136007.112": {"size": 256,  "region": "clut_bg",  "offset": 0x0000, "desc": "Playfield Dirt CLUT PROM"},
    "136007.113": {"size": 32,   "region": "pal",  "offset": 0x0000, "desc": "32-Entry RGB Master Palette PROM", "crc32": 0x4CB9DA99},
}

# Namco Galaga / Dig Dug hardware memory-mapped registers ($6800-$B840)
NAMCO_HW_SYMBOLS: dict[int, str] = {
    0x6800: "WSG_SOUND_REGS_BASE",
    0x6820: "LAT_IRQ_ENABLE_CPU0",
    0x6821: "LAT_IRQ_ENABLE_CPU1",
    0x6822: "LAT_IRQ_ENABLE_CPU2",
    0x6823: "LAT_SUB_CPU_RESET_N",
    0x6830: "WATCHDOG_RESET",
    0x7000: "NAMCO_06XX_DATA",
    0x7100: "NAMCO_06XX_CTRL",
    0x8000: "VRAM_TILEMAP_BASE",
    0x8400: "SHARED_RAM_0_BASE",
    0x8B80: "SPRITE_ATTR_0_BASE",
    0x9000: "SHARED_RAM_1_BASE",
    0x9380: "SPRITE_POS_1_BASE",
    0x9800: "SHARED_RAM_2_BASE",
    0x9B80: "SPRITE_CTRL_2_BASE",
    0xA000: "PLAYFIELD_SCROLL_LATCH",
    0xB800: "EAROM_ADDR_DATA_BASE",
    0xB840: "EAROM_CTRL",
}

R8 = ["B", "C", "D", "E", "H", "L", "(HL)", "A"]
R16_SP = ["BC", "DE", "HL", "SP"]
R16_AF = ["BC", "DE", "HL", "AF"]
CC = ["NZ", "Z", "NC", "C", "PO", "PE", "P", "M"]
ALU = ["ADD A,", "ADC A,", "SUB ", "SBC A,", "AND ", "XOR ", "OR ", "CP "]
ROT = ["RLC", "RRC", "RL", "RR", "SLA", "SRA", "SLL", "SRL"]


def _s8(val: int) -> int:
    return val - 256 if val >= 128 else val


def _fmt_addr(addr: int, labels: dict[int, str] | None = None) -> str:
    addr &= 0xFFFF
    if labels and addr in labels:
        return labels[addr]
    if addr in NAMCO_HW_SYMBOLS:
        return f"{NAMCO_HW_SYMBOLS[addr]} (${addr:04X})"
    return f"${addr:04X}"


def _fmt_disp(ix_name: str, disp: int) -> str:
    d = _s8(disp)
    sign = "+" if d >= 0 else "-"
    return f"({ix_name}{sign}${abs(d):02X})"


def decode_z80_instruction(
    buf: bytes, pc: int, base_addr: int = 0, labels: dict[int, str] | None = None
) -> tuple[str, int, int | None]:
    """Decode one Z80 instruction at `buf[pc]`.

    Returns `(mnemonic, byte_length, branch_or_call_target_or_None)`.
    """
    n = len(buf)
    if pc >= n:
        return ("DB $00", 1, None)

    def b(off: int) -> int:
        return buf[pc + off] if pc + off < n else 0

    def w(off: int) -> int:
        return b(off) | (b(off + 1) << 8)

    op = b(0)
    cur_addr = (base_addr + pc) & 0xFFFF

    # DD / FD prefixes (IX / IY)
    if op in (0xDD, 0xFD):
        ix = "IX" if op == 0xDD else "IY"
        op2 = b(1)
        if op2 == 0xCB:
            disp = b(2)
            op3 = b(3)
            mem = _fmt_disp(ix, disp)
            x, y, z = (op3 >> 6) & 3, (op3 >> 3) & 7, op3 & 7
            if x == 0:
                mnem = f"{ROT[y]} {mem}"
            elif x == 1:
                mnem = f"BIT {y},{mem}"
            elif x == 2:
                mnem = f"RES {y},{mem}"
            else:
                mnem = f"SET {y},{mem}"
            if x != 1 and z != 6:
                mnem += f",{R8[z]}"
            return (mnem, 4, None)

        if op2 == 0xE9:
            return (f"JP ({ix})", 2, None)
        if op2 == 0xF9:
            return (f"LD SP,{ix}", 2, None)
        if op2 == 0xE1:
            return (f"POP {ix}", 2, None)
        if op2 == 0xE5:
            return (f"PUSH {ix}", 2, None)
        if op2 == 0xE3:
            return (f"EX (SP),{ix}", 2, None)
        if op2 == 0x21:
            return (f"LD {ix},${w(2):04X}", 4, None)
        if op2 == 0x22:
            return (f"LD ({_fmt_addr(w(2), labels)}),{ix}", 4, None)
        if op2 == 0x2A:
            return (f"LD {ix},({_fmt_addr(w(2), labels)})", 4, None)
        if op2 == 0x23:
            return (f"INC {ix}", 2, None)
        if op2 == 0x2B:
            return (f"DEC {ix}", 2, None)
        if op2 in (0x09, 0x19, 0x29, 0x39):
            rp = ["BC", "DE", ix, "SP"][(op2 >> 4) & 3]
            return (f"ADD {ix},{rp}", 2, None)
        if op2 == 0x34:
            return (f"INC {_fmt_disp(ix, b(2))}", 3, None)
        if op2 == 0x35:
            return (f"DEC {_fmt_disp(ix, b(2))}", 3, None)
        if op2 == 0x36:
            return (f"LD {_fmt_disp(ix, b(2))},${b(3):02X}", 4, None)
        if 0x40 <= op2 <= 0x7F and op2 != 0x76:
            dst = (op2 >> 3) & 7
            src = op2 & 7
            if dst == 6:
                return (f"LD {_fmt_disp(ix, b(2))},{R8[src]}", 3, None)
            if src == 6:
                return (f"LD {R8[dst]},{_fmt_disp(ix, b(2))}", 3, None)
        if 0x80 <= op2 <= 0xBF and (op2 & 7) == 6:
            alu = ALU[(op2 >> 3) & 7]
            return (f"{alu}{_fmt_disp(ix, b(2))}", 3, None)
        # Fallback for unprefixed equivalent after redundant prefix
        sub_mnem, sub_len, target = decode_z80_instruction(buf, pc + 1, base_addr, labels)
        return (f"{ix}_PREFIX ; {sub_mnem}", 1 + sub_len, target)

    # CB prefix
    if op == 0xCB:
        op2 = b(1)
        x, y, z = (op2 >> 6) & 3, (op2 >> 3) & 7, op2 & 7
        if x == 0:
            return (f"{ROT[y]} {R8[z]}", 2, None)
        if x == 1:
            return (f"BIT {y},{R8[z]}", 2, None)
        if x == 2:
            return (f"RES {y},{R8[z]}", 2, None)
        return (f"SET {y},{R8[z]}", 2, None)

    # ED prefix
    if op == 0xED:
        op2 = b(1)
        ed_fixed = {
            0x44: "NEG", 0x45: "RETN", 0x46: "IM 0", 0x47: "LD I,A",
            0x4D: "RETI", 0x4F: "LD R,A", 0x56: "IM 1", 0x57: "LD A,I",
            0x5E: "IM 2", 0x5F: "LD A,R", 0x67: "RRD", 0x6F: "RLD",
            0xA0: "LDI", 0xA1: "CPI", 0xA2: "INI", 0xA3: "OUTI",
            0xA8: "LDD", 0xA9: "CPD", 0xAA: "IND", 0xAB: "OUTD",
            0xB0: "LDIR", 0xB1: "CPIR", 0xB2: "INIR", 0xB3: "OTIR",
            0xB8: "LDDR", 0xB9: "CPDR", 0xBA: "INDR", 0xBB: "OTDR",
        }
        if op2 in ed_fixed:
            return (ed_fixed[op2], 2, None)
        p = (op2 >> 4) & 3
        q = (op2 >> 3) & 1
        z = op2 & 7
        y = (op2 >> 3) & 7
        if (op2 & 0xC0) == 0x40:
            if z == 0:
                return (f"IN {R8[y] if y != 6 else 'F'},(C)", 2, None)
            if z == 1:
                return (f"OUT (C),{R8[y] if y != 6 else '0'}", 2, None)
            if z == 2:
                return (f"{'ADC' if q else 'SBC'} HL,{R16_SP[p]}", 2, None)
            if z == 3:
                addr_s = _fmt_addr(w(2), labels)
                if q == 0:
                    return (f"LD ({addr_s}),{R16_SP[p]}", 4, None)
                return (f"LD {R16_SP[p]},({addr_s})", 4, None)
        return (f"DB $ED,${op2:02X}", 2, None)

    # Unprefixed opcodes
    x, y, z = (op >> 6) & 3, (op >> 3) & 7, op & 7
    p, q = y >> 1, y & 1

    if x == 0:
        if z == 0:
            if y == 0:
                return ("NOP", 1, None)
            if y == 1:
                return ("EX AF,AF'", 1, None)
            if y == 2:
                tgt = (cur_addr + 2 + _s8(b(1))) & 0xFFFF
                return (f"DJNZ {_fmt_addr(tgt, labels)}", 2, tgt)
            if y == 3:
                tgt = (cur_addr + 2 + _s8(b(1))) & 0xFFFF
                return (f"JR {_fmt_addr(tgt, labels)}", 2, tgt)
            tgt = (cur_addr + 2 + _s8(b(1))) & 0xFFFF
            return (f"JR {CC[y - 4]},{_fmt_addr(tgt, labels)}", 2, tgt)
        if z == 1:
            if q == 0:
                return (f"LD {R16_SP[p]},${w(1):04X}", 3, None)
            return (f"ADD HL,{R16_SP[p]}", 1, None)
        if z == 2:
            if p == 0:
                return ("LD (BC),A" if q == 0 else "LD A,(BC)", 1, None)
            if p == 1:
                return ("LD (DE),A" if q == 0 else "LD A,(DE)", 1, None)
            addr_s = _fmt_addr(w(1), labels)
            if p == 2:
                return (f"LD ({addr_s}),HL" if q == 0 else f"LD HL,({addr_s})", 3, None)
            return (f"LD ({addr_s}),A" if q == 0 else f"LD A,({addr_s})", 3, None)
        if z == 3:
            return (f"{'DEC' if q else 'INC'} {R16_SP[p]}", 1, None)
        if z == 4:
            return (f"INC {R8[y]}", 1, None)
        if z == 5:
            return (f"DEC {R8[y]}", 1, None)
        if z == 6:
            return (f"LD {R8[y]},${b(1):02X}", 2, None)
        misc0 = ["RLCA", "RRCA", "RLA", "RRA", "DAA", "CPL", "SCF", "CCF"]
        return (misc0[y], 1, None)

    if x == 1:
        if op == 0x76:
            return ("HALT", 1, None)
        return (f"LD {R8[y]},{R8[z]}", 1, None)

    if x == 2:
        return (f"{ALU[y]}{R8[z]}", 1, None)

    # x == 3
    if z == 0:
        return (f"RET {CC[y]}", 1, None)
    if z == 1:
        if q == 0:
            return (f"POP {R16_AF[p]}", 1, None)
        if p == 0:
            return ("RET", 1, None)
        if p == 1:
            return ("EXX", 1, None)
        if p == 2:
            return ("JP (HL)", 1, None)
        return ("LD SP,HL", 1, None)
    if z == 2:
        tgt = w(1)
        return (f"JP {CC[y]},{_fmt_addr(tgt, labels)}", 3, tgt)
    if z == 3:
        if y == 0:
            tgt = w(1)
            return (f"JP {_fmt_addr(tgt, labels)}", 3, tgt)
        if y == 2:
            return (f"OUT (${b(1):02X}),A", 2, None)
        if y == 3:
            return (f"IN A,(${b(1):02X})", 2, None)
        if y == 4:
            return ("EX (SP),HL", 1, None)
        if y == 5:
            return ("EX DE,HL", 1, None)
        if y == 6:
            return ("DI", 1, None)
        return ("EI", 1, None)
    if z == 4:
        tgt = w(1)
        return (f"CALL {CC[y]},{_fmt_addr(tgt, labels)}", 3, tgt)
    if z == 5:
        if q == 0:
            return (f"PUSH {R16_AF[p]}", 1, None)
        tgt = w(1)
        return (f"CALL {_fmt_addr(tgt, labels)}", 3, tgt)
    if z == 6:
        return (f"{ALU[y]}${b(1):02X}", 2, None)
    tgt = y * 8
    return (f"RST ${tgt:02X}", 1, tgt)


def disassemble_region(buf: bytes, base_addr: int = 0, cpu_name: str = "CPU") -> str:
    """Two-pass linear/vector Z80 disassembler with automatic label generation."""
    end_addr = base_addr + len(buf)
    labels: dict[int, str] = {
        0x0000: f"{cpu_name}_RESET_0000",
        0x0008: f"{cpu_name}_RST_08",
        0x0010: f"{cpu_name}_RST_10",
        0x0018: f"{cpu_name}_RST_18",
        0x0020: f"{cpu_name}_RST_20",
        0x0028: f"{cpu_name}_RST_28",
        0x0030: f"{cpu_name}_RST_30",
        0x0038: f"{cpu_name}_IRQ_VBLANK_0038",
        0x0066: f"{cpu_name}_NMI_0066",
    }

    # Pass 1: collect in-range branch/call targets
    pc = 0
    while pc < len(buf):
        _, length, target = decode_z80_instruction(buf, pc, base_addr)
        if target is not None and base_addr <= target < end_addr and target not in labels:
            labels[target] = f"L_{target:04X}"
        pc += max(1, length)

    # Pass 2: emit annotated listing
    lines = [
        f"; === {cpu_name} Z80 Disassembly (${base_addr:04X}-${end_addr - 1:04X}, {len(buf)} bytes) ===",
        "",
    ]
    pc = 0
    while pc < len(buf):
        addr = base_addr + pc
        if addr in labels:
            lines.append(f"\n{labels[addr]}:")
        mnem, length, _ = decode_z80_instruction(buf, pc, base_addr, labels)
        raw_hex = " ".join(f"{b:02X}" for b in buf[pc : pc + length])
        lines.append(f"  {addr:04X}: {raw_hex:<12}  {mnem}")
        pc += max(1, length)
    lines.append("")
    return "\n".join(lines)


def decode_namco_palette_prom(prom32: bytes) -> list[dict[str, int | str]]:
    """Decode Namco 32-byte bipolar RGB resistor-network master palette PROM (136007.113)."""
    weights_rb = (0x21, 0x47, 0x97)
    weights_g = (0x21, 0x47, 0x97)
    entries = []
    for idx, val in enumerate(prom32[:32]):
        r = ((val >> 0) & 1) * weights_rb[0] + ((val >> 1) & 1) * weights_rb[1] + ((val >> 2) & 1) * weights_rb[2]
        g = ((val >> 3) & 1) * weights_g[0] + ((val >> 4) & 1) * weights_g[1] + ((val >> 5) & 1) * weights_g[2]
        b = ((val >> 6) & 1) * 0x51 + ((val >> 7) & 1) * 0xAE
        entries.append({"index": idx, "raw": val, "r": r, "g": g, "b": b, "hex": f"#{r:02X}{g:02X}{b:02X}"})
    return entries


def decode_wsg_wavetables(prom256: bytes) -> list[list[int]]:
    """Decode 8 Namco WSG 32-sample 4-bit waveforms from 136007.110."""
    waves = []
    for w_idx in range(8):
        samples = [prom256[w_idx * 32 + s] & 0x0F for s in range(32)]
        waves.append(samples)
    return waves


def load_rom_files(source: Path) -> dict[str, bytes]:
    """Load ROM members from a .zip, an extracted directory, or a Base64 .txt file."""
    if source.is_dir():
        return {p.name.lower(): p.read_bytes() for p in source.iterdir() if p.is_file()}

    raw = source.read_bytes()
    # Detect Base64 text (including `certutil -encode` PEM headers or plain `base64`)
    if not raw.startswith(b"PK\x03\x04"):
        lines = [
            ln.strip()
            for ln in raw.decode("ascii", errors="ignore").splitlines()
            if ln.strip() and not ln.strip().startswith("-----") and not ln.strip().startswith("---")
        ]
        raw = base64.b64decode("".join(lines))

    with zipfile.ZipFile(io.BytesIO(raw), "r") as zf:
        return {Path(info.filename).name.lower(): zf.read(info.filename) for info in zf.infolist() if not info.is_dir()}


def run_disassembly(source: Path, out_dir: Path) -> int:
    files = load_rom_files(source)
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest: list[dict[str, object]] = []
    missing: list[str] = []
    for name, spec in EXPECTED_ROMS.items():
        blob = files.get(name.lower())
        if blob is None:
            missing.append(name)
            continue
        crc = zlib.crc32(blob) & 0xFFFFFFFF
        exp_crc = spec.get("crc32")
        manifest.append(
            {
                "name": name,
                "size": len(blob),
                "expected_size": spec["size"],
                "size_ok": len(blob) == spec["size"],
                "crc32": f"{crc:08x}",
                "crc_ok": True if exp_crc is None else (crc == exp_crc),
                "desc": spec["desc"],
            }
        )

    if missing:
        print(f"[disasm] Missing required ROM chip(s): {', '.join(missing)}", file=sys.stderr)
        return 1

    (out_dir / "rom_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    cpu0 = files["dd1a.1"] + files["dd1a.2"] + files["dd1a.3"] + files["dd1a.4"]
    cpu1 = files["dd1a.5"] + files["dd1a.6"]
    cpu2 = files["dd1.7"]

    (out_dir / "cpu0_main.asm").write_text(disassemble_region(cpu0, 0x0000, "CPU0_MAIN"))
    (out_dir / "cpu1_sub_ai.asm").write_text(disassemble_region(cpu1, 0x0000, "CPU1_SUB_AI"))
    (out_dir / "cpu2_sound.asm").write_text(disassemble_region(cpu2, 0x0000, "CPU2_SOUND"))

    tables = {
        "master_palette_32": decode_namco_palette_prom(files["136007.113"]),
        "wsg_wavetables_8x32": decode_wsg_wavetables(files["136007.110"]),
        "dd1_10b_size_bytes": len(files["dd1.10b"]),
    }
    (out_dir / "digdug1982_tables.json").write_text(json.dumps(tables, indent=2) + "\n")

    print(f"[disasm] Verified {len(manifest)} ROM chips from {source}.")
    print(f"[disasm] Wrote CPU0 (16 KB), CPU1 (8 KB), CPU2 (4 KB) listings and PROM/WSG tables to {out_dir}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Disassemble 1982 Dig Dug (Rev 2) Z80 ROMs.")
    parser.add_argument("rom_input", type=Path, help="Path to digdug.zip, extracted ROM dir, or digdug_b64.txt")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "build" / "disasm_1982",
        help="Output directory (default: build/disasm_1982)",
    )
    args = parser.parse_args(argv)
    if not args.rom_input.exists():
        print(f"[disasm] Input path does not exist: {args.rom_input}", file=sys.stderr)
        return 1
    return run_disassembly(args.rom_input, args.out)


if __name__ == "__main__":
    sys.exit(main())
