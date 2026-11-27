/*
 * Super Dig Dug — Neo Geo MVS Art & Hardware Diagnostics Viewer (Gates M0 & B0)
 * Implements Sprite Guide §6.8:
 *   - Browse all 65 families (UP/DOWN) and all 2,074 frames (LEFT/RIGHT)
 *   - Auto-play frames (BTN_C), cycle backdrop luminance (BTN_B), audition V-ROM audio (BTN_A)
 *   - Toggle 4x4 16-mask terrain occupancy test grid (BTN_D)
 *   - Live VBlank counter, P1/P2 input hex monitor, and scanline sprite-strip telemetry
 */
#include "sdd_game.h"
#include "../audio/sdd_audio.h"
#include "../platform/neogeo/neogeo_hw.h"
#include "../render/sdd_render.h"
#include "../../assets/generated/sdd_assets.h"

static uint16_t s_fam_idx    = 55u; /* Default to FAM_CHR_PLAYER_1 */
static uint16_t s_frame_off  = 0u;
static uint8_t  s_bg_mode    = 0u;
static bool     s_auto_play  = true;
static bool     s_show_masks = false;
static uint8_t  s_anim_div   = 0u;
static uint8_t  s_cue_idx    = 12u; /* AUDIO_SFX_DIG */

static const uint16_t k_bg_words[4] = {
    0x8000u, /* Reference black */
    0x0112u, /* Dark neutral slate */
    0x0445u, /* Mid neutral gray */
    0x0531u, /* Warm underground clay */
};

void sdd_art_viewer_init(void) {
    s_fam_idx    = FAM_CHR_PLAYER_1;
    s_frame_off  = 0u;
    s_bg_mode    = 1u;
    s_auto_play  = true;
    s_show_masks = false;
    s_anim_div   = 0u;
    mvs_fix_clear_all();
    sdd_audio_stop_all();
}

