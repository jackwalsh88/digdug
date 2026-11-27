/*
 * Native Host C99 Unit Test Suite for Phase 1 (1982 Dig Dug Replica on Neo Geo MVS)
 * Automatically compiled & executed by `tools/sdd.py test` when `gcc` or `clang` is present.
 */
#include <assert.h>
#include <stdio.h>
#include "../src/actors/sdd_actors.h"
#include "../src/audio/sdd_audio.h"
#include "../src/game/sdd_game.h"
#include "../src/platform/neogeo/neogeo_hw.h"
#include "../src/render/sdd_render.h"
#include "../src/score/sdd_score.h"
#include "../src/world/sdd_world.h"
#include "../assets/generated/sdd_assets.h"

int main(void) {
    mvs_hw_init();
    sdd_game_init(false);

    /* 1. Verify palette index 0 transparency ($8000) across all 256 palettes */
    for (int p = 0; p < 256; ++p) {
        assert(g_mock_palette_ram[p * 16] == 0x8000u);
    }

    /* 2. Verify Round 1 init, quadrant masks, and +10pt digging */
    sdd_round_def_t def;
    sdd_world_init_round(1u, &def);
    sdd_actors_spawn_round(&def);
    assert(def.enemy_count == 4u);
    assert(def.rock_count == 3u);
    /* Round 1 as stored in the 1982 ROM: two 5-cell vertical and two 4-cell
     * horizontal tunnels, 3 Pookas + 1 Fygar (bottom-left), 3 rocks. */
    assert(def.tunnel_count == 4u);
    assert(def.enemies[0].kind == ENEMY_KIND_POOKA && def.enemies[0].tx == 1u && def.enemies[0].ty == 2u);
    assert(def.enemies[3].kind == ENEMY_KIND_FYGAR && def.enemies[3].tx == 3u && def.enemies[3].ty == 10u);
    assert(sdd_world_tile_is_open(1, 2) && sdd_world_tile_is_open(1, 6));   /* top-left vertical */
    assert(sdd_world_tile_is_open(9, 2) && sdd_world_tile_is_open(12, 2));  /* top-right horizontal */
    assert(sdd_world_tile_is_open(2, 10) && sdd_world_tile_is_open(5, 10)); /* bottom-left horizontal */
    assert(sdd_world_tile_is_open(9, 9) && sdd_world_tile_is_open(9, 13));  /* bottom-right vertical */
    assert(!sdd_world_tile_is_open(4, 3));                                  /* rock sits in dirt */
    assert(sdd_world_tile_is_open(6, 0) && sdd_world_tile_is_open(5, 7) && sdd_world_tile_is_open(7, 7));
    /* Layout selection: round n for 1..15, then 12..15 repeating */
    assert(sdd_world_layout_index(1u) == 0u && sdd_world_layout_index(15u) == 14u);
    assert(sdd_world_layout_index(16u) == 11u && sdd_world_layout_index(19u) == 14u);
    assert(sdd_world_layout_index(20u) == 11u);
    /* Strata are 3/4/4/2 rows below the surface lane */
    assert(sdd_world_stratum_for_y(16 * 3) == 0u && sdd_world_stratum_for_y(16 * 4) == 1u);
    assert(sdd_world_stratum_for_y(16 * 11) == 2u && sdd_world_stratum_for_y(16 * 12) == 3u);
    assert(g_world.tile_mask[0][0] == 0x00u); /* Surface row open */
    assert(g_world.tile_mask[1][0] == 0x0Fu); /* Undug stratum 0 tile solid */

    uint32_t dig_pts = 0u;
    for (int t = 0; t < 24; ++t) {
        dig_pts += sdd_player_step(INPUT_DOWN, 0u);
    }
    assert(dig_pts >= 20u);
    /* The first 2 px are still inside the chamber (walk rate); after that
     * digging advances one 2-pixel step every 4 ticks (rate $40): 14 px in 24 ticks. */
    assert((g_player.y_fp >> FP_SHIFT) == PLAYER_SPAWN_PX_Y + 14);

    /* A round-1 Pooka (rate 124, updated every other frame) covers 2 * 124/256 / 2
     * px per tick: between 28 and 31 px in 60 ticks while it has tunnel ahead. */
    {
        int16_t y0 = g_enemies[0].y_fp;
        uint32_t none = 0u;
        g_enemies[0].phase_cooldown = 1000u;
        for (int t = 0; t < 60; ++t) {
            sdd_enemies_step(&none);
        }
        int16_t moved = (int16_t)((g_enemies[0].y_fp - y0) >> FP_SHIFT);
        assert(moved >= 28 && moved <= 31);
    }

    /* 3. Verify Pump Kill Stratum + 2x Horizontal Fygar Scoring */
    assert(sdd_score_for_pump_kill(0u, false, true)  == 200u);
    assert(sdd_score_for_pump_kill(0u, true,  false) == 200u);
    assert(sdd_score_for_pump_kill(0u, true,  true)  == 400u);
    assert(sdd_score_for_pump_kill(3u, true,  true)  == 1000u);

    /* 4. Verify Indefinite Rock Hold by Player -> Wobble -> Multi-Crush & 2-Rock Veggie */
    g_rocks[0].active = true;
    g_rocks[0].state  = ROCK_SUPPORTED;
    g_rocks[0].x_fp   = 6 * FP_TILE_16;
    g_rocks[0].y_fp   = 3 * FP_TILE_16;
    sdd_world_carve_tile_box(6u, 4u, 1u, 3u);
    g_player.x_fp = 6 * FP_TILE_16;
    g_player.y_fp = (3 * 16 + 16) * FP_ONE_PX; /* Directly underneath rock! */

    for (int t = 0; t < 120; ++t) {
        (void)sdd_rocks_step();
        assert(g_rocks[0].state == ROCK_HELD_BY_PLAYER);
    }

    /* Move player away and place 2 enemies in shaft below */
    g_player.x_fp = 2 * FP_TILE_16;
    g_enemies[0].x_fp = 6 * FP_TILE_16;
    g_enemies[0].y_fp = 5 * FP_TILE_16;
    g_enemies[1].x_fp = 6 * FP_TILE_16;
    g_enemies[1].y_fp = 6 * FP_TILE_16;

    uint32_t rock_pts = 0u;
    for (int t = 0; t < 120; ++t) {
        rock_pts += sdd_rocks_step();
    }
    assert(rock_pts == 2500u); /* 2 monsters crushed by 1 rock = 2,500 pts! */
    assert(g_world.rocks_dropped == 1u);
    assert(!g_veggie.active);

    /* Drop 2nd rock -> spawns Round 1 Carrot (400 pts) */
    g_rocks[1].active = true;
    g_rocks[1].state  = ROCK_SUPPORTED;
    g_rocks[1].x_fp   = 8 * FP_TILE_16;
    g_rocks[1].y_fp   = 3 * FP_TILE_16;
    sdd_world_carve_tile_box(8u, 4u, 1u, 2u);
    for (int t = 0; t < 120; ++t) {
        (void)sdd_rocks_step();
    }
    assert(g_world.rocks_dropped == 2u);
    assert(g_veggie.active);
    assert(g_veggie.points == 400u);

    /* 5. Verify Render Strip Budget (<= 84 eng ceiling) and Art Viewer tick */
    mvs_sprites_begin();
    sdd_render_playfield_and_actors();
    sdd_render_draw_side_hud(2500u, 0u, 0u, false, 3u, 1u, 1u);
    mvs_video_commit_vblank();
    mvs_frame_stats_update();
    assert(g_frame_stats.worst_scanline_strips >= MVS_BG_COLUMNS); /* terrain layer counted */
    assert(g_frame_stats.worst_scanline_strips <= MVS_SPRITE_STRIPS_ENG_MAX);
    /* Terrain column 0 row 1 reaches VRAM through the persistent background layer */
    assert(g_mock_vram[VRAM_SCB1_BASE + 1u * 64u + 2u] != 0u);

    sdd_art_viewer_init();
    (void)sdd_art_viewer_tick_and_render();
    assert(g_frame_stats.worst_scanline_strips <= MVS_SPRITE_STRIPS_ENG_MAX);

    printf("[c-test] PASS — Native C99 Phase 1 MVS simulation & renderer verified.\n");
    return 0;
}
