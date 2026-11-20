/*
 * Super Dig Dug — Neo Geo MVS Platform Video, Palette, Input & Sound Implementation
 * Zero dynamic allocation; deterministic VBlank commit into LSPC2 VRAM.
 */
#include "neogeo_hw.h"
#include "../../../assets/generated/sdd_assets.h"

volatile uint32_t g_vblank_counter = 0u;
mvs_input_state_t g_input;
mvs_frame_stats_t g_frame_stats;

#ifdef SDD_HOST_TEST
uint16_t g_mock_vram[0x8800];
uint16_t g_mock_palette_ram[256 * 16];
uint8_t  g_mock_last_sound_cmd = 0u;
uint32_t g_mock_watchdog_kicks = 0u;
#endif

/* Shadow buffers in 68000 Work RAM (flushed during VBlank) */
#define SHADOW_MAX_SPRITES 160u

typedef struct {
    uint16_t scb1[32];  /* Up to 16 vertical tiles (256px) x 2 words */
    uint16_t scb2;
    uint16_t scb3;
    uint16_t scb4;
    uint8_t  height_tiles;
} shadow_sprite_t;

static shadow_sprite_t s_sprites[SHADOW_MAX_SPRITES];
static uint16_t        s_sprite_count = 0u;
static uint16_t        s_prev_sprite_count = 0u;
static uint16_t        s_fix_shadow[40][32];
static uint8_t         s_fix_dirty_col[40];

static inline void vram_write_block(uint16_t addr, int16_t mod, const uint16_t *words, uint16_t count) {
#ifndef SDD_HOST_TEST
    REG_VRAMMOD = mod;
    REG_VRAMADDR = addr;
    for (uint16_t i = 0u; i < count; ++i) {
        REG_VRAMRW = words[i];
    }
#else
    uint16_t cur = addr;
    for (uint16_t i = 0u; i < count; ++i) {
        if (cur < 0x8800u) {
            g_mock_vram[cur] = words[i];
        }
        cur = (uint16_t)(cur + (uint16_t)mod);
    }
#endif
}

void mvs_kick_watchdog(void) {
#ifndef SDD_HOST_TEST
    REG_WATCHDOG = 0x00u;
#else
    ++g_mock_watchdog_kicks;
#endif
}

void mvs_hw_init(void) {
    mvs_kick_watchdog();
#ifndef SDD_HOST_TEST
    REG_PALBANK0 = 0x00u;
    REG_CRTFIX   = 0x00u;   /* Select cartridge S1 FIX ROM instead of BIOS sfix */
    REG_IRQACK   = 0x0007u; /* Acknowledge all pending LSPC interrupts */
#endif
    mvs_load_palettes(sdd_palettes);
    mvs_fix_clear_all();
    s_sprite_count = 0u;
    s_prev_sprite_count = MVS_MAX_SPRITES;
    mvs_video_commit_vblank();
}

void mvs_wait_vblank(void) {
#ifndef SDD_HOST_TEST
    uint32_t start = g_vblank_counter;
    while (g_vblank_counter == start) {
        mvs_kick_watchdog();
    }
#else
    ++g_vblank_counter;
    mvs_kick_watchdog();
#endif
}

void mvs_load_palettes(const uint16_t palettes[256][16]) {
    for (uint16_t p = 0u; p < 256u; ++p) {
        mvs_set_palette_16((uint8_t)p, palettes[p]);
    }
}

void mvs_set_palette_16(uint8_t pal_id, const uint16_t words[16]) {
    uint16_t base = (uint16_t)pal_id * 16u;
#ifndef SDD_HOST_TEST
    MVS_PALETTE_RAM[base] = 0x8000u; /* Enforce transparent reference black at index 0 */
    for (uint16_t i = 1u; i < 16u; ++i) {
        MVS_PALETTE_RAM[base + i] = words[i];
    }
#else
    g_mock_palette_ram[base] = 0x8000u;
    for (uint16_t i = 1u; i < 16u; ++i) {
        g_mock_palette_ram[base + i] = words[i];
    }
#endif
}

