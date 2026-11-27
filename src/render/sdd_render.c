/*
 * Super Dig Dug — Neo Geo MVS Playfield Strip, Actor Meta-Sprite & Side-HUD FIX Renderer
 * Confirmed Screen Layout:
 *   - Left/Center Playfield: 224x224 px (x=0..223) rendered via 14 vertical 16x224 sprite strips
 *   - Right-Hand Side HUD:   96x224 px (x=224..319, FIX cols 28..39, rows 2..29, 0 sprite strips!)
 */
#include "sdd_render.h"
#include "../actors/sdd_actors.h"
#include "../platform/neogeo/neogeo_hw.h"
#include "../score/sdd_score.h"
#include "../world/sdd_world.h"
#include "../../assets/generated/sdd_assets.h"

void sdd_render_draw_frame_desc(
    uint16_t global_frame_idx,
    int16_t anchor_x,
    int16_t anchor_y,
    uint8_t pal_override,
    bool hflip
) {
    if (global_frame_idx >= SDD_ASSET_FRAME_COUNT) {
        return;
    }
    const sdd_frame_desc_t *fr = &sdd_frames[global_frame_idx];
    int16_t tl_x = (int16_t)(anchor_x - (int16_t)fr->pivot_x);
    int16_t tl_y = (int16_t)(anchor_y - (int16_t)fr->pivot_y);
    mvs_draw_meta_sprite(tl_x, tl_y, fr->cols, fr->rows, fr->c_tile_base, pal_override, hflip, false);
}

void sdd_render_draw_side_hud(
    uint32_t p1_score,
    uint32_t p2_score,
    uint8_t  active_player,
    bool     two_player_game,
    uint8_t  lives_remaining,
    uint16_t round_num,
    uint8_t  credits
) {
    /* Vertical divider column 28 and clean 11-column HUD panel (cols 29..39) */
    for (uint8_t r = FIX_VISIBLE_ROW_TOP; r <= FIX_VISIBLE_ROW_BOT; ++r) {
        mvs_fix_put(SIDE_HUD_FIX_COL_MIN, r, '|', PAL_FIX_GOLD);
    }

    mvs_fix_print(29u, 3u,  PAL_FIX_DANGER, "HIGH SCORE");
    mvs_fix_print_u32(31u, 4u, 8u, PAL_FIX_TEXT, g_high_score);

    mvs_fix_print(29u, 6u, (active_player == 0u) ? PAL_FIX_P1 : PAL_FIX_TEXT, "   1UP    ");
    mvs_fix_print_u32(31u, 7u, 8u, PAL_FIX_TEXT, p1_score);

    if (two_player_game) {
        mvs_fix_print(29u, 9u, (active_player == 1u) ? PAL_FIX_P2 : PAL_FIX_TEXT, "   2UP    ");
        mvs_fix_print_u32(31u, 10u, 8u, PAL_FIX_TEXT, p2_score);
    } else {
        mvs_fix_print(29u, 9u,  PAL_FIX_TEXT, "          ");
        mvs_fix_print(29u, 10u, PAL_FIX_TEXT, "          ");
    }

    /* Lives row using native 8x8 S-ROM life_helmet_8x8 icon from ui_hud */
    mvs_fix_print(29u, 13u, PAL_FIX_GOLD, "LIVES");
    uint16_t hud_base = sdd_families[FAM_UI_HUD].first_frame;
    int16_t  helm_s   = sdd_frames[hud_base + 11u].s_tile_id; /* 11:life_helmet_8x8 */
    uint16_t helm_tid = (helm_s >= 0) ? (uint16_t)helm_s : (uint16_t)'*';
    for (uint8_t i = 0u; i < 6u; ++i) {
        if (i < lives_remaining) {
            mvs_fix_put((uint8_t)(29u + i), 14u, helm_tid, PAL_FIX_UI_HUD);
        } else {
            mvs_fix_put((uint8_t)(29u + i), 14u, ' ', PAL_FIX_TEXT);
        }
    }

    /* Round counter & flower markers */
    mvs_fix_print(29u, 17u, PAL_FIX_GOLD, "ROUND");
    mvs_fix_print_u32(35u, 17u, 3u, PAL_FIX_TEXT, round_num);

    uint16_t rew_base = sdd_families[FAM_PICK_REWARDS].first_frame;
    int16_t  flw_s    = sdd_frames[rew_base + 9u].s_tile_id; /* 9:hud_8x8 */
    uint16_t flw_tid  = (flw_s >= 0) ? (uint16_t)flw_s : (uint16_t)'+';
    uint8_t  flowers  = (round_num > 10u) ? 10u : (uint8_t)round_num;
    for (uint8_t i = 0u; i < 10u; ++i) {
        mvs_fix_put((uint8_t)(29u + i), 19u, (i < flowers) ? flw_tid : ' ', PAL_FIX_P2);
    }

    /* Phase 2 Equipment Reserve Panel (cleanly framed & ready for M2-M9 expansion) */
    mvs_fix_print(29u, 22u, PAL_FIX_P1,   "PUMP: STD ");
    mvs_fix_print(29u, 24u, PAL_FIX_TEXT, "MODE: 1982");

    mvs_fix_print(29u, 27u, PAL_FIX_GOLD, "CREDIT");
    mvs_fix_print_u32(36u, 27u, 2u, PAL_FIX_TEXT, credits);
}

void sdd_render_playfield_and_actors(void) {
    uint16_t top_first = sdd_families[FAM_TILE_TOPSOIL].first_frame;
    uint16_t occ_base  = (uint16_t)(top_first + 6u); /* occupancy_v1_00..0f */
    uint16_t surf_trim = sdd_frames[top_first + 3u].c_tile_base; /* green_grass_surface_cap */

    /* 1. 14 vertical 16x224 background terrain sprite strips (x = 0..223) */
    for (uint8_t tx = 0u; tx < WORLD_TILES_W; ++tx) {
        uint16_t col_tiles[WORLD_TILES_H];
        uint8_t  col_pals[WORLD_TILES_H];

        for (uint8_t ty = 0u; ty < WORLD_TILES_H; ++ty) {
            uint8_t mask = g_world.tile_mask[ty][tx];
            if (ty == 0u) {
                /* Surface row: completely open sky; draw subtle grass trim above intact column 1 dirt */
                if (g_world.tile_mask[1][tx] == QUAD_FULL && tx != 6u && tx != 0u) {
                    col_tiles[ty] = surf_trim;
                    col_pals[ty]  = PAL_DD1982_SURFACE;
                } else {
                    col_tiles[ty] = 0u; /* Blank transparent tile 0 */
                    col_pals[ty]  = PAL_FIX_TEXT;
                }
            } else {
                col_tiles[ty] = sdd_frames[occ_base + (mask & 0x0Fu)].c_tile_base;
                col_pals[ty]  = sdd_world_palette_for_tile_row(ty);
            }
        }

        mvs_alloc_sprite_strip(
            (int16_t)((int16_t)tx * 16),
            0,
            WORLD_TILES_H,
            (tx > 0u),
            col_tiles,
            col_pals,
            0u
        );
    }

    /* 2. Bonus Vegetable in central chamber */
    if (g_veggie.active) {
        uint16_t r_first = sdd_families[FAM_PICK_REWARDS].first_frame;
        sdd_render_draw_frame_desc(
            (uint16_t)(r_first + g_veggie.reward_frame_idx),
            (int16_t)(g_veggie.px + 8),
            (int16_t)(g_veggie.py + 8),
            PAL_PICK_REWARDS,
            false
        );
    }

    /* 3. Harpoon & Pump Tether */
    if (g_player.harpoon.extending || g_player.harpoon.latched) {
        uint16_t fp_first = sdd_families[FAM_FX_PUMP].first_frame;
        int16_t px = (int16_t)(g_player.x_fp >> FP_SHIFT);
        int16_t py = (int16_t)(g_player.y_fp >> FP_SHIFT);
        int16_t len = g_player.harpoon.latched ? 16 : g_player.harpoon.length_px;
        sdd_dir_t d = g_player.harpoon.dir;

        int16_t hx = (int16_t)(px + 8);
        int16_t hy = (int16_t)(py + 8);
        uint16_t f_off = 2u; /* harpoon_endpoint_right */
        bool hflip = false;

        if (d == DIR_RIGHT) { hx = (int16_t)(px + 8 + len); f_off = 2u; }
        if (d == DIR_LEFT)  { hx = (int16_t)(px + 8 - len); f_off = 2u; hflip = true; }
        if (d == DIR_UP)    { hy = (int16_t)(py + 8 - len); f_off = 3u; }
        if (d == DIR_DOWN)  { hy = (int16_t)(py + 8 + len); f_off = 1u; }

        sdd_render_draw_frame_desc((uint16_t)(fp_first + f_off), hx, hy, PAL_FX_PUMP, hflip);
    }

    /* 4. Enemies (Pooka & Fygar + Fygar Horizontal Flame) */
    uint16_t pooka_base = sdd_families[FAM_ENM_POOKA].first_frame;
    uint16_t fygar_base = sdd_families[FAM_ENM_FYGAR].first_frame;
    uint16_t atk_base   = sdd_families[FAM_FX_ENEMY_ATTACKS].first_frame;

    for (uint8_t i = 0u; i < MAX_ENEMIES; ++i) {
        const sdd_enemy_t *e = &g_enemies[i];
        if (!e->active || e->state == ENM_STATE_DEAD || e->state == ENM_STATE_ESCAPED) {
            continue;
        }
        int16_t cx = (int16_t)((e->x_fp >> FP_SHIFT) + 8);
        int16_t cy = (int16_t)((e->y_fp >> FP_SHIFT) + 8);
        bool is_fygar = (e->kind == ENEMY_KIND_FYGAR);
        uint16_t base = is_fygar ? fygar_base : pooka_base;
        uint8_t  pal  = is_fygar ? PAL_ENM_FYGAR : PAL_ENM_POOKA;
        uint16_t rel  = (uint16_t)(25u + ((e->anim_tick >> 2) & 3u)); /* walk_right_01..04 */
        bool     hflip = (e->horiz_facing == DIR_LEFT);

        if (e->state == ENM_STATE_GHOST) {
            rel = is_fygar ? 49u : 41u; /* phase_eyes */
        } else if (e->state == ENM_STATE_ROCK_HELD) {
            rel = 17u; /* flattened_crushed */
        } else if (e->state == ENM_STATE_POPPING) {
            rel = 22u; /* pop_01 */
        } else if (e->state == ENM_STATE_INFLATED) {
            uint8_t st = e->inflate_stage;
            if (st < 1u) st = 1u;
            if (st > 3u) st = 3u;
            rel = (uint16_t)(10u + st); /* 11..13 inflated poses (48x48 canvas) */
        } else if (is_fygar && e->state == ENM_STATE_INHALE) {
            rel = (uint16_t)(41u + ((e->anim_tick >> 1) & 1u));
        } else if (is_fygar && e->state == ENM_STATE_FIRE) {
            rel = 44u;
            /* Draw horizontal flame segments */
            int16_t step_sign = (e->horiz_facing == DIR_RIGHT) ? 16 : -16;
            for (uint8_t seg = 1u; seg <= 2u; ++seg) {
                sdd_render_draw_frame_desc(
                    (uint16_t)(atk_base + (seg == 1u ? 1u : 2u)),
                    (int16_t)(cx + step_sign * (int16_t)seg),
                    cy,
                    PAL_FX_ENEMY_ATTACKS,
                    hflip
                );
            }
        } else if (e->dir == DIR_UP) {
            rel   = (uint16_t)(29u + ((e->anim_tick >> 2) & 3u));
            hflip = false;
        } else if (e->dir == DIR_DOWN) {
            rel   = (uint16_t)(33u + ((e->anim_tick >> 2) & 3u));
            hflip = false;
        }

        sdd_render_draw_frame_desc((uint16_t)(base + rel), cx, cy, pal, hflip);
    }

    /* 5. Rocks */
    uint16_t rock_base = sdd_families[FAM_PROP_ROCKS].first_frame;
    for (uint8_t r = 0u; r < MAX_ROCKS; ++r) {
        const sdd_rock_t *rk = &g_rocks[r];
        if (!rk->active || rk->state == ROCK_RETIRED) {
            continue;
        }
        int16_t rx = (int16_t)((rk->x_fp >> FP_SHIFT) + 8);
        int16_t ry = (int16_t)((rk->y_fp >> FP_SHIFT) + 8);
        uint16_t rel = 0u;
        if (rk->state == ROCK_WOBBLE) {
            rel = (uint16_t)(6u + ((rk->state_timer >> 2) & 1u));
        } else if (rk->state == ROCK_FALLING) {
            rel = 9u;
        } else if (rk->state == ROCK_SHATTER) {
            rel = 11u;
        }
        sdd_render_draw_frame_desc((uint16_t)(rock_base + rel), rx, ry, PAL_PROP_ROCKS, false);
    }

    /* 6. Player Taizo (chr_player_1) */
    if (g_player.state != PLAYER_DEAD) {
        uint16_t p1_base = sdd_families[FAM_CHR_PLAYER_1].first_frame;
        int16_t px = (int16_t)((g_player.x_fp >> FP_SHIFT) + 8);
        int16_t py = (int16_t)((g_player.y_fp >> FP_SHIFT) + 8);
        uint16_t rel = 27u; /* idle_01 */
        uint8_t step4 = (uint8_t)((g_player.anim_tick >> 2) & 3u);

        if (g_player.state == PLAYER_DYING || g_player.state == PLAYER_CRUSHED) {
            rel = (uint16_t)(73u + ((g_player.state_timer >> 3) & 3u));
        } else if (g_player.state == PLAYER_PUMPING) {
            if (g_player.dir == DIR_RIGHT) rel = 49u;
            if (g_player.dir == DIR_LEFT)  rel = 56u;
            if (g_player.dir == DIR_UP)    rel = 63u;
            if (g_player.dir == DIR_DOWN)  rel = 70u;
        } else if (g_player.digging) {
            if (g_player.dir == DIR_RIGHT) rel = (uint16_t)(45u + step4);
            if (g_player.dir == DIR_LEFT)  rel = (uint16_t)(52u + step4);
            if (g_player.dir == DIR_UP)    rel = (uint16_t)(59u + step4);
            if (g_player.dir == DIR_DOWN)  rel = (uint16_t)(66u + step4);
        } else if (g_player.moving) {
            if (g_player.dir == DIR_RIGHT) rel = (uint16_t)(29u + step4);
            if (g_player.dir == DIR_UP)    rel = (uint16_t)(33u + step4);
            if (g_player.dir == DIR_DOWN)  rel = (uint16_t)(37u + step4);
            if (g_player.dir == DIR_LEFT)  rel = (uint16_t)(41u + step4);
        }

        sdd_render_draw_frame_desc((uint16_t)(p1_base + rel), px, py, PAL_CHR_PLAYER_1, false);
    }
}
