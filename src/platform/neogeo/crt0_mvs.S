/*
 * Super Dig Dug — SNK Neo Geo MVS 68000 Cartridge Header & C Runtime Startup
 * Verified against wiki.neogeodev.org (68k_program_header, Security_code, USER_subroutine).
 * Note: On Neo Geo MVS, VBlank is Level 1 Autovector ($000064) and Timer is Level 2 ($000068).
 */

    .section .vectors, "ax"
    .globl _start
    .globl _vblank_isr

/* $000000 - $0000FF: 68000 Exception Vector Table */
_vectors_base:
    .long   0x0010F300          /* $00: Initial SSP (top of user Work RAM below BIOS $10F300) */
    .long   0x00C00402          /* $04: Reset PC -> MVS System ROM cold boot entry */
    .rept   22
    .long   _exc_ignore         /* $08..$5C: Bus/Address/Illegal/Trap vectors */
    .endr
    .long   _irq_ignore         /* $60: Spurious interrupt */
    .long   _vblank_isr         /* $64: Level 1 Autovector — LSPC2 VBlank IRQ */
    .long   _timer_isr          /* $68: Level 2 Autovector — LSPC2 Timer IRQ */
    .long   _irq_ignore         /* $6C: Level 3 Autovector — Cold reset / unused */
    .rept   36
    .long   _irq_ignore         /* $70..$FC: Remaining autovectors & traps */
    .endr

/* $000100: SNK Neo Geo Cartridge Program Header */
    .org    0x0100
    .ascii  "NEO-GEO"
    .byte   0x00                /* $107: System version (0 = MVS/AES cartridge) */
    .word   0x0482              /* $108: Homebrew NGH BCD ID (unused free range) */
    .long   0x00080000          /* $10A: P-ROM size = 512 KiB */
    .long   0x0010E000          /* $10E: Backup RAM mirror block in user Work RAM */
    .word   0x0040              /* $112: 64 bytes saved high-score & config block */
    .byte   0x02                /* $114: Eye-catcher = 2 (skip BIOS logo, boot straight to USER) */
    .byte   0x00                /* $115: Eye-catcher bank */
    .long   _soft_dip_jp        /* $116: JP Soft-DIP config pointer */
    .long   _soft_dip_us        /* $11A: US Soft-DIP config pointer */
    .long   _soft_dip_eu        /* $11E: EU Soft-DIP config pointer */

/* $000122: BIOS Jump Table (each jmp.l is 6 bytes) */
    jmp     _user_entry.l       /* $122: USER */
    jmp     _player_start.l     /* $128: PLAYER_START */
    jmp     _demo_end.l         /* $12E: DEMO_END */
    jmp     _coin_sound.l       /* $134: COIN_SOUND */

    .org    0x0182
    .long   _security_code      /* $182: Pointer to mandatory cartridge recognition stub */

    .align  2
_security_code:
    .long   0x76004A6D, 0x0A146600, 0x003C206D, 0x0A043E2D
    .long   0x0A0813C0, 0x00300001, 0x32100C01, 0x00FF671A
    .long   0x30280002, 0xB02D0ACE, 0x66103028, 0x0004B02D
    .long   0x0ACF6606, 0xB22D0AD0, 0x67085088, 0x51CFFFD4
    .long   0x36074E75, 0x206D0A04, 0x3E2D0A08, 0x3210E049
    .long   0x0C0100FF, 0x671A3010, 0xB02D0ACE, 0x66123028
    .long   0x0002E048, 0xB02D0ACF, 0x6606B22D, 0x0AD06708
    .long   0x588851CF, 0xFFD83607
    .word   0x4E75

/* Soft-DIP Configuration Tables (JP / US / EU) */
    .align  2