void mvs_poll_inputs(void) {
    uint16_t raw_p[2] = {0u, 0u};
    uint16_t raw_sys = 0u;

#ifndef SDD_HOST_TEST
    /* Neo Geo inputs are active-low in hardware */
    uint8_t p1 = (uint8_t)~REG_P1CNT;
    uint8_t p2 = (uint8_t)~REG_P2CNT;
    uint8_t sa = (uint8_t)~REG_STATUS_A;
    uint8_t sb = (uint8_t)~REG_STATUS_B;

    if (p1 & 0x01u) raw_p[0] |= INPUT_UP;
    if (p1 & 0x02u) raw_p[0] |= INPUT_DOWN;
    if (p1 & 0x04u) raw_p[0] |= INPUT_LEFT;
    if (p1 & 0x08u) raw_p[0] |= INPUT_RIGHT;
    if (p1 & 0x10u) raw_p[0] |= INPUT_BTN_A;
    if (p1 & 0x20u) raw_p[0] |= INPUT_BTN_B;
    if (p1 & 0x40u) raw_p[0] |= INPUT_BTN_C;
    if (p1 & 0x80u) raw_p[0] |= INPUT_BTN_D;

    if (p2 & 0x01u) raw_p[1] |= INPUT_UP;
    if (p2 & 0x02u) raw_p[1] |= INPUT_DOWN;
    if (p2 & 0x04u) raw_p[1] |= INPUT_LEFT;
    if (p2 & 0x08u) raw_p[1] |= INPUT_RIGHT;
    if (p2 & 0x10u) raw_p[1] |= INPUT_BTN_A;
    if (p2 & 0x20u) raw_p[1] |= INPUT_BTN_B;
    if (p2 & 0x40u) raw_p[1] |= INPUT_BTN_C;
    if (p2 & 0x80u) raw_p[1] |= INPUT_BTN_D;

    if (sb & 0x01u) { raw_p[0] |= INPUT_START;  raw_sys |= INPUT_START;  }
    if (sb & 0x02u) { raw_p[0] |= INPUT_SELECT; raw_sys |= INPUT_SELECT; }
    if (sb & 0x04u) { raw_p[1] |= INPUT_START;  }
    if (sb & 0x08u) { raw_p[1] |= INPUT_SELECT; }
    if (sa & 0x03u) { raw_sys  |= INPUT_COIN;   }
    if (sa & 0x80u) { raw_sys  |= INPUT_TEST;   }

    for (uint8_t i = 0u; i < 2u; ++i) {
        uint16_t prev = g_input.held[i];
        g_input.held[i]     = raw_p[i];
        g_input.pressed[i]  = (uint16_t)(raw_p[i] & ~prev);
        g_input.released[i] = (uint16_t)(prev & ~raw_p[i]);
    }
    g_input.sys_pressed = (uint16_t)(raw_sys & ~g_input.sys_held);
    g_input.sys_held    = raw_sys;
#else
    /* In host tests, tests write directly into g_input.held[] before calling mvs_poll_inputs() */
    (void)raw_p;
    (void)raw_sys;
#endif
}

void mvs_snd_send(uint8_t cmd) {
#ifndef SDD_HOST_TEST
    REG_SOUND = cmd;
#else
    g_mock_last_sound_cmd = cmd;
#endif
}

void mvs_sprites_begin(void) {
    s_sprite_count = 0u;
    g_frame_stats.sprites_used = 0u;
    g_frame_stats.worst_scanline_strips = 0u;
    for (uint16_t y = 0u; y < MVS_SCREEN_H; ++y) {
        g_frame_stats.scanline_strips[y] = 0u;
    }
}

