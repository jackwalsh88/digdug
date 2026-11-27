;;; Super Dig Dug — Neo Geo Z80 + YM2610 sound driver (M1 ROM), sdasz80 syntax.
;;;
;;; Assembled by tools/build_m1_z80.py with ngdevkit's z80-neogeo-ihx-sdasz80.
;;; The assembled code (everything below CUE_COUNT_ADDR) is also committed as
;;; src/audio/z80_driver.bin so the ROM can be built without a Z80 assembler;
;;; the cue table at CUE_TABLE is patched in from the asset manifest.
;;;
;;; 68000 command bytes (REG_SOUND):
;;;   $01        BIOS: prepare for slot switch (wait in RAM)
;;;   $03        BIOS/game: reset and start the driver
;;;   $07        silence everything
;;;   $10, $11   start 3-stem music suite 0 / 1 on ADPCM-A channels 0..2
;;;   $20..$27   stem mask: bit0 groove, bit1 melody, bit2 danger percussion
;;;   $80+n      play cue n on ADPCM-A channels 3..5 (round robin)
;;;
;;; The three stems of a suite have identical length and are keyed on with a
;;; single register write, so they stay sample-locked; the loop restarts when
;;; channel 0 raises its end flag.

        .module sdd_m1
        .area   CODE (ABS)

P_FROM_68K      = 0x00          ; read: command latch
P_YM_FLAGS      = 0x06          ; read: ADPCM end flags (bit n = channel n)
P_YM_A_ADDR     = 0x04
P_YM_A_DATA     = 0x05
P_YM_B_ADDR     = 0x06
P_YM_B_DATA     = 0x07
P_NMI_ON        = 0x08          ; write: enable NMI on 68000 commands
P_TO_68K        = 0x0C          ; write: reply latch

RING            = 0xF800        ; 16-byte command ring buffer
WR_IDX          = 0xF810
RD_IDX          = 0xF811
MUSIC_ON        = 0xF812
STEM_MASK       = 0xF813
SFX_RR          = 0xF814        ; next effect channel (3..5)
MUSIC_CUE       = 0xF815        ; cue index of the active suite's first stem
SFX_MASK        = 0xF816
STACK_TOP       = 0xFFFC
WAIT_PC         = 0xFFFE        ; "jr self" parked here during a slot switch

CUE_COUNT_ADDR  = 0x03FF        ; number of entries in CUE_TABLE
CUE_TABLE       = 0x0400        ; per cue: start page lo/hi, end page lo/hi

;;; ------------------------------------------------------------- vectors
        .org    0x0000
        di
        jp      boot

        .org    0x0038                  ; IM 1 interrupt (YM2610 timers, unused)
        reti

        .org    0x0066                  ; NMI: the 68000 wrote a command
nmi:
        push    af
        push    bc
        push    hl
        in      a, (P_FROM_68K)
        ld      c, a
        cp      #0x01
        jp      z, cmd_slot_switch
        cp      #0x03
        jp      z, cmd_reset
        cp      #0x04
        jr      c, nmi_exit             ; $00 and $02 are ignored
        ld      a, (WR_IDX)
        ld      l, a
        ld      h, #0xF8
        ld      (hl), c
        inc     a
        and     #0x0F
        ld      (WR_IDX), a
nmi_exit:
        ld      a, c
        out     (P_TO_68K), a           ; acknowledge by echoing the command
        pop     hl
        pop     bc
        pop     af
        retn

;;; $01: stop sound and idle in RAM while the 68000 swaps the Z80 ROM
cmd_slot_switch:
        di
        xor     a
        out     (P_TO_68K), a
        call    ym_silence
        ld      bc, #0xFE18             ; jr -2
        ld      (WAIT_PC), bc
        ld      hl, #WAIT_PC
        ld      sp, hl
        push    hl
        ld      a, #0x01
        out     (P_TO_68K), a
        retn

;;; $03: restart the driver with a clean stack
cmd_reset:
        di
        ld      sp, #STACK_TOP
        ld      hl, #start
        push    hl
        retn

;;; ---------------------------------------------------------------- init
boot:
        ld      sp, #STACK_TOP
        im      1
start:
        di
        ld      sp, #STACK_TOP
        ld      hl, #RING
        ld      b, #0x20
        xor     a
1$:     ld      (hl), a
        inc     hl
        djnz    1$
        ld      a, #3
        ld      (SFX_RR), a
        call    ym_silence
        xor     a
        out     (P_NMI_ON), a

;;; ----------------------------------------------------------- main loop
main:
        ld      a, (MUSIC_ON)
        or      a
        jr      z, poll
        in      a, (P_YM_FLAGS)
        and     #0x01                   ; channel 0 reached the end of its stem
        call    nz, music_keyon
poll:
        ld      a, (RD_IDX)
        ld      c, a
        ld      a, (WR_IDX)
        cp      c
        jr      z, main
        ld      l, c
        ld      h, #0xF8
        ld      b, (hl)                 ; B = command
        ld      a, c
        inc     a
        and     #0x0F
        ld      (RD_IDX), a

        ld      a, b
        cp      #0x07
        jr      nz, 2$
        call    ym_silence
        jr      main
2$:     cp      #0x10
        jr      z, cmd_suite
        cp      #0x11
        jr      z, cmd_suite
        and     #0xF8
        cp      #0x20
        jr      nz, 3$
        ld      a, b
        and     #0x07
        ld      (STEM_MASK), a
        call    apply_stems
        jr      main
3$:     ld      a, b
        sub     #0x80
        jr      c, main
        ld      hl, #CUE_COUNT_ADDR
        cp      (hl)
        jr      nc, main
        call    play_sfx
        jr      main

