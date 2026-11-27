/*
 * Super Dig Dug — SNK Neo Geo MVS Hardware & Platform Abstraction Header
 * Target: 68000 @ 12 MHz, LSPC2 Video (320x224), Z80 + YM2610 Audio
 */
#ifndef NEOGEO_HW_H
#define NEOGEO_HW_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

/* Screen & Confirmed Horizontal Side-HUD Geometry */
#define MVS_SCREEN_W          320
#define MVS_SCREEN_H          224
#define PLAYFIELD_PX_W        224   /* x = 0..223 (14 x 16px sprite strips) */
#define PLAYFIELD_PX_H        224   /* y = 0..223 (14 x 16px tiles = 28 x 8px cells) */
#define SIDE_HUD_PX_X         224   /* x = 224..319 (96px = 12 x 8px FIX columns) */
#define SIDE_HUD_FIX_COL_MIN  28    /* FIX col 28 * 8 = 224 */
#define SIDE_HUD_FIX_COL_MAX  39    /* FIX col 39 * 8 = 312 */
#define FIX_VISIBLE_ROW_TOP   2     /* LSPC2 visible rows are 2..29 (28 rows = 224px) */
#define FIX_VISIBLE_ROW_BOT   29

/* Hardware Limits & Engineering Guardrails */
#define MVS_MAX_SPRITES             381u
#define MVS_SPRITE_STRIPS_HW_MAX     96u
#define MVS_SPRITE_STRIPS_ENG_MAX    84u

/* LSPC2 VRAM Word Addresses */
#define VRAM_SCB1_BASE   0x0000u   /* 64 words per sprite (32 vertical tiles x 2 words) */
#define VRAM_FIX_BASE    0x7000u   /* 40 cols x 32 rows, column-major */
#define VRAM_SCB2_BASE   0x8000u   /* Shrink: 0x0FFF = 1:1 full scale */
#define VRAM_SCB3_BASE   0x8200u   /* ((496 - y) << 7) | (sticky << 6) | height_tiles */
#define VRAM_SCB4_BASE   0x8400u   /* (x & 0x1FF) << 7 */

#define SCB2_NO_SHRINK   0x0FFFu

/* Input Button Bitmasks (normalized active-high in software) */
#define INPUT_UP         0x0001u
#define INPUT_DOWN       0x0002u
#define INPUT_LEFT       0x0004u
#define INPUT_RIGHT      0x0008u
#define INPUT_BTN_A      0x0010u   /* Pump / Harpoon */
#define INPUT_BTN_B      0x0020u   /* Special Weapon (Phase 2) / Prev (Viewer) */
#define INPUT_BTN_C      0x0040u   /* Module / Next (Viewer) */
#define INPUT_BTN_D      0x0080u   /* Debug / Grid Overlay (Viewer) */
#define INPUT_START      0x0100u
#define INPUT_SELECT     0x0200u
#define INPUT_COIN       0x0400u

#ifndef SDD_HOST_TEST
/* Real 68000 Memory-Mapped Registers on Neo Geo MVS */
#define REG_P1CNT        (*(volatile const uint8_t  *)0x300000u)
#define REG_DIPSW        (*(volatile const uint8_t  *)0x300001u)
#define REG_WATCHDOG     (*(volatile uint8_t        *)0x300001u)
#define REG_SOUND        (*(volatile uint8_t        *)0x320000u)
#define REG_STATUS_A     (*(volatile const uint8_t  *)0x320001u)
#define REG_P2CNT        (*(volatile const uint8_t  *)0x340000u)
#define REG_STATUS_B     (*(volatile const uint8_t  *)0x380000u)

#define REG_BRDFIX       (*(volatile uint8_t        *)0x3A000Bu)
#define REG_CRTFIX       (*(volatile uint8_t        *)0x3A001Bu)
#define REG_PALBANK1     (*(volatile uint8_t        *)0x3A000Fu)
#define REG_PALBANK0     (*(volatile uint8_t        *)0x3A001Fu)

#define REG_VRAMADDR     (*(volatile uint16_t       *)0x3C0000u)
#define REG_VRAMRW       (*(volatile uint16_t       *)0x3C0002u)
#define REG_VRAMMOD      (*(volatile int16_t        *)0x3C0004u)
#define REG_LSPCMODE     (*(volatile uint16_t       *)0x3C0006u)
#define REG_IRQACK       (*(volatile uint16_t       *)0x3C000Cu)

#define MVS_PALETTE_RAM  ((volatile uint16_t *)0x400000u)

/* BIOS work RAM and backup RAM used by the credit/start contract */
#define BIOS_USER_MODE       (*(volatile uint8_t       *)0x10FDAFu)
#define BRAM_P1_CREDITS_BCD  (*(volatile const uint8_t *)0xD00034u)
#define BIOS_USER_MODE_DEMO  1u
#define BIOS_USER_MODE_GAME  2u
#else
/* Host Native Unit-Test Mock Backing Buffers */
extern uint16_t g_mock_vram[0x8800];
extern uint16_t g_mock_palette_ram[256 * 16];
extern uint8_t  g_mock_last_sound_cmd;
extern uint32_t g_mock_watchdog_kicks;
extern uint8_t  g_mock_credits;
#endif

typedef struct {
    uint16_t held[2];
    uint16_t pressed[2];
    uint16_t released[2];
    uint16_t sys_held;
    uint16_t sys_pressed;
} mvs_input_state_t;

typedef struct {
    uint16_t sprites_used;
    uint16_t worst_scanline_strips;
    uint8_t  scanline_strips[MVS_SCREEN_H];
} mvs_frame_stats_t;

extern volatile uint32_t g_vblank_counter;
extern mvs_input_state_t g_input;
extern mvs_frame_stats_t g_frame_stats;

void mvs_hw_init(void);
void mvs_kick_watchdog(void);
void mvs_wait_vblank(void);
void mvs_load_palettes(const uint16_t palettes[256][16]);
void mvs_set_palette_16(uint8_t pal_id, const uint16_t words[16]);
void mvs_poll_inputs(void);
void mvs_snd_send(uint8_t cmd);

/* MVS credit/start contract (BIOS owns coins and credits; see crt0_mvs.S) */
#define MVS_START_P1 0x01u
#define MVS_START_P2 0x02u
extern volatile uint8_t g_bios_start_req;  /* players accepted by PLAYER_START */
extern volatile uint8_t g_start_accept;    /* non-zero while a start may be accepted */
extern volatile uint8_t g_coin_sound_cmd;  /* Z80 command sent by COIN_SOUND */
uint8_t mvs_credits(void);                 /* credits held by the BIOS, 0..99 */
void    mvs_set_start_accept(bool accept);
uint8_t mvs_take_start_request(void);      /* returns MVS_START_* bits once */
void    mvs_set_in_game(bool in_game);     /* BIOS_USER_MODE: game vs demo/title */
void    sdd_crash_report(uint32_t vector, const uint16_t *frame);

/* Shadow Sprite & FIX Layer Staging API (flushed atomically during VBlank) */
void     mvs_sprites_begin(void);
uint16_t mvs_alloc_sprite_strip(
    int16_t x,
    int16_t y,
    uint8_t height_tiles,
    bool sticky,
    const uint16_t *c_tiles,
    const uint8_t  *palettes,
    uint8_t flip_flags
);
void mvs_draw_meta_sprite(
    int16_t x_top_left,
    int16_t y_top_left,
    uint8_t cols,
    uint8_t rows,
    uint16_t first_c_tile,
    uint8_t palette_id,
    bool hflip,
    bool vflip
);
void mvs_fix_clear_all(void);
void mvs_fix_put(uint8_t col, uint8_t row, uint16_t s_tile_id, uint8_t fix_pal_id);
void mvs_fix_print(uint8_t col, uint8_t row, uint8_t fix_pal_id, const char *text);
void mvs_fix_print_u32(uint8_t col, uint8_t row, uint8_t width, uint8_t fix_pal_id, uint32_t val);
void mvs_video_commit_vblank(void);

#endif /* NEOGEO_HW_H */
