/*
 * Super Dig Dug — SNK Neo Geo MVS 68000 cartridge header and C runtime startup.
 *
 * Layout follows the documented cartridge program header (vectors at $000000,
 * "NEO-GEO" header at $000100, BIOS jump table at $000122, security-code
 * pointer at $000182). Interrupt levels on cartridge systems: level 1 = VBlank,
 * level 2 = timer, level 3 = pending after cold boot.
 *
 * BIOS contract used here:
 *   USER ($122)          BIOS_USER_REQUEST 0 = init, 1 = eye-catcher,
 *                        2 = demo, 3 = title (credit inserted).
 *   PLAYER_START ($128)  BIOS_START_FLAG holds the players that pressed start
 *                        with credit available; the game clears the bits it
 *                        refuses and sets BIOS_USER_MODE = 2 when it accepts.
 *   VBlank               while BIOS_SYSTEM_MODE bit 7 is clear the BIOS owns
 *                        the interrupt; otherwise the game acknowledges it and
 *                        calls SYSTEM_IO once per frame (inputs, coins, start).
 */

#define REG_WATCHDOG        0x300001
#define REG_SOUND           0x320000
#define REG_SWPROM          0x3A0013
#define REG_IRQACK          0x3C000C

#define BIOS_SYSTEM_MODE    0x10FD80
#define BIOS_USER_REQUEST   0x10FDAE
#define BIOS_USER_MODE      0x10FDAF
#define BIOS_START_FLAG     0x10FDB4

#define SYSTEM_INT1         0xC00438
#define SYSTEM_INT2         0xC0043E
#define SYSTEM_RETURN       0xC00444
#define SYSTEM_IO           0xC0044A

#define STACK_TOP           0x10F300

    .section .vectors, "ax"
    .globl  _start
    .globl  _vblank_isr

/* $000000 - $0000FF: 68000 exception vector table */
_vectors_base:
    .long   STACK_TOP           /* $00: initial SSP */
    .long   0x00C00402          /* $04: reset PC -> system ROM cold boot entry */
    .long   _exc_bus            /* $08: bus error */
    .long   _exc_address        /* $0C: address error */
    .long   _exc_illegal        /* $10: illegal instruction */
    .long   _exc_zerodiv        /* $14: division by zero */
    .long   _exc_other          /* $18: CHK */
    .long   _exc_other          /* $1C: TRAPV */
    .long   _exc_other          /* $20: privilege violation */
    .long   _exc_other          /* $24: trace */
    .long   _exc_other          /* $28: line 1010 */
    .long   _exc_other          /* $2C: line 1111 */
    .rept   12
    .long   _exc_other          /* $30..$5C: reserved / uninitialized interrupt */
    .endr
    .long   _irq_ignore         /* $60: spurious interrupt */
    .long   _vblank_isr         /* $64: level 1 autovector — VBlank */
    .long   _timer_isr          /* $68: level 2 autovector — timer */
    .long   _irq_ignore         /* $6C: level 3 autovector — cold boot */
    .rept   36
    .long   _irq_ignore         /* $70..$FC: remaining autovectors and traps */
    .endr

/* $000100: cartridge program header */
    .org    0x0100
    .ascii  "NEO-GEO"
    .byte   0x00                /* $107: system version (cartridge) */
    .word   0x0482              /* $108: NGH number (development ID) */
    .long   0x00080000          /* $10A: P-ROM size = 512 KiB */
    .long   0x0010E000          /* $10E: backup-RAM mirror block in work RAM */
    .word   0x0040              /* $112: 64 bytes of saved data */
    .byte   0x02                /* $114: eye-catcher mode 2 = none */
    .byte   0x00                /* $115: eye-catcher sprite bank */
    .long   _soft_dip_jp        /* $116: JP soft DIP table */
    .long   _soft_dip_us        /* $11A: US soft DIP table */
    .long   _soft_dip_eu        /* $11E: EU soft DIP table */

/* $000122: BIOS jump table (each jmp.l is 6 bytes) */
    jmp     _user_entry.l       /* $122: USER */
    jmp     _player_start.l     /* $128: PLAYER_START */
    jmp     _demo_end.l         /* $12E: DEMO_END */
    jmp     _coin_sound.l       /* $134: COIN_SOUND */

    .org    0x0182
    .long   _security_code      /* $182: pointer to the cartridge recognition code */

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

/* Soft DIP tables (shared by all regions) */
    .align  2