;;; Start a 3-stem suite. A = $10 or $11.
cmd_suite:
        sub     #0x10
        ld      e, a
        add     a, a
        add     a, e                    ; first stem cue = suite * 3
        ld      (MUSIC_CUE), a
        ld      b, #0x00
        ld      c, #0x87                ; dump channels 0..2
        call    ym_write_b
        ld      a, #0x01
        ld      (STEM_MASK), a          ; groove only until told otherwise
        ld      a, (MUSIC_CUE)
        ld      e, a
        ld      d, #0
4$:     ld      a, e
        call    load_cue
        inc     e
        inc     d
        ld      a, d
        cp      #3
        jr      nz, 4$
        call    apply_stems
        call    music_keyon
        ld      a, #0x01
        ld      (MUSIC_ON), a
        jp      main

;;; Key on channels 0..2 with one write so the stems stay sample-locked.
music_keyon:
        ld      b, #0x1C
        ld      c, #0x07                ; reset the end flags of channels 0..2
        call    ym_write_a
        ld      c, #0x00
        call    ym_write_a
        ld      b, #0x00
        ld      c, #0x07
        call    ym_write_b
        ret

;;; Channel level/pan for the stems: audible ($DF) or silent ($00).
apply_stems:
        ld      a, (STEM_MASK)
        ld      e, a
        ld      b, #0x08
        ld      d, #3
5$:     ld      c, #0x00
        rr      e
        jr      nc, 6$
        ld      c, #0xDF
6$:     call    ym_write_b
        inc     b
        dec     d
        jr      nz, 5$
        ret

;;; Play cue A on the next effect channel (3..5).
play_sfx:
        ld      e, a
        ld      a, (SFX_RR)
        ld      d, a                    ; D = channel
        inc     a
        cp      #6
        jr      c, 7$
        ld      a, #3
7$:     ld      (SFX_RR), a
        ld      a, #1
        ld      b, d
8$:     add     a, a
        djnz    8$                      ; A = 1 << channel
        ld      (SFX_MASK), a
        or      #0x80
        ld      c, a
        ld      b, #0x00
        call    ym_write_b              ; dump the channel
        ld      a, #0x08
        add     a, d
        ld      b, a
        ld      c, #0xDF
        call    ym_write_b              ; full level, both speakers
        ld      a, e
        call    load_cue
        ld      a, (SFX_MASK)
        ld      c, a
        ld      b, #0x1C
        call    ym_write_a              ; reset its end flag
        ld      c, #0x00
        call    ym_write_a
        ld      a, (SFX_MASK)
        ld      c, a
        ld      b, #0x00
        call    ym_write_b              ; key on
        ret

;;; Program start/end pages of cue A into ADPCM-A channel D.
;;; Clobbers A, BC, HL.
load_cue:
        ld      l, a
        ld      h, #0
        add     hl, hl
        add     hl, hl
        ld      bc, #CUE_TABLE
        add     hl, bc
        ld      a, #0x10
        add     a, d
        ld      b, a
        ld      c, (hl)
        inc     hl
        call    ym_write_b              ; start address LSB
        ld      a, #0x18
        add     a, d
        ld      b, a
        ld      c, (hl)
        inc     hl
        call    ym_write_b              ; start address MSB
        ld      a, #0x20
        add     a, d
        ld      b, a
        ld      c, (hl)
        inc     hl
        call    ym_write_b              ; end address LSB
        ld      a, #0x28
        add     a, d
        ld      b, a
        ld      c, (hl)
        call    ym_write_b              ; end address MSB
        ret

;;; Stop every sound source and restore the ADPCM-A master level.
ym_silence:
        ld      b, #0x00
        ld      c, #0xBF                ; dump all six ADPCM-A channels
        call    ym_write_b
        ld      b, #0x01
        ld      c, #0x3F                ; ADPCM-A master level
        call    ym_write_b
        ld      b, #0x10
        ld      c, #0x01                ; ADPCM-B reset
        call    ym_write_a
        ld      c, #0x00
        call    ym_write_a
        ld      b, #0x1C
        ld      c, #0xBF                ; reset all ADPCM end flags
        call    ym_write_a
        ld      c, #0x00
        call    ym_write_a
        ld      b, #0x07
        ld      c, #0x3F                ; SSG mixer: all off
        call    ym_write_a
        ld      b, #0x08
        ld      c, #0x00                ; SSG volumes
        call    ym_write_a
        inc     b
        call    ym_write_a
        inc     b
        call    ym_write_a
        ld      b, #0x28                ; FM key off, channels 1..4
        ld      c, #0x01
        call    ym_write_a
        ld      c, #0x02
        call    ym_write_a
        ld      c, #0x05
        call    ym_write_a
        ld      c, #0x06
        call    ym_write_a
        xor     a
        ld      (MUSIC_ON), a
        ret

;;; Register writes. B = register, C = value. Preserve every register.
ym_write_a:
        push    af
        ld      a, b
        out     (P_YM_A_ADDR), a
        call    ym_delay
        ld      a, c
        out     (P_YM_A_DATA), a
        call    ym_delay
        pop     af
        ret

ym_write_b:
        push    af
        ld      a, b
        out     (P_YM_B_ADDR), a
        call    ym_delay
        ld      a, c
        out     (P_YM_B_DATA), a
        call    ym_delay
        pop     af
        ret

;;; Settle time between YM2610 accesses (longer than the chip's busy period).
ym_delay:
        push    bc
        ld      b, #6
9$:     djnz    9$
        pop     bc
        ret

driver_end:
