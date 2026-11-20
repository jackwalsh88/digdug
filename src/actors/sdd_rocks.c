/*
 * Super Dig Dug — Authentic 1982 Rock Physics, Indefinite Player-Hold, Multi-Crush & 2-Rock Veggie Trigger
 */
#include "sdd_actors.h"
#include "../audio/sdd_audio.h"
#include "../score/sdd_score.h"

#define ROCK_WOBBLE_TICKS    32u
#define ROCK_SHATTER_TICKS   20u
#define ROCK_FALL_SPEED_FP   40   /* 2.5 px/tick */

static bool rock_has_dirt_support(int16_t rx, int16_t ry) {
    int16_t cy_below = (int16_t)((ry + 16) >> 3);
    if (cy_below >= WORLD_CELLS_H) {
        return true;
    }
    int16_t cx_l = (int16_t)((rx + 2) >> 3);
    int16_t cx_r = (int16_t)((rx + 13) >> 3);
    return sdd_world_cell_is_solid(cx_l, cy_below) || sdd_world_cell_is_solid(cx_r, cy_below);
}

static bool player_holding_rock_from_below(int16_t rx, int16_t ry) {
    if (g_player.state == PLAYER_DEAD || g_player.state == PLAYER_DYING) {
        return false;
    }
    int16_t px = (int16_t)(g_player.x_fp >> FP_SHIFT);
    int16_t py = (int16_t)(g_player.y_fp >> FP_SHIFT);
    /* Classic 1982 rule: rock stays propped up as long as Dig Dug's head is right below it */
    return (px + 14 > rx) && (px + 2 < rx + 16) && (py >= ry + 10) && (py <= ry + 20);
}