_soft_dip_jp:
_soft_dip_us:
_soft_dip_eu:
    .ascii  "SUPER DIG DUG   "  /* 16-byte cabinet game title */
    .word   0xFFFF, 0xFFFF      /* Unused time settings */
    .byte   0xFF, 0xFF          /* Unused count settings */
    .byte   0x24                /* Setting 1: LIVES (default idx 2 = "3 LIVES", 4 choices) */
    .byte   0x02                /* Setting 2: ENGINE MODE (default idx 0 = "1982 REPLICA", 2 choices) */
    .byte   0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
    .ascii  "LIVES       "
    .ascii  "1 LIFE      "
    .ascii  "2 LIVES     "
    .ascii  "3 LIVES     "
    .ascii  "5 LIVES     "
    .ascii  "GAME RULES  "
    .ascii  "1982 CLASSIC"
    .ascii  "SUPER MVS   "

    .section .text, "ax"
    .align  2

_start:
_user_entry:
    move.b  d0, 0x300001        /* Kick watchdog */
    /* Check BIOS_USER_REQUEST ($10FDAE): 0 = Init Backup RAM, 1 = Logo, 2 = Demo/Attract, 3 = Title */
    moveq   #0, d0
    move.b  0x10FDAE, d0
    tst.b   d0
    bne.s   1f
    /* Command 0: Backup RAM init — return cleanly to BIOSF_SYSTEM_RETURN ($C00444) */
    clr.b   0x10FDAF
    jmp     0xC00444.l

1:
    /* Switch vector table to cartridge ROM ($3A0013 = REG_SWPROM) and init C runtime once */
    lea     0x10F300.l, sp
    move.w  #0x2700, sr         /* Mask interrupts during .data/.bss setup */
    move.b  d0, 0x3A0013        /* Map cart vectors ($000000..$00007F) */
    move.b  #0x80, 0x10FD80     /* BIOS_SYSTEM_MODE = game control */
    move.b  #0x02, 0x10FDAF     /* BIOS_USER_MODE = in game/attract */

    /* Copy .data from ROM (_etext) to Work RAM (_sdata.._edata) */
    lea     _etext.l, a0
    lea     _sdata.l, a1
    lea     _edata.l, a2
    bra.s   3f
2:  move.w  (a0)+, (a1)+
3:  cmpa.l  a2, a1
    blo.s   2b

    /* Zero .bss (_sbss.._ebss) */
    lea     _sbss.l, a1
    lea     _ebss.l, a2
    bra.s   5f
4:  clr.w   (a1)+
5:  cmpa.l  a2, a1
    blo.s   4b

    move.w  #0x0007, 0x3C000C   /* Clear pending LSPC interrupts */
    move.w  #0x2000, sr         /* Enable VBlank interrupts (IPL >= 1) */

    jsr     sdd_cart_main.l
    jmp     0xC00444.l          /* BIOSF_SYSTEM_RETURN */

_player_start:
    move.b  #1, g_bios_start_req
    rts

_demo_end:
    rts

_coin_sound:
    move.b  #0x80, 0x320000     /* Trigger coin SFX cue on Z80 */
    rts

_vblank_isr:
    movem.l d0-d1/a0-a1, -(sp)
    move.w  #0x0004, 0x3C000C   /* Acknowledge VBlank interrupt (bit 2) */
    move.b  d0, 0x300001        /* Kick hardware watchdog */
    addq.l  #1, g_vblank_counter
    /* If BIOS is still owning system mode, let BIOS_SYSTEM_IO run */
    btst    #7, 0x10FD80
    beq.s   9f
    movem.l (sp)+, d0-d1/a0-a1
    rte
9:  movem.l (sp)+, d0-d1/a0-a1
    jmp     0xC00438.l          /* BIOS VBlank handler fallback */

_timer_isr:
    move.w  #0x0002, 0x3C000C   /* Acknowledge Timer interrupt (bit 1) */
    rte

_exc_ignore:
_irq_ignore:
    move.w  #0x0001, 0x3C000C
    rte

    .section .bss
    .globl  g_bios_start_req
g_bios_start_req:
    .space  2