uint16_t mvs_alloc_sprite_strip(
    int16_t x,
    int16_t y,
    uint8_t height_tiles,
    bool sticky,
    const uint16_t *c_tiles,
    const uint8_t  *palettes,
    uint8_t flip_flags
) {
    /* Hardware sprite 0 is avoided because sticky chaining references previous sprite; start at slot 1 */
    if (height_tiles == 0u || s_sprite_count >= (SHADOW_MAX_SPRITES - 1u)) {
        return 0u;
    }
    if (height_tiles > 16u) {
        height_tiles = 16u;
    }

    uint16_t idx = ++s_sprite_count;
    shadow_sprite_t *sp = &s_sprites[idx];
    sp->height_tiles = height_tiles;
    sp->scb2 = SCB2_NO_SHRINK;

    /* Neo Geo Y coordinate in SCB3 bits 15..7 is ((496 - y_screen) & 0x1FF) */
    uint16_t hw_y = (uint16_t)((496 - y) & 0x01FF);
    sp->scb3 = (uint16_t)((hw_y << 7) | (sticky ? 0x0040u : 0x0000u) | (height_tiles & 0x3Fu));
    sp->scb4 = (uint16_t)(((uint16_t)x & 0x01FFu) << 7);

    for (uint8_t t = 0u; t < height_tiles; ++t) {
        uint16_t c_id = c_tiles[t];
        uint8_t  pal  = palettes ? palettes[t] : PAL_FIX_TEXT;
        sp->scb1[t * 2u]      = c_id;
        sp->scb1[t * 2u + 1u] = (uint16_t)(((uint16_t)pal << 8) | (flip_flags & 0x03u));
    }

    /* Update scanline strip budget telemetry */
    int16_t y0 = y < 0 ? 0 : y;
    int16_t y1 = (int16_t)(y + (int16_t)height_tiles * 16);
    if (y1 > MVS_SCREEN_H) {
        y1 = MVS_SCREEN_H;
    }
    for (int16_t sy = y0; sy < y1; ++sy) {
        uint8_t c = ++g_frame_stats.scanline_strips[sy];
        if (c > g_frame_stats.worst_scanline_strips) {
            g_frame_stats.worst_scanline_strips = c;
        }
    }
    g_frame_stats.sprites_used = s_sprite_count;
    return idx;
}

void mvs_draw_meta_sprite(
    int16_t x_top_left,
    int16_t y_top_left,
    uint8_t cols,
    uint8_t rows,
    uint16_t first_c_tile,
    uint8_t palette_id,
    bool hflip,
    bool vflip
) {
    uint16_t strip_tiles[16];
    uint8_t  strip_pals[16];
    uint8_t  flip_bits = (uint8_t)((hflip ? 0x01u : 0x00u) | (vflip ? 0x02u : 0x00u));

    for (uint8_t r = 0u; r < rows && r < 16u; ++r) {
        strip_pals[r] = palette_id;
    }

    for (uint8_t c = 0u; c < cols; ++c) {
        uint8_t src_col = hflip ? (uint8_t)(cols - 1u - c) : c;
        for (uint8_t r = 0u; r < rows && r < 16u; ++r) {
            uint8_t src_row = vflip ? (uint8_t)(rows - 1u - r) : r;
            strip_tiles[r] = (uint16_t)(first_c_tile + (uint16_t)src_col * rows + src_row);
        }
        /* Sticky bit chains strips 1..cols-1 horizontally to strip 0 */
        bool sticky = (c > 0u);
        mvs_alloc_sprite_strip(
            (int16_t)(x_top_left + (int16_t)c * 16),
            y_top_left,
            rows,
            sticky,
            strip_tiles,
            strip_pals,
            flip_bits
        );
    }
}

void mvs_fix_clear_all(void) {
    /* Space glyph (0x0020) with palette 0 is completely transparent */
    for (uint8_t col = 0u; col < 40u; ++col) {
        for (uint8_t row = 0u; row < 32u; ++row) {
            s_fix_shadow[col][row] = 0x0020u;
        }
        s_fix_dirty_col[col] = 1u;
    }
}

void mvs_fix_put(uint8_t col, uint8_t row, uint16_t s_tile_id, uint8_t fix_pal_id) {
    if (col >= 40u || row >= 32u) {
        return;
    }
    uint16_t word = (uint16_t)((((uint16_t)fix_pal_id & 0x0Fu) << 12) | (s_tile_id & 0x0FFFu));
    if (s_fix_shadow[col][row] != word) {
        s_fix_shadow[col][row] = word;
        s_fix_dirty_col[col] = 1u;
    }
}