uint32_t sdd_rocks_step(void) {
    uint32_t total_pts = 0u;

    for (uint8_t r = 0u; r < MAX_ROCKS; ++r) {
        sdd_rock_t *rk = &g_rocks[r];
        if (!rk->active || rk->state == ROCK_RETIRED) {
            continue;
        }

        int16_t rx = (int16_t)(rk->x_fp >> FP_SHIFT);
        int16_t ry = (int16_t)(rk->y_fp >> FP_SHIFT);

        switch (rk->state) {
            case ROCK_SUPPORTED:
                if (!rock_has_dirt_support(rx, ry)) {
                    if (player_holding_rock_from_below(rx, ry)) {
                        rk->state = ROCK_HELD_BY_PLAYER;
                    } else {
                        rk->state           = ROCK_WOBBLE;
                        rk->state_timer     = ROCK_WOBBLE_TICKS;
                        rk->fall_start_y_px = ry;
                        sdd_world_carve_tile_box((uint8_t)(rx >> 4), (uint8_t)(ry >> 4), 1u, 1u);
                        sdd_audio_play_cue(AUDIO_SFX_ROCK_WOBBLE);
                    }
                }
                break;

            case ROCK_HELD_BY_PLAYER:
                /* Waits indefinitely until player clears out from directly underneath! */
                if (!player_holding_rock_from_below(rx, ry)) {
                    rk->state           = ROCK_WOBBLE;
                    rk->state_timer     = ROCK_WOBBLE_TICKS;
                    rk->fall_start_y_px = ry;
                    sdd_world_carve_tile_box((uint8_t)(rx >> 4), (uint8_t)(ry >> 4), 1u, 1u);
                    sdd_audio_play_cue(AUDIO_SFX_ROCK_WOBBLE);
                }
                break;

            case ROCK_WOBBLE:
                if (rk->state_timer > 0u) {
                    --rk->state_timer;
                } else {
                    rk->state          = ROCK_FALLING;
                    rk->crushed_count  = 0u;
                    rk->crushed_player = false;
                    sdd_audio_play_cue(AUDIO_SFX_ROCK_FALL);
                }
                break;

            case ROCK_FALLING: {
                rk->y_fp = (int16_t)(rk->y_fp + ROCK_FALL_SPEED_FP);
                ry       = (int16_t)(rk->y_fp >> FP_SHIFT);

                /* Carve shaft behind falling boulder */
                sdd_world_carve_footprint_16x16(rx, ry);

                /* Sweep enemies (including ghost-eyes & inflated monsters!) */
                for (uint8_t i = 0u; i < MAX_ENEMIES; ++i) {
                    sdd_enemy_t *e = &g_enemies[i];
                    if (!e->active || e->state == ENM_STATE_DEAD || e->state == ENM_STATE_ESCAPED) {
                        continue;
                    }
                    if (e->state == ENM_STATE_ROCK_HELD) {
                        if (e->crushing_rock == r) {
                            e->y_fp = rk->y_fp;
                        }
                        continue;
                    }
                    int16_t ex = (int16_t)(e->x_fp >> FP_SHIFT);
                    int16_t ey = (int16_t)(e->y_fp >> FP_SHIFT);
                    if (ex + 14 > rx && ex + 2 < rx + 16 && ey + 14 > ry && ey + 2 < ry + 16) {
                        e->state         = ENM_STATE_ROCK_HELD;
                        e->crushing_rock = r;
                        e->x_fp          = rk->x_fp;
                        e->y_fp          = rk->y_fp;
                        ++rk->crushed_count;
                        if (g_player.harpoon.latched && g_player.harpoon.target_enemy == i) {
                            g_player.harpoon.latched   = false;
                            g_player.harpoon.length_px = 0;
                            g_player.state             = PLAYER_ALIVE;
                        }
                    }
                }

                /* Check player crush (points for enemies crushed by the same rock still count!) */
                if (g_player.state == PLAYER_ALIVE || g_player.state == PLAYER_PUMPING) {
                    int16_t px = (int16_t)(g_player.x_fp >> FP_SHIFT);
                    int16_t py = (int16_t)(g_player.y_fp >> FP_SHIFT);
                    if (px + 13 > rx && px + 3 < rx + 16 && py + 13 > ry && py + 3 < ry + 16) {
                        g_player.state             = PLAYER_CRUSHED;
                        g_player.harpoon.extending = false;
                        g_player.harpoon.latched   = false;
                        rk->crushed_player         = true;
                        sdd_audio_play_cue(AUDIO_SFX_PLAYER_HURT);
                    }
                }
                if (rk->crushed_player) {
                    g_player.y_fp = rk->y_fp;
                }

                /* Check tunnel floor / playfield bottom impact after dropping >= 12 px */
                bool hit_bottom = (ry >= 208);
                bool hit_floor  = ((ry - rk->fall_start_y_px) >= 12) && rock_has_dirt_support(rx, ry);
                if (hit_bottom || hit_floor) {
                    if (hit_bottom) {
                        rk->y_fp = 208 * FP_ONE_PX;
                        ry       = 208;
                    }
                    rk->state       = ROCK_SHATTER;
                    rk->state_timer = ROCK_SHATTER_TICKS;
                    sdd_audio_play_cue(AUDIO_SFX_ROCK_IMPACT);

                    /* Finalize all enemies crushed by this rock */
                    for (uint8_t i = 0u; i < MAX_ENEMIES; ++i) {
                        if (g_enemies[i].active &&
                            g_enemies[i].state == ENM_STATE_ROCK_HELD &&
                            g_enemies[i].crushing_rock == r) {
                            g_enemies[i].state = ENM_STATE_DEAD;
                        }
                    }

                    uint32_t cpts = sdd_score_for_rock_crush(rk->crushed_count);
                    if (cpts > 0u) {
                        total_pts += cpts;
                        sdd_spawn_score_popup(rx, ry, cpts);
                    }

                    if (rk->crushed_player) {
                        g_player.state       = PLAYER_DYING;
                        g_player.state_timer = 36u;
                    }

                    /* Spawn round bonus vegetable at center chamber after 2nd rock drops! */
                    ++g_world.rocks_dropped;
                    if (g_world.rocks_dropped == 2u && !g_world.veggie_spawned) {
                        g_world.veggie_spawned = true;
                        g_veggie.active        = true;
                        g_veggie.px            = PLAYER_SPAWN_PX_X;
                        g_veggie.py            = PLAYER_SPAWN_PX_Y;
                        g_veggie.timer         = 600u;
                        g_veggie.points        = sdd_score_for_round_vegetable(
                            g_world.round_num,
                            &g_veggie.reward_frame_idx
                        );
                    }
                }
                break;
            }

            case ROCK_SHATTER:
                if (rk->state_timer > 0u) {
                    --rk->state_timer;
                } else {
                    rk->state  = ROCK_RETIRED;
                    rk->active = false;
                }
                break;

            default:
                break;
        }
    }

    return total_pts;
}