_soft_dip_jp:
_soft_dip_us:
_soft_dip_eu:
    .ascii  "SUPER DIG DUG   "  /* 16-byte title */
    .word   0xFFFF, 0xFFFF      /* unused time settings */
    .byte   0xFF, 0xFF          /* unused count settings */
    .byte   0x24                /* setting 1: default index 2, 4 choices */
    .byte   0x02                /* setting 2: default index 0, 2 choices */
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

/* ------------------------------------------------------------------ USER */
_start:
_user_entry:
    move.b  %d0, REG_WATCHDOG
    moveq   #0, %d0
    move.b  BIOS_USER_REQUEST, %d0
    bne.s   1f
    /* Request 0: one-time init. Nothing to prepare; hand control back. */
    jmp     SYSTEM_RETURN

1:
    /* Requests 1..3 never return: restart the C runtime and run the game. */
    move.w  #0x2700, %sr
    lea     STACK_TOP, %sp
    move.b  %d0, REG_SWPROM     /* cartridge vector table */
    move.l  %d0, -(%sp)         /* argument for sdd_cart_main(request) */

    /* Copy .data from ROM to work RAM */
    lea     _etext, %a0
    lea     _sdata, %a1
    lea     _edata, %a2
    bra.s   3f
2:  move.w  (%a0)+, (%a1)+
3:  cmpa.l  %a2, %a1
    blo.s   2b

    /* Zero .bss */
    lea     _sbss, %a1
    lea     _ebss, %a2
    bra.s   5f
4:  clr.w   (%a1)+
5:  cmpa.l  %a2, %a1
    blo.s   4b

    move.w  #0x0007, REG_IRQACK /* drop any pending interrupt */
    bset    #7, BIOS_SYSTEM_MODE/* the game services VBlank from here on */
    move.w  #0x2000, %sr

    jsr     sdd_cart_main
    addq.l  #4, %sp
    jmp     SYSTEM_RETURN

/* ---------------------------------------------------------- PLAYER_START */
/* Called by the BIOS from SYSTEM_IO when start is pressed with credit left. */
_player_start:
    move.b  %d0, REG_WATCHDOG
    tst.b   g_start_accept
    beq.s   1f
    move.b  BIOS_START_FLAG, g_bios_start_req
    clr.b   g_start_accept
    move.b  #2, BIOS_USER_MODE  /* in game: BIOS deducts the credit */
    rts
1:  clr.b   BIOS_START_FLAG     /* refuse: no credit is taken */
    rts

_demo_end:
    rts

_coin_sound:
    move.b  g_coin_sound_cmd, REG_SOUND
    rts

/* ------------------------------------------------------------ interrupts */
_vblank_isr:
    btst    #7, BIOS_SYSTEM_MODE
    bne.s   1f
    jmp     SYSTEM_INT1         /* BIOS owns the frame */
1:  movem.l %d0-%d7/%a0-%a6, -(%sp)
    move.w  #0x0004, REG_IRQACK
    move.b  %d0, REG_WATCHDOG
    jsr     SYSTEM_IO           /* inputs, coins, credits, start */
    addq.l  #1, g_vblank_counter
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rte

_timer_isr:
    move.w  #0x0002, REG_IRQACK
    rte

_irq_ignore:
    move.w  #0x0001, REG_IRQACK
    rte

/* ------------------------------------------------------------ exceptions */
/* Fatal CPU exceptions land in a C reporter that prints on the FIX layer.  */
_exc_bus:
    moveq   #2, %d0
    bra.s   _exc_common
_exc_address:
    moveq   #3, %d0
    bra.s   _exc_common
_exc_illegal:
    moveq   #4, %d0
    bra.s   _exc_common
_exc_zerodiv:
    moveq   #5, %d0
    bra.s   _exc_common
_exc_other:
    moveq   #0, %d0
_exc_common:
    move.w  #0x2700, %sr
    move.l  %sp, %a0
    lea     STACK_TOP, %sp
    move.l  %a0, -(%sp)         /* faulting stack frame */
    move.l  %d0, -(%sp)         /* vector number (0 = unclassified) */
    jsr     sdd_crash_report
2:  move.b  %d0, REG_WATCHDOG
    bra.s   2b

    .section .bss
    .globl  g_bios_start_req
    .globl  g_start_accept
    .globl  g_coin_sound_cmd
g_bios_start_req:
    .space  1
g_start_accept:
    .space  1
g_coin_sound_cmd:
    .space  1
    .space  1
