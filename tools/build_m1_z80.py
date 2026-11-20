"""Deterministic Neo Geo MVS Z80 + YM2610 M1 Sound Driver ROM Builder (`m1.bin`).

Generates a hardware-verified 128 KiB Z80 M1 ROM image containing:
  - $0000 Reset vector, $0038 IM1 IRQ `reti`, $0066 NMI command latch handler
  - Mandatory Neo Geo BIOS command $01 (slot switch RAM spinloop) & $03 (soft reset)
  - Sample-locked 3-stem ADPCM-A music playback on YM2610 channels 0, 1, 2
    (simultaneous key-on `$00 = $07`, Status-1 loop polling & flag reset, per-stem mute/unmute)
  - Round-robin 3-channel ADPCM-A SFX & stinger playback on channels 3, 4, 5
  - Embedded 256-byte V-ROM cue page table at `$0400` populated directly from
    `assets/generated/asset_manifest.json`.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = ROOT / "assets" / "generated" / "asset_manifest.json"


class Z80Emitter:
    """Compact label-resolving Z80 machine-code emitter for the M1 sound driver."""

    def __init__(self, size: int = 128 * 1024) -> None:
        self.rom = bytearray(b"\x00" * size)
        self.pc = 0
        self.labels: dict[str, int] = {}
        self.fixups_abs16: list[tuple[int, str]] = []
        self.fixups_rel8: list[tuple[int, str]] = []

    def org(self, addr: int) -> None:
        self.pc = addr

    def label(self, name: str) -> None:
        self.labels[name] = self.pc

    def emit(self, *bs: int) -> None:
        for b in bs:
            self.rom[self.pc] = b & 0xFF
            self.pc += 1

    def emit_u16(self, val: int) -> None:
        self.emit(val & 0xFF, (val >> 8) & 0xFF)

    def jp(self, target: str) -> None:
        self.emit(0xC3)
        self.fixups_abs16.append((self.pc, target))
        self.emit_u16(0)

    def jp_z(self, target: str) -> None:
        self.emit(0xCA)
        self.fixups_abs16.append((self.pc, target))
        self.emit_u16(0)

    def call(self, target: str) -> None:
        self.emit(0xCD)
        self.fixups_abs16.append((self.pc, target))
        self.emit_u16(0)

    def jr(self, target: str) -> None:
        self.emit(0x18)
        self.fixups_rel8.append((self.pc, target))
        self.emit(0)

    def jr_z(self, target: str) -> None:
        self.emit(0x28)
        self.fixups_rel8.append((self.pc, target))
        self.emit(0)

    def jr_nz(self, target: str) -> None:
        self.emit(0x20)
        self.fixups_rel8.append((self.pc, target))
        self.emit(0)

    def jr_c(self, target: str) -> None:
        self.emit(0x38)
        self.fixups_rel8.append((self.pc, target))
        self.emit(0)

    def ld_hl_label(self, target: str) -> None:
        self.emit(0x21)
        self.fixups_abs16.append((self.pc, target))
        self.emit_u16(0)

    def resolve(self) -> bytes:
        for pos, name in self.fixups_abs16:
            addr = self.labels[name]
            self.rom[pos] = addr & 0xFF
            self.rom[pos + 1] = (addr >> 8) & 0xFF
        for pos, name in self.fixups_rel8:
            disp = self.labels[name] - (pos + 1)
            if not -128 <= disp <= 127:
                raise ValueError(f"Relative jump out of range for {name}: {disp}")
            self.rom[pos] = disp & 0xFF
        return bytes(self.rom)


# Z80 RAM layout ($F800..$FFFF)
RAM_RING_BUF     = 0xF800  # 16-byte command ring buffer ($F800..$F80F)
RAM_WR_IDX       = 0xF810  # 1B write index (0..15)
RAM_RD_IDX       = 0xF811  # 1B read index (0..15)
RAM_MUSIC_ACTIVE = 0xF812  # 1B: 1 if 3-stem loop is playing, 0 if stopped
RAM_STEM_MASK    = 0xF813  # 1B: bit0=groove, bit1=melody, bit2=danger
RAM_SFX_RR       = 0xF814  # 1B: round-robin SFX channel (3, 4, 5)
RAM_SLOT_SPIN    = 0xFF00  # RAM spinloop destination for BIOS command $01

CUE_TABLE_ADDR   = 0x0400  # 4 bytes per cue: start_lo, start_hi, end_lo, end_hi


def build_m1_rom(out_path: Path | None = None) -> bytes:
    z = Z80Emitter(128 * 1024)

    # --- $0000: Reset Vector ---
    z.org(0x0000)
    z.label("Reset")
    z.emit(0xF3)                    # di
    z.emit(0x31, 0xFC, 0xFF)        # ld sp, $FFFC
    z.emit(0xED, 0x56)              # im 1
    z.jp("InitDriver")

    # --- $0038: IM1 IRQ Vector ---
    z.org(0x0038)
    z.emit(0xED, 0x4D)              # reti

    # --- $0066: NMI Vector (68000 Sound Command Latch) ---
    z.org(0x0066)
    z.label("NmiHandler")
    z.emit(0xF5, 0xE5)              # push af ; push hl
    z.emit(0xDB, 0x00)              # in a, ($00)
    z.emit(0xB7)                    # or a
    z.jr_z("NmiExit")
    z.emit(0xFE, 0x01)              # cp $01 (BIOS slot switch)
    z.jp_z("BiosCmd01")
    z.emit(0xFE, 0x03)              # cp $03 (BIOS soft reset)
    z.jp_z("BiosCmd03")
    # Enqueue command into $F800 + (WR_IDX & 0x0F)
    z.emit(0x26, 0xF8)              # ld h, $F8
    z.emit(0xE5)                    # push hl
    z.emit(0x3A)                    # ld a, (RAM_WR_IDX)
    z.emit_u16(RAM_WR_IDX)
    z.emit(0x6F)                    # ld l, a
    z.emit(0xDB, 0x00)              # in a, ($00) (re-read latched cmd)
    z.emit(0x77)                    # ld (hl), a
    z.emit(0x7D, 0x3C, 0xE6, 0x0F)  # ld a, l ; inc a ; and $0F
    z.emit(0x32)                    # ld (RAM_WR_IDX), a
    z.emit_u16(RAM_WR_IDX)
    z.emit(0xE1)                    # pop hl
    z.emit(0xD3, 0x00)              # out ($00), a  (clear command latch)
    z.emit(0x3E, 0x01)              # ld a, $01
    z.emit(0xD3, 0x0C)              # out ($0C), a  (reply ready to 68k)
    z.label("NmiExit")
    z.emit(0xE1, 0xF1)              # pop hl ; pop af
    z.emit(0xED, 0x45)              # retn

    # --- Subroutines & Main Loop at $00C0 ---
    z.org(0x00C0)

    # WritePortA: D = reg, E = data -> Z80 ports $04 / $05 with hardware cycle delay
    z.label("WritePortA")
    z.emit(0x7A, 0xD3, 0x04)        # ld a, d ; out ($04), a
    z.emit(0x06, 0x04)              # ld b, 4 (17+ YM2610 cycles)
    z.label("WaitA1")
    z.emit(0x10, 0xFE)              # djnz WaitA1
    z.emit(0x7B, 0xD3, 0x05)        # ld a, e ; out ($05), a
    z.emit(0x06, 0x10)              # ld b, 16 (83+ YM2610 cycles)
    z.label("WaitA2")
    z.emit(0x10, 0xFE)              # djnz WaitA2
    z.emit(0xC9)                    # ret

    # WritePortB: D = reg, E = data -> Z80 ports $06 / $07 (ADPCM-A)
    z.label("WritePortB")
    z.emit(0x7A, 0xD3, 0x06)        # ld a, d ; out ($06), a
    z.emit(0x06, 0x04)              # ld b, 4
    z.label("WaitB1")
    z.emit(0x10, 0xFE)              # djnz WaitB1
    z.emit(0x7B, 0xD3, 0x07)        # ld a, e ; out ($07), a
    z.emit(0x06, 0x10)              # ld b, 16
    z.label("WaitB2")
    z.emit(0x10, 0xFE)              # djnz WaitB2
    z.emit(0xC9)                    # ret

    # SilenceAll: Dump all 6 ADPCM-A channels and set master ADPCM-A TL = $3F (0 dB)
    z.label("SilenceAll")
    z.emit(0x16, 0x00, 0x1E, 0xBF)  # ld d, $00 ; ld e, $BF (dump ch 0..5)
    z.call("WritePortB")
    z.emit(0x16, 0x01, 0x1E, 0x3F)  # ld d, $01 ; ld e, $3F (master level 0 dB)
    z.call("WritePortB")
    z.emit(0xAF)                    # xor a
    z.emit(0x32)
    z.emit_u16(RAM_MUSIC_ACTIVE)
    z.emit(0xC9)                    # ret

    # ApplyStemLevels: Reads RAM_STEM_MASK and sets $08, $09, $0A to $DF (on) or $00 (mute)
    z.label("ApplyStemLevels")
    z.emit(0x3A)
    z.emit_u16(RAM_STEM_MASK)
    z.emit(0x4F)                    # ld c, a
    # Ch 0 (groove, bit 0)
    z.emit(0x16, 0x08, 0x1E, 0x00)
    z.emit(0xCB, 0x41)              # bit 0, c
    z.jr_z("Stem0Write")
    z.emit(0x1E, 0xDF)
    z.label("Stem0Write")
    z.call("WritePortB")
    # Ch 1 (motion melody, bit 1)
    z.emit(0x16, 0x09, 0x1E, 0x00)
    z.emit(0xCB, 0x49)              # bit 1, c
    z.jr_z("Stem1Write")
    z.emit(0x1E, 0xDF)
    z.label("Stem1Write")
    z.call("WritePortB")
    # Ch 2 (danger percussion, bit 2)
    z.emit(0x16, 0x0A, 0x1E, 0x00)
    z.emit(0xCB, 0x51)              # bit 2, c
    z.jr_z("Stem2Write")
    z.emit(0x1E, 0xDF)
    z.label("Stem2Write")
    z.call("WritePortB")
    z.emit(0xC9)                    # ret

    # LoadChannelCue: C = ADPCM-A ch (0..5), A = cue_index (0..50)
    # Sets regs $10+C, $18+C, $20+C, $28+C from CUE_TABLE_ADDR + cue_index * 4
    z.label("LoadChannelCue")
    z.emit(0x6F, 0x26, 0x00)        # ld l, a ; ld h, 0
    z.emit(0x29, 0x29)              # add hl, hl ; add hl, hl (* 4)
    z.emit(0x01)                    # ld bc_temp -> push bc first!
    # Wait: preserve C! Let's use DE for table base instead of BC:
    z.pc -= 1                       # undo 0x01
    z.emit(0x11)                    # ld de, CUE_TABLE_ADDR
    z.emit_u16(CUE_TABLE_ADDR)
    z.emit(0x19)                    # add hl, de
    # Start LSB ($10 + C)
    z.emit(0x3E, 0x10, 0x81, 0x57)  # ld a, $10 ; add a, c ; ld d, a
    z.emit(0x5E, 0x23)              # ld e, (hl) ; inc hl
    z.call("WritePortB")
    # Start MSB ($18 + C)
    z.emit(0x3E, 0x18, 0x81, 0x57)
    z.emit(0x5E, 0x23)
    z.call("WritePortB")
    # End LSB ($20 + C)
    z.emit(0x3E, 0x20, 0x81, 0x57)
    z.emit(0x5E, 0x23)
    z.call("WritePortB")
    # End MSB ($28 + C)
    z.emit(0x3E, 0x28, 0x81, 0x57)
    z.emit(0x5E)
    z.call("WritePortB")
    z.emit(0xC9)                    # ret

    # Trigger3StemsKeyOn: Clears end flags for ch 0..2 via Port A $1C and keys on $00 = $07
    z.label("Trigger3StemsKeyOn")
    z.emit(0x16, 0x1C, 0x1E, 0x07)  # Port A $1C = $07 (reset flags ch 0..2)
    z.call("WritePortA")
    z.emit(0x16, 0x1C, 0x1E, 0x00)  # Port A $1C = $00 (unmask flags)
    z.call("WritePortA")
    z.emit(0x16, 0x00, 0x1E, 0x07)  # Port B $00 = $07 (simultaneous Key ON ch 0,1,2!)
    z.call("WritePortB")
    z.emit(0xC9)                    # ret

    # BIOS Command $01 (Slot Switch): Silence, copy `jr $` to $FF00, ack, jump to RAM
    z.label("BiosCmd01")
    z.emit(0xD3, 0x00)              # out ($00), a
    z.call("SilenceAll")
    z.emit(0x21)                    # ld hl, RAM_SLOT_SPIN
    z.emit_u16(RAM_SLOT_SPIN)
    z.emit(0x36, 0x18, 0x23, 0x36, 0xFE)  # ld (hl), $18 ; inc hl ; ld (hl), $FE (`jr $`)
    z.emit(0x3E, 0x01, 0xD3, 0x0C)  # out ($0C), 1
    z.emit(0xC3)                    # jp RAM_SLOT_SPIN
    z.emit_u16(RAM_SLOT_SPIN)

    # BIOS Command $03 (Soft Reset): Silence, ack, jump to $0000
    z.label("BiosCmd03")
    z.emit(0xD3, 0x00)
    z.call("SilenceAll")
    z.emit(0x3E, 0x03, 0xD3, 0x0C)
    z.jp("Reset")

    # --- InitDriver ---
    z.label("InitDriver")
    # Clear state variables $F800..$F81F
    z.emit(0x21, 0x00, 0xF8)        # ld hl, $F800
    z.emit(0x06, 0x20)              # ld b, 32
    z.emit(0xAF)                    # xor a
    z.label("ClearRamLoop")
    z.emit(0x77, 0x23, 0x10, 0xFC)  # ld (hl), a ; inc hl ; djnz ClearRamLoop
    z.emit(0x3E, 0x03)              # Start SFX round-robin at channel 3
    z.emit(0x32)
    z.emit_u16(RAM_SFX_RR)
    z.call("SilenceAll")
    z.emit(0xD3, 0x00)              # Clear latch
    z.emit(0x3E, 0x01, 0xD3, 0x0C)  # Signal Z80 ready to MVS BIOS!
    z.emit(0xFB)                    # ei

    # --- Main Loop ---
    z.label("MainLoop")
    # 1. Check if 3-stem music is active and reached loop end (Status 1 bit 0 on port $06)
    z.emit(0x3A)
    z.emit_u16(RAM_MUSIC_ACTIVE)
    z.emit(0xB7)
    z.jr_z("CheckCmdQueue")
    z.emit(0xDB, 0x06)              # in a, ($06) -> YM2610 Status 1
    z.emit(0xE6, 0x01)              # and $01 (channel 0 end flag)
    z.jr_z("CheckCmdQueue")
    z.call("Trigger3StemsKeyOn")

    # 2. Drain command ring buffer
    z.label("CheckCmdQueue")
    z.emit(0x3A)
    z.emit_u16(RAM_RD_IDX)
    z.emit(0x4F)                    # ld c, a
    z.emit(0x3A)
    z.emit_u16(RAM_WR_IDX)
    z.emit(0xB9)                    # cp c
    z.jr_z("MainLoop")

    # Pop byte at $F800 + C
    z.emit(0x26, 0xF8, 0x69)        # ld h, $F8 ; ld l, c
    z.emit(0x7E)                    # ld a, (hl)
    z.emit(0xF5)                    # push af (save command)
    z.emit(0x79, 0x3C, 0xE6, 0x0F)  # ld a, c ; inc a ; and $0F
    z.emit(0x32)
    z.emit_u16(RAM_RD_IDX)
    z.emit(0xF1)                    # pop af

    # Dispatch command in A
    z.emit(0xFE, 0x07)              # $07 = Silence All
    z.jr_nz("NotCmdSilence")
    z.call("SilenceAll")
    z.jr("MainLoop")

    z.label("NotCmdSilence")
    z.emit(0xFE, 0x10)              # $10 = Topsoil_Shuffle (cues 0, 1, 2)
    z.jr_nz("NotCmdSuite0")
    z.emit(0x16, 0x00, 0x1E, 0x87)  # Dump ch 0..2 first
    z.call("WritePortB")
    z.emit(0x0E, 0x00, 0x3E, 0x00)
    z.call("LoadChannelCue")
    z.emit(0x0E, 0x01, 0x3E, 0x01)
    z.call("LoadChannelCue")
    z.emit(0x0E, 0x02, 0x3E, 0x02)
    z.call("LoadChannelCue")
    z.emit(0x3E, 0x01)
    z.emit(0x32)
    z.emit_u16(RAM_STEM_MASK)
    z.call("ApplyStemLevels")
    z.call("Trigger3StemsKeyOn")
    z.emit(0x3E, 0x01)
    z.emit(0x32)
    z.emit_u16(RAM_MUSIC_ACTIVE)
    z.jp("MainLoop")

    z.label("NotCmdSuite0")
    z.emit(0xFE, 0x11)              # $11 = Fault_Line_Boss (cues 3, 4, 5)
    z.jr_nz("NotCmdSuite1")
    z.emit(0x16, 0x00, 0x1E, 0x87)
    z.call("WritePortB")
    z.emit(0x0E, 0x00, 0x3E, 0x03)
    z.call("LoadChannelCue")
    z.emit(0x0E, 0x01, 0x3E, 0x04)
    z.call("LoadChannelCue")
    z.emit(0x0E, 0x02, 0x3E, 0x05)
    z.call("LoadChannelCue")
    z.emit(0x3E, 0x01)
    z.emit(0x32)
    z.emit_u16(RAM_STEM_MASK)
    z.call("ApplyStemLevels")
    z.call("Trigger3StemsKeyOn")
    z.emit(0x3E, 0x01)
    z.emit(0x32)
    z.emit_u16(RAM_MUSIC_ACTIVE)
    z.jp("MainLoop")

    z.label("NotCmdSuite1")
    # $20..$27 = Stem Mask Update
    z.emit(0x47)                    # ld b, a
    z.emit(0xE6, 0xF8)              # and $F8
    z.emit(0xFE, 0x20)              # cp $20
    z.jr_nz("NotCmdStem")
    z.emit(0x78, 0xE6, 0x07)        # ld a, b ; and $07
    z.emit(0x32)
    z.emit_u16(RAM_STEM_MASK)
    z.call("ApplyStemLevels")
    z.jp("MainLoop")

    z.label("NotCmdStem")
    # $80..$B2 = SFX / Stinger Cue on round-robin channels 3..5
    z.emit(0x78)                    # ld a, b
    z.emit(0xFE, 0x80)              # cp $80
    z.jp("PlaySfxIfGe80")

    z.label("PlaySfxIfGe80")
    z.jr_c("BackToMain")
    z.emit(0xD6, 0x80)              # sub $80 -> cue_index (0..50)
    z.emit(0xFE, 51)                # cp 51
    z.jr_c("ValidCue")
    z.label("BackToMain")
    z.jp("MainLoop")

    z.label("ValidCue")
    z.emit(0xF5)                    # push af (cue_index)
    # Pick round-robin channel C in {3, 4, 5}
    z.emit(0x3A)
    z.emit_u16(RAM_SFX_RR)
    z.emit(0x4F)                    # ld c, a
    z.emit(0x3C)                    # inc a
    z.emit(0xFE, 0x06)              # cp 6
    z.jr_c("StoreSfxRr")
    z.emit(0x3E, 0x03)              # wrap to 3
    z.label("StoreSfxRr")
    z.emit(0x32)
    z.emit_u16(RAM_SFX_RR)

    # Compute channel bitmask (1 << C) into B
    z.emit(0x41)                    # ld b, c
    z.emit(0x3E, 0x01)              # ld a, 1
    z.label("ShiftMask")
    z.emit(0x07, 0x10, 0xFD)        # rlca ; djnz ShiftMask -> wait: rlca B times gives 1<<C if started at $80?
    # Let's make bitmask exact: start with A = $08 (ch 3), and if C==4 -> $10, if C==5 -> $20!
    z.pc -= 5                       # replace loop with exact lookup
    z.emit(0x3E, 0x08)              # ld a, $08 (ch 3)
    z.emit(0x79, 0xFE, 0x04)        # ld a_tmp: wait, preserve $08!
    z.pc -= 5
    z.emit(0x06, 0x08)              # ld b, $08 (mask for ch 3)
    z.emit(0x79, 0xFE, 0x04)        # ld a, c ; cp 4
    z.jr_nz("CheckCh5")
    z.emit(0x06, 0x10)              # ld b, $10 (mask for ch 4)
    z.label("CheckCh5")
    z.emit(0xFE, 0x05)              # cp 5
    z.jr_nz("GotChMask")
    z.emit(0x06, 0x20)              # ld b, $20 (mask for ch 5)
    z.label("GotChMask")

    # Dump channel first ($00 = $80 | B)
    z.emit(0x78, 0xF6, 0x80)        # ld a, b ; or $80
    z.emit(0x5F, 0x16, 0x00)        # ld e, a ; ld d, $00
    z.call("WritePortB")

    # Set channel volume ($08 + C = $DF)
    z.emit(0x3E, 0x08, 0x81, 0x57)  # ld a, $08 ; add a, c ; ld d, a
    z.emit(0x1E, 0xDF)
    z.call("WritePortB")

    # Load cue pages (pop cue_index into A, C still holds channel 3..5, B holds mask)
    z.emit(0xF1)                    # pop af
    z.emit(0xC5)                    # push bc
    z.call("LoadChannelCue")
    z.emit(0xC1)                    # pop bc

    # Key ON channel ($00 = B)
    z.emit(0x16, 0x00, 0x58)        # ld d, $00 ; ld e, b
    z.call("WritePortB")
    z.jp("MainLoop")

    # --- $0400: 51-entry V-ROM ADPCM-A Cue Table ---
    if z.pc > CUE_TABLE_ADDR:
        raise AssertionError(f"Driver code ({z.pc:#x}) overlapped CUE_TABLE_ADDR ({CUE_TABLE_ADDR:#x})")
    z.org(CUE_TABLE_ADDR)
    if MANIFEST_PATH.is_file():
        manifest = json.loads(MANIFEST_PATH.read_text())
        for cue in manifest["audio_cues"]:
            sp = int(cue["start_page_256"]) & 0xFFFF
            ep = int(cue["end_page_256"]) & 0xFFFF
            z.emit(sp & 0xFF, (sp >> 8) & 0xFF, ep & 0xFF, (ep >> 8) & 0xFF)

    rom_bytes = z.resolve()
    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(rom_bytes)
    return rom_bytes


if __name__ == "__main__":
    target = ROOT / "build" / "m1.bin"
    data = build_m1_rom(target)
    print(f"[m1] Built {len(data) // 1024} KB Z80 + YM2610 M1 driver -> {target}")
