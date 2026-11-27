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
uint8_t  g_mock_credits = 0u;
/* Provided by crt0_mvs.S on the target */
volatile uint8_t g_bios_start_req = 0u;
volatile uint8_t g_start_accept   = 0u;
volatile uint8_t g_coin_sound_cmd = 0u;
#endif

/* Shadow buffers in 68000 work RAM (flushed during VBlank).
 *
 * Hardware sprites 1..MVS_BG_COLUMNS form a persistent background layer whose
 * tile maps are rewritten only for columns marked dirty. Per-frame (dynamic)
 * strips follow at hardware sprite MVS_BG_COLUMNS + 1 and draw above it.
 */
#define SHADOW_MAX_SPRITES 160u
#define DYN_SPRITE_BASE    MVS_BG_COLUMNS

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

static uint16_t        s_bg_scb1[MVS_BG_COLUMNS][MVS_BG_MAX_TILES * 2u];
static uint16_t        s_bg_dirty = 0u;       /* bit n = column n needs its SCB1 rewritten */
static uint8_t         s_bg_height = 0u;
static bool            s_bg_visible = false;
static bool            s_bg_ctrl_dirty = true; /* SCB2..SCB4 of the layer need rewriting */

static int8_t          s_strip_delta[MVS_SCREEN_H + 1];
static uint32_t        s_last_frame = 0u;

volatile uint32_t g_missed_frames = 0u;
uint16_t          g_fix_generation = 0u;
#ifdef SDD_HOST_TEST
bool              g_frame_stats_enabled = true;
static uint16_t   s_mock_vram_cursor = 0u;
static int16_t    s_mock_vram_mod = 1;
#else
bool              g_frame_stats_enabled = false;
#endif

static inline void vram_begin(uint16_t addr, int16_t mod) {
#ifndef SDD_HOST_TEST
    REG_VRAMMOD  = mod;
    REG_VRAMADDR = addr;
#else
    s_mock_vram_cursor = addr;
    s_mock_vram_mod    = mod;
#endif
}

static inline void vram_put(uint16_t word) {
#ifndef SDD_HOST_TEST
    REG_VRAMRW = word;
#else
    if (s_mock_vram_cursor < 0x8800u) {
        g_mock_vram[s_mock_vram_cursor] = word;
    }
    s_mock_vram_cursor = (uint16_t)(s_mock_vram_cursor + (uint16_t)s_mock_vram_mod);
#endif
}

static void vram_write_block(uint16_t addr, int16_t mod, const uint16_t *words, uint16_t count) {
    vram_begin(addr, mod);
    for (uint16_t i = 0u; i < count; ++i) {
        vram_put(words[i]);
    }
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
    s_prev_sprite_count = (uint16_t)(MVS_MAX_SPRITES - DYN_SPRITE_BASE);
    s_bg_visible = false;
    s_bg_ctrl_dirty = true;
    s_bg_dirty = 0u;
    mvs_video_commit_vblank();
    s_last_frame = g_vblank_counter;
}