bool sdd_art_viewer_tick_and_render(void) {
    uint16_t pr = g_input.pressed[0];

    /* Exit back to game on START+SELECT (unless built in standalone viewer-only ROM) */
#ifndef SDD_ART_VIEWER_ONLY
    if ((g_input.held[0] & INPUT_START) && (pr & INPUT_SELECT)) {
        uint16_t blk[16];
        for (uint8_t i = 0u; i < 16u; ++i) blk[i] = 0x8000u;
        mvs_set_palette_16(PAL_BACKDROP, blk);
        mvs_fix_clear_all();
        return true;
    }
#endif

    if (pr & INPUT_UP) {
        s_fam_idx   = (s_fam_idx == 0u) ? (SDD_ASSET_FAMILY_COUNT - 1u) : (uint16_t)(s_fam_idx - 1u);
        s_frame_off = 0u;
    }
    if (pr & INPUT_DOWN) {
        s_fam_idx   = (uint16_t)((s_fam_idx + 1u) % SDD_ASSET_FAMILY_COUNT);
        s_frame_off = 0u;
    }

    const sdd_family_desc_t *fam = &sdd_families[s_fam_idx];
    if (pr & INPUT_LEFT) {
        s_frame_off = (s_frame_off == 0u) ? (uint16_t)(fam->frame_count - 1u) : (uint16_t)(s_frame_off - 1u);
        s_auto_play = false;
    }
    if (pr & INPUT_RIGHT) {
        s_frame_off = (uint16_t)((s_frame_off + 1u) % fam->frame_count);
        s_auto_play = false;
    }
    if (pr & INPUT_BTN_C) {
        s_auto_play = !s_auto_play;
    }
    if (pr & INPUT_BTN_B) {
        s_bg_mode = (uint8_t)((s_bg_mode + 1u) & 3u);
        uint16_t bg_pal[16];
        for (uint8_t i = 0u; i < 15u; ++i) bg_pal[i] = 0x8000u;
        bg_pal[15] = k_bg_words[s_bg_mode];
#ifndef SDD_HOST_TEST
        MVS_PALETTE_RAM[255u * 16u + 15u] = bg_pal[15];
#else
        g_mock_palette_ram[255u * 16u + 15u] = bg_pal[15];
#endif
    }
    if (pr & INPUT_BTN_D) {
        s_show_masks = !s_show_masks;
    }
    if (pr & INPUT_BTN_A) {
        sdd_audio_play_cue((sdd_audio_cue_id_t)s_cue_idx);
        s_cue_idx = (uint8_t)((s_cue_idx + 1u) % SDD_AUDIO_CUE_COUNT);
    }

    if (s_auto_play && fam->frame_count > 1u) {
        if (++s_anim_div >= 8u) {
            s_anim_div  = 0u;
            s_frame_off = (uint16_t)((s_frame_off + 1u) % fam->frame_count);
        }
    }

    uint16_t g_idx = (uint16_t)(fam->first_frame + s_frame_off);
    const sdd_frame_desc_t *fr = &sdd_frames[g_idx];

    mvs_sprites_begin();

    /* Draw selected sprite centered in left showcase viewport (anchor x=112, y=112) */
    sdd_render_draw_frame_desc(g_idx, 112, 112, fam->palette_id, false);

    /* Optional 4x4 16-mask terrain occupancy matrix test (x=24..88, y=144..208) */
    if (s_show_masks) {
        uint16_t occ0 = (uint16_t)(sdd_families[FAM_TILE_TOPSOIL].first_frame + 6u);
        for (uint8_t m = 0u; m < 16u; ++m) {
            int16_t gx = (int16_t)(24 + (m & 3u) * 18);
            int16_t gy = (int16_t)(144 + (m >> 2u) * 18);
            mvs_draw_meta_sprite(
                gx,
                gy,
                1u,
                1u,
                sdd_frames[occ0 + m].c_tile_base,
                PAL_DD1982_STRATUM_0,
                false,
                false
            );
        }
    }

    /* FIX Overlay Diagnostics */
    mvs_fix_print(2u, 3u, PAL_FIX_GOLD, "SUPER DIG DUG M0/B0 ART VIEWER");
    mvs_fix_print(2u, 5u, PAL_FIX_P1,   "FAMILY:");
    mvs_fix_print(10u, 5u, PAL_FIX_TEXT, "                        ");
    mvs_fix_print(10u, 5u, PAL_FIX_TEXT, fam->id);

    mvs_fix_print(2u, 7u,  PAL_FIX_GOLD, "FAM IDX:");
    mvs_fix_print_u32(11u, 7u, 3u, PAL_FIX_TEXT, s_fam_idx);
    mvs_fix_print(16u, 7u, PAL_FIX_GOLD, "FRAME:");
    mvs_fix_print_u32(23u, 7u, 3u, PAL_FIX_TEXT, s_frame_off);
    mvs_fix_put(26u, 7u, '/', PAL_FIX_TEXT);
    mvs_fix_print_u32(27u, 7u, 3u, PAL_FIX_TEXT, fam->frame_count);

    mvs_fix_print(2u, 9u, PAL_FIX_GOLD, "CANVAS :");
    mvs_fix_print_u32(11u, 9u, 3u, PAL_FIX_TEXT, fr->width);
    mvs_fix_put(14u, 9u, 'X', PAL_FIX_TEXT);
    mvs_fix_print_u32(15u, 9u, 3u, PAL_FIX_TEXT, fr->height);
    mvs_fix_print(20u, 9u, PAL_FIX_GOLD, "PAL:");
    mvs_fix_print_u32(25u, 9u, 3u, PAL_FIX_TEXT, fam->palette_id);

    mvs_fix_print(2u, 23u, PAL_FIX_P2,   "A:SFX  B:BG  C:PLAY  D:16-MASK");
    mvs_fix_print(2u, 25u, PAL_FIX_GOLD, "VBLANK :");
    mvs_fix_print_u32(11u, 25u, 8u, PAL_FIX_TEXT, g_vblank_counter);
    mvs_fix_print(21u, 25u, PAL_FIX_GOLD, "STRIPS:");
    mvs_fix_print_u32(29u, 25u, 2u, PAL_FIX_TEXT, g_frame_stats.worst_scanline_strips);

    mvs_fix_print(2u, 27u, PAL_FIX_GOLD, "INPUT  :");
    mvs_fix_print_u32(11u, 27u, 5u, PAL_FIX_TEXT, g_input.held[0]);
    mvs_fix_print(18u, 27u, PAL_FIX_GOLD, "CUE:");
    mvs_fix_print_u32(23u, 27u, 2u, PAL_FIX_TEXT, s_cue_idx);

    return false;
}