void mvs_fix_print(uint8_t col, uint8_t row, uint8_t fix_pal_id, const char *text) {
    if (!text || row >= 32u) {
        return;
    }
    uint8_t c = col;
    while (*text && c < 40u) {
        uint8_t ch = (uint8_t)*text++;
        if (ch >= 'a' && ch <= 'z') {
            ch = (uint8_t)(ch - 32u);
        }
        if (ch < 0x20u || ch > 0x5Au) {
            ch = 0x20u;
        }
        mvs_fix_put(c++, row, ch, fix_pal_id);
    }
}

void mvs_fix_print_u32(uint8_t col, uint8_t row, uint8_t width, uint8_t fix_pal_id, uint32_t val) {
    char buf[12];
    if (width == 0u || width > 10u) {
        width = 6u;
    }
    buf[width] = '\0';
    for (int i = (int)width - 1; i >= 0; --i) {
        buf[i] = (char)('0' + (val % 10u));
        val /= 10u;
        if (val == 0u && i > 0) {
            for (int j = i - 1; j >= 0; --j) {
                buf[j] = ' ';
            }
            break;
        }
    }
    mvs_fix_print(col, row, fix_pal_id, buf);
}

void mvs_video_commit_vblank(void) {
    mvs_kick_watchdog();

    /* 1. Flush active sprite SCB1, SCB2, SCB3, SCB4 words */
    uint16_t scb2_buf[SHADOW_MAX_SPRITES];
    uint16_t scb3_buf[SHADOW_MAX_SPRITES];
    uint16_t scb4_buf[SHADOW_MAX_SPRITES];

    scb2_buf[0] = SCB2_NO_SHRINK;
    scb3_buf[0] = 0u;
    scb4_buf[0] = 0u;

    for (uint16_t i = 1u; i <= s_sprite_count; ++i) {
        const shadow_sprite_t *sp = &s_sprites[i];
        vram_write_block((uint16_t)(VRAM_SCB1_BASE + i * 64u), 1, sp->scb1, (uint16_t)(sp->height_tiles * 2u));
        scb2_buf[i] = sp->scb2;
        scb3_buf[i] = sp->scb3;
        scb4_buf[i] = sp->scb4;
    }

    if (s_sprite_count > 0u) {
        vram_write_block(VRAM_SCB2_BASE, 1, scb2_buf, (uint16_t)(s_sprite_count + 1u));
        vram_write_block(VRAM_SCB3_BASE, 1, scb3_buf, (uint16_t)(s_sprite_count + 1u));
        vram_write_block(VRAM_SCB4_BASE, 1, scb4_buf, (uint16_t)(s_sprite_count + 1u));
    }

    /* Zero height in SCB3 for any sprites retired since last frame */
    if (s_prev_sprite_count > s_sprite_count) {
        uint16_t zero = 0u;
        uint16_t max_clear = s_prev_sprite_count;
        if (max_clear > MVS_MAX_SPRITES) {
            max_clear = MVS_MAX_SPRITES;
        }
#ifndef SDD_HOST_TEST
        REG_VRAMMOD  = 1;
        REG_VRAMADDR = (uint16_t)(VRAM_SCB3_BASE + s_sprite_count + 1u);
        for (uint16_t i = (uint16_t)(s_sprite_count + 1u); i <= max_clear; ++i) {
            REG_VRAMRW = zero;
        }
#else
        for (uint16_t i = (uint16_t)(s_sprite_count + 1u); i <= max_clear; ++i) {
            g_mock_vram[VRAM_SCB3_BASE + i] = zero;
        }
#endif
    }
    s_prev_sprite_count = s_sprite_count;

    /* 2. Flush dirty FIX columns (column-major: 32 words per column) */
    for (uint8_t col = 0u; col < 40u; ++col) {
        if (s_fix_dirty_col[col]) {
            vram_write_block((uint16_t)(VRAM_FIX_BASE + (uint16_t)col * 32u), 1, s_fix_shadow[col], 32u);
            s_fix_dirty_col[col] = 0u;
        }
    }
}