void mvs_wait_vblank(void) {
#ifndef SDD_HOST_TEST
    uint32_t now = g_vblank_counter;
    if (now != s_last_frame) {
        /* The tick overran one or more VBlanks: record it, then resynchronise
         * on the next one so VRAM commits stay inside vertical blanking. */
        g_missed_frames += (now - s_last_frame);
    }
    while (g_vblank_counter == now) {
        mvs_kick_watchdog();
    }
    s_last_frame = g_vblank_counter;
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

/* Sound commands are queued and released one per VBlank: each write to
 * REG_SOUND raises a Z80 NMI, and a second write before the driver has read
 * the latch would overwrite the first command. */
#define SND_FIFO_SIZE 32u
static uint8_t s_snd_fifo[SND_FIFO_SIZE];
static uint8_t s_snd_head = 0u;
static uint8_t s_snd_tail = 0u;

void mvs_snd_send(uint8_t cmd) {
#ifdef SDD_HOST_TEST
    g_mock_last_sound_cmd = cmd;
#endif
    uint8_t next = (uint8_t)((s_snd_head + 1u) % SND_FIFO_SIZE);
    if (next == s_snd_tail) {
        return; /* queue full: drop the newest command */
    }
    s_snd_fifo[s_snd_head] = cmd;
    s_snd_head = next;
}

void mvs_snd_pump(void) {
    if (s_snd_tail == s_snd_head) {
        return;
    }
#ifndef SDD_HOST_TEST
    REG_SOUND = s_snd_fifo[s_snd_tail];
#endif
    s_snd_tail = (uint8_t)((s_snd_tail + 1u) % SND_FIFO_SIZE);
}

uint8_t mvs_credits(void) {
#ifndef SDD_HOST_TEST
    uint8_t bcd = BRAM_P1_CREDITS_BCD;
    return (uint8_t)((bcd >> 4) * 10u + (bcd & 0x0Fu));
#else
    return g_mock_credits;
#endif
}

void mvs_set_start_accept(bool accept) {
    g_start_accept = accept ? 1u : 0u;
}

uint8_t mvs_take_start_request(void) {
#ifdef SDD_HOST_TEST
    /* No BIOS on the host: derive the request from the start buttons. */
    if (g_start_accept) {
        if (g_input.pressed[1] & INPUT_START) {
            g_bios_start_req = MVS_START_P1 | MVS_START_P2;
        } else if (g_input.pressed[0] & INPUT_START) {
            g_bios_start_req = MVS_START_P1;
        }
    }
#endif
    uint8_t req = g_bios_start_req;
    if (req != 0u) {
        g_bios_start_req = 0u;
        g_start_accept   = 0u;
    }
    return req;
}

void mvs_set_in_game(bool in_game) {
#ifndef SDD_HOST_TEST
    BIOS_USER_MODE = in_game ? BIOS_USER_MODE_GAME : BIOS_USER_MODE_DEMO;
#else
    (void)in_game;
#endif
}

static void crash_put_hex(uint8_t col, uint8_t row, uint32_t value, uint8_t digits) {
    for (uint8_t i = 0u; i < digits; ++i) {
        uint8_t nib = (uint8_t)((value >> ((uint32_t)(digits - 1u - i) * 4u)) & 0x0Fu);
        mvs_fix_put((uint8_t)(col + i), row, (uint16_t)(nib < 10u ? (uint8_t)('0' + nib) : (uint8_t)('A' + nib - 10u)), PAL_FIX_TEXT);
    }
}

/* Fatal CPU exception: print the cause on the FIX layer; crt0 then idles. */
void sdd_crash_report(uint32_t vector, const uint16_t *frame) {
    /* Bus and address errors push a 14-byte frame; the rest push SR + PC. */
    const uint16_t *srpc = (vector == 2u || vector == 3u) ? frame + 4 : frame;
    uint32_t pc = ((uint32_t)srpc[1] << 16) | srpc[2];

    mvs_load_palettes(sdd_palettes);
    mvs_fix_clear_all();
    s_sprite_count = 0u;
    s_prev_sprite_count = (uint16_t)(MVS_MAX_SPRITES - DYN_SPRITE_BASE);
    mvs_bg_show(false);
    mvs_fix_print(4u, 10u, PAL_FIX_DANGER, "CPU EXCEPTION");
    mvs_fix_print(4u, 12u, PAL_FIX_GOLD, "VECTOR");
    crash_put_hex(12u, 12u, vector, 2u);
    mvs_fix_print(4u, 14u, PAL_FIX_GOLD, "PC");
    crash_put_hex(12u, 14u, pc, 8u);
    mvs_fix_print(4u, 16u, PAL_FIX_GOLD, "SR");
    crash_put_hex(12u, 16u, srpc[0], 4u);
    if (vector == 2u || vector == 3u) {
        mvs_fix_print(4u, 18u, PAL_FIX_GOLD, "ADDR");
        crash_put_hex(12u, 18u, ((uint32_t)frame[1] << 16) | frame[2], 8u);
    }
    mvs_video_commit_vblank();
}

void mvs_sprites_begin(void) {
    s_sprite_count = 0u;
    if (g_frame_stats_enabled) {
        for (uint16_t y = 0u; y <= MVS_SCREEN_H; ++y) {
            s_strip_delta[y] = 0;
        }
    }
}

/* Resolve the per-scanline strip counts gathered since mvs_sprites_begin().
 * Only meaningful while g_frame_stats_enabled is set (viewer, host tests). */
void mvs_frame_stats_update(void) {
    int16_t  acc = 0;
    uint8_t  worst = 0u;
    uint16_t bg_lines = s_bg_visible ? (uint16_t)(s_bg_height * 16u) : 0u;
    for (uint16_t y = 0u; y < MVS_SCREEN_H; ++y) {
        acc = (int16_t)(acc + s_strip_delta[y]);
        uint8_t n = (uint8_t)(acc + ((y < bg_lines) ? (int16_t)MVS_BG_COLUMNS : 0));
        g_frame_stats.scanline_strips[y] = n;
        if (n > worst) {
            worst = n;
        }
    }
    g_frame_stats.worst_scanline_strips = worst;
    g_frame_stats.sprites_used = (uint16_t)(s_sprite_count + (s_bg_visible ? MVS_BG_COLUMNS : 0u));
}

void mvs_bg_set_column(uint8_t col, const uint16_t *c_tiles, const uint8_t *palettes, uint8_t height_tiles) {
    if (col >= MVS_BG_COLUMNS) {
        return;
    }
    if (height_tiles > MVS_BG_MAX_TILES) {
        height_tiles = MVS_BG_MAX_TILES;
    }
    uint16_t *dst = s_bg_scb1[col];
    for (uint8_t t = 0u; t < height_tiles; ++t) {
        *dst++ = c_tiles[t];
        *dst++ = (uint16_t)((uint16_t)palettes[t] << 8);
    }
    if (s_bg_height != height_tiles) {
        s_bg_height = height_tiles;
        s_bg_ctrl_dirty = true;
    }
    s_bg_dirty |= (uint16_t)(1u << col);
}

void mvs_bg_show(bool visible) {
    if (s_bg_visible != visible) {
        s_bg_visible = visible;
        s_bg_ctrl_dirty = true;
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
    /* Slot 0 is unused; dynamic strip n maps to hardware sprite DYN_SPRITE_BASE + n */
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

    if (g_frame_stats_enabled) {
        int16_t y0 = y < 0 ? 0 : y;
        int16_t y1 = (int16_t)(y + (int16_t)height_tiles * 16);
        if (y1 > MVS_SCREEN_H) {
            y1 = MVS_SCREEN_H;
        }
        if (y0 < y1) {
            ++s_strip_delta[y0];
            --s_strip_delta[y1];
        }
    }
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
    ++g_fix_generation;
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
    mvs_snd_pump();

    /* 1. Background layer: tile maps of dirty columns, then its control words */
    if (s_bg_dirty != 0u) {
        for (uint8_t col = 0u; col < MVS_BG_COLUMNS; ++col) {
            if (s_bg_dirty & (uint16_t)(1u << col)) {
                vram_write_block(
                    (uint16_t)(VRAM_SCB1_BASE + (uint16_t)(1u + col) * 64u), 1,
                    s_bg_scb1[col], (uint16_t)(s_bg_height * 2u)
                );
            }
        }
        s_bg_dirty = 0u;
    }
    if (s_bg_ctrl_dirty) {
        uint16_t scb3 = s_bg_visible ? (uint16_t)(((496u & 0x01FFu) << 7) | (s_bg_height & 0x3Fu)) : 0u;
        vram_begin((uint16_t)(VRAM_SCB2_BASE + 1u), 1);
        for (uint8_t col = 0u; col < MVS_BG_COLUMNS; ++col) {
            vram_put(SCB2_NO_SHRINK);
        }
        vram_begin((uint16_t)(VRAM_SCB3_BASE + 1u), 1);
        for (uint8_t col = 0u; col < MVS_BG_COLUMNS; ++col) {
            vram_put((s_bg_visible && col > 0u) ? (uint16_t)(scb3 | 0x0040u) : scb3);
        }
        vram_begin((uint16_t)(VRAM_SCB4_BASE + 1u), 1);
        for (uint8_t col = 0u; col < MVS_BG_COLUMNS; ++col) {
            vram_put((uint16_t)(((uint16_t)col * 16u) << 7));
        }
        s_bg_ctrl_dirty = false;
    }

    /* 2. Dynamic strips: SCB1 tile maps, then SCB2..SCB4 as three runs */
    for (uint16_t i = 1u; i <= s_sprite_count; ++i) {
        const shadow_sprite_t *sp = &s_sprites[i];
        vram_write_block(
            (uint16_t)(VRAM_SCB1_BASE + (DYN_SPRITE_BASE + i) * 64u), 1,
            sp->scb1, (uint16_t)(sp->height_tiles * 2u)
        );
    }
    if (s_sprite_count > 0u) {
        vram_begin((uint16_t)(VRAM_SCB2_BASE + DYN_SPRITE_BASE + 1u), 1);
        for (uint16_t i = 1u; i <= s_sprite_count; ++i) {
            vram_put(s_sprites[i].scb2);
        }
        vram_begin((uint16_t)(VRAM_SCB3_BASE + DYN_SPRITE_BASE + 1u), 1);
        for (uint16_t i = 1u; i <= s_sprite_count; ++i) {
            vram_put(s_sprites[i].scb3);
        }
        vram_begin((uint16_t)(VRAM_SCB4_BASE + DYN_SPRITE_BASE + 1u), 1);
        for (uint16_t i = 1u; i <= s_sprite_count; ++i) {
            vram_put(s_sprites[i].scb4);
        }
    }

    /* Zero the height of dynamic strips retired since the previous frame */
    if (s_prev_sprite_count > s_sprite_count) {
        vram_begin((uint16_t)(VRAM_SCB3_BASE + DYN_SPRITE_BASE + s_sprite_count + 1u), 1);
        for (uint16_t i = s_sprite_count; i < s_prev_sprite_count; ++i) {
            vram_put(0u);
        }
    }
    s_prev_sprite_count = s_sprite_count;

    /* 3. Dirty FIX columns (column-major: 32 words per column) */
    for (uint8_t col = 0u; col < 40u; ++col) {
        if (s_fix_dirty_col[col]) {
            vram_write_block((uint16_t)(VRAM_FIX_BASE + (uint16_t)col * 32u), 1, s_fix_shadow[col], 32u);
            s_fix_dirty_col[col] = 0u;
        }
    }
}
