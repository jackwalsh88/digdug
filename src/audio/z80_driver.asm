; =============================================================================
; Super Dig Dug — SNK Neo Geo MVS Z80 + YM2610 ADPCM-A Sound Driver (M1 ROM)
; =============================================================================
; Architecture:
;   - Z80 @ 4 MHz, ROM $0000..$7FFF, Work RAM $F800..$FFFF (SP = $FFFC)
;   - NMI ($0066) triggered when 68000 writes command to REG_SOUND ($320000):
;       * Reads port $00, acknowledges via port $0C, pushes cmd to ring buffer
;       * Handles mandatory Neo Geo BIOS commands $01 (slot switch) & $03 (reset)
;   - YM2610 ADPCM-A (Port B: addr $06, data $07; Status 1 read on $06):
;       * Channels 0..2: Sample-locked 3-stem music suites (keyed on together
;         via reg $00 = $07, seamlessly re-triggered on Status 1 bit 0 end flag,
;         and mixed dynamically via reg $08..$0A stereo/level bytes)
;       * Channels 3..5: Round-robin low-latency SFX & stinger playback
;   - Cue Page Table at $0400: 51 x 4-byte entries (start_lo, start_hi, end_lo, end_hi)
;     generated from `assets/generated/asset_manifest.json` by `tools/build_m1_z80.py`.
; =============================================================================

    ORG     $0000
ResetEntry:
    di
    ld      sp, $FFFC
    im      1
    jp      InitDriver

    ORG     $0038
IrqHandler:
    reti

    ORG     $0066
NmiHandler:
    push    af
    push    hl
    in      a, ($00)            ; Read 68000 sound command byte
    or      a
    jr      z, NmiDone
    cp      $01                 ; BIOS Slot Switch?
    jp      z, BiosSlotSwitch
    cp      $03                 ; BIOS Soft Reset?
    jp      z, BiosSoftReset
    ; Enqueue command in 16-byte ring buffer at $F800
    ld      hl, ($F810)         ; write_idx (low 4 bits)
    ld      h, $F8
    ld      (hl), a
    ld      a, l
    inc     a
    and     $0F
    ld      ($F810), a
    ld      a, $01
    out     ($0C), a            ; Acknowledge command to 68000
NmiDone:
    pop     hl
    pop     af
    retn
