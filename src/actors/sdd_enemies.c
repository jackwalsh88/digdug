/*
 * Super Dig Dug — Authentic 1982 Pooka & Fygar AI, Ghost-Eyes Phasing, Horizontal Fire & Escape
 */
#include "sdd_actors.h"
#include "../audio/sdd_audio.h"
#include "../platform/neogeo/neogeo_hw.h"

/* Movement follows the 1982 original: Pookas and Fygars are updated on
 * alternate frames; on its frame a monster subtracts its speed from an 8-bit
 * accumulator and takes one 2-pixel step when that borrows. Speeds come from
 * the ROM tables (k_dd82_speed_*), indexed by round step and tier. */
#define ENEMY_STEP_FP          (2 * FP_ONE_PX)
#define GHOST_STEP_FP          (1 * FP_ONE_PX)  /* estimate: ghost drift is half a tunnel step */
static uint8_t s_frame_phase = 0u;

static uint8_t enemy_speed(const sdd_enemy_t *e, bool on_surface) {
    uint8_t step  = sdd_world_round_step();
    bool    fygar = (e->kind == ENEMY_KIND_FYGAR);
    uint16_t spd;
    if (on_surface) {
        spd = (uint16_t)(k_dd82_speed_surface[step] + (fygar ? 10u : 0u));
    } else {
        /* Tier mapping is this port's reading of the original's two state
         * flags: fast for the last monster fleeing, mid during hurry-up. */
        uint8_t tier = e->escaping ? DD82_TIER_FAST : (g_hurry_up ? DD82_TIER_MID : DD82_TIER_NORMAL);
        spd = k_dd82_speed_tier[(fygar ? 3u : 0u) + tier][step];
    }
    if (e->dir == DIR_DOWN && step >= 3u) {
        spd = (uint16_t)(spd + k_dd82_speed_down_bonus);
    }
    return (spd > 255u) ? 255u : (uint8_t)spd;
}

/* Returns true when this monster takes a step on this frame. */
static bool enemy_step_due(sdd_enemy_t *e, bool on_surface) {
    bool my_frame = ((s_frame_phase & 1u) == ((e->kind == ENEMY_KIND_FYGAR) ? 1u : 0u));
    if (!my_frame) {
        return false;
    }
    uint8_t prev = e->speed_acc;
    e->speed_acc = (uint8_t)(e->speed_acc - enemy_speed(e, on_surface));
    return e->speed_acc > prev;
}

#define FYGAR_INHALE_TICKS     24u
#define FYGAR_FIRE_TICKS       24u
#define DEFLATE_STEP_TICKS     36u

static int16_t abs_i16(int16_t v) {
    return v < 0 ? (int16_t)(-v) : v;
}

static sdd_dir_t opposite_dir(sdd_dir_t d) {
    return (sdd_dir_t)(((uint8_t)d + 2u) & 3u);
}

static bool enemy_tile_passable(int16_t tx, int16_t ty) {
    if (!sdd_world_tile_is_open(tx, ty)) {
        return false;
    }
    int16_t px = (int16_t)(tx * 16);
    int16_t py = (int16_t)(ty * 16);
    for (uint8_t r = 0u; r < MAX_ROCKS; ++r) {
        if (!g_rocks[r].active || g_rocks[r].state == ROCK_RETIRED ||
            g_rocks[r].state == ROCK_FALLING || g_rocks[r].state == ROCK_SHATTER) {
            continue;
        }
        int16_t rx = (int16_t)(g_rocks[r].x_fp >> FP_SHIFT);
        int16_t ry = (int16_t)(g_rocks[r].y_fp >> FP_SHIFT);
        if (rx == px && ry == py) {
            return false;
        }
    }
    return true;
}

/* Compute Fygar horizontal flame extent in pixels (up to 48px = 3 tiles; pierces <=1 thin dirt cell) */
static int16_t fygar_flame_reach_px(const sdd_enemy_t *e) {
    int16_t ex = (int16_t)(e->x_fp >> FP_SHIFT);
    int16_t ey = (int16_t)(e->y_fp >> FP_SHIFT);
    int16_t reach = 0;
    uint8_t solid_cells_seen = 0u;

    for (int16_t step = 8; step <= 48; step = (int16_t)(step + 8)) {
        int16_t test_x = (e->horiz_facing == DIR_RIGHT)
            ? (int16_t)(ex + 15 + step)
            : (int16_t)(ex - step);
        if (test_x < 0 || test_x >= PLAYFIELD_PX_W) {
            break;
        }
        if (sdd_world_cell_is_solid((int16_t)(test_x >> 3), (int16_t)((ey + 8) >> 3))) {
            ++solid_cells_seen;
            if (solid_cells_seen > 1u) {
                break;
            }
        }
        reach = step;
    }
    return reach;
}

static void hurt_player_if_vulnerable(void) {
    if (g_player.state == PLAYER_ALIVE || g_player.state == PLAYER_PUMPING) {
        g_player.state             = PLAYER_DYING;
        g_player.state_timer       = 36u;
        g_player.harpoon.extending = false;
        g_player.harpoon.latched   = false;
        sdd_audio_play_cue(AUDIO_SFX_PLAYER_HURT);
    }
}

void sdd_enemies_step(uint32_t *io_awarded_pts) {
    (void)io_awarded_pts;
    ++s_frame_phase;
    uint8_t alive = sdd_actors_alive_enemy_count();
    if ((alive == 1u || g_round_ticks >= 1800u) && !g_hurry_up) {
        g_hurry_up = true;
        sdd_audio_play_cue(AUDIO_SFX_WARNING);
    }

    int16_t px = (int16_t)(g_player.x_fp >> FP_SHIFT);
    int16_t py = (int16_t)(g_player.y_fp >> FP_SHIFT);

    for (uint8_t i = 0u; i < MAX_ENEMIES; ++i) {
        sdd_enemy_t *e = &g_enemies[i];
        if (!e->active || e->state == ENM_STATE_DEAD ||
            e->state == ENM_STATE_ESCAPED || e->state == ENM_STATE_ROCK_HELD) {
            continue;
        }

        if (alive == 1u) {
            e->escaping = true;
        }

        int16_t ex = (int16_t)(e->x_fp >> FP_SHIFT);
        int16_t ey = (int16_t)(e->y_fp >> FP_SHIFT);
        ++e->anim_tick;

        /* 1. Popping animation completion */
        if (e->state == ENM_STATE_POPPING) {
            if (e->state_timer > 0u) {
                --e->state_timer;
            } else {
                e->state = ENM_STATE_DEAD;
            }
            continue;
        }

        /* 2. Inflated state: harmless pass-through + stage-by-stage deflation when not actively pumped */
        if (e->state == ENM_STATE_INFLATED) {
            bool actively_held =
                g_player.harpoon.latched &&
                (g_player.harpoon.target_enemy == i) &&
                ((g_input.held[0] & INPUT_BTN_A) != 0u);

            if (!actively_held) {
                if (e->deflate_timer > 0u) {
                    --e->deflate_timer;
                } else {
                    if (e->inflate_stage > 0u) {
                        --e->inflate_stage;
                    }
                    e->deflate_timer = DEFLATE_STEP_TICKS;
                    if (e->inflate_stage == 0u) {
                        e->state = ENM_STATE_TUNNEL;
                        if (g_player.harpoon.latched && g_player.harpoon.target_enemy == i) {
                            g_player.harpoon.latched   = false;
                            g_player.harpoon.length_px = 0;
                            g_player.state             = PLAYER_ALIVE;
                        }
                    }
                }
            }
            continue;
        }

        /* 3. Fygar Inhale Warning -> Horizontal Fire Breath */
        if (e->state == ENM_STATE_INHALE) {
            if (e->state_timer > 0u) {
                --e->state_timer;
            } else {
                e->state       = ENM_STATE_FIRE;
                e->state_timer = FYGAR_FIRE_TICKS;
                sdd_audio_play_cue(AUDIO_SFX_FIRE_BREATH);
            }
            /* Body contact is still lethal during inhale */
            if (px + 12 > ex && px + 4 < ex + 16 && py + 12 > ey && py + 4 < ey + 16) {
                hurt_player_if_vulnerable();
            }
            continue;
        }

        if (e->state == ENM_STATE_FIRE) {
            int16_t reach = fygar_flame_reach_px(e);
            if (reach > 0) {
                int16_t fx0 = (e->horiz_facing == DIR_RIGHT) ? (int16_t)(ex + 16) : (int16_t)(ex - reach);
                int16_t fx1 = (e->horiz_facing == DIR_RIGHT) ? (int16_t)(ex + 16 + reach) : ex;
                if (px + 12 > fx0 && px + 4 < fx1 && py + 12 > ey && py + 4 < ey + 16) {
                    hurt_player_if_vulnerable();
                }
            }
            if (px + 12 > ex && px + 4 < ex + 16 && py + 12 > ey && py + 4 < ey + 16) {
                hurt_player_if_vulnerable();
            }
            if (e->state_timer > 0u) {
                --e->state_timer;
            } else {
                e->state         = ENM_STATE_TUNNEL;
                e->fire_cooldown = 180u;
            }
            continue;
        }

        /* Target selection: sole survivor heads to surface (y=0) then top-left exit (x=0, y=0) */
        int16_t target_x = e->escaping ? (ey <= 2 ? 0 : ex) : px;
        int16_t target_y = e->escaping ? 0 : py;

        if (e->escaping && ex <= 2 && ey <= 2) {
            e->state = ENM_STATE_ESCAPED;
            continue;
        }

        /* 4. Ghost-Eyes Phasing State */
        if (e->state == ENM_STATE_GHOST) {
            ++e->state_timer;
            int16_t dx = (int16_t)(target_x - ex);
            int16_t dy = (int16_t)(target_y - ey);
            if (enemy_step_due(e, false)) {
                if (dx > 0) { e->x_fp = (int16_t)(e->x_fp + GHOST_STEP_FP); e->horiz_facing = DIR_RIGHT; e->dir = DIR_RIGHT; }
                if (dx < 0) { e->x_fp = (int16_t)(e->x_fp - GHOST_STEP_FP); e->horiz_facing = DIR_LEFT;  e->dir = DIR_LEFT;  }
                if (dy > 0) { e->y_fp = (int16_t)(e->y_fp + GHOST_STEP_FP); }
                if (dy < 0) { e->y_fp = (int16_t)(e->y_fp - GHOST_STEP_FP); }
            }

            ex = (int16_t)(e->x_fp >> FP_SHIFT);
            ey = (int16_t)(e->y_fp >> FP_SHIFT);

            /* Re-materialize into an open tunnel tile near grid intersection after >= 24 ticks */
            if (e->state_timer >= 24u && (ex & 15) <= 2 && (ey & 15) <= 2) {
                int16_t tx = (int16_t)((ex + 4) >> 4);
                int16_t ty = (int16_t)((ey + 4) >> 4);
                if (enemy_tile_passable(tx, ty)) {
                    e->x_fp           = (int16_t)(tx * FP_TILE_16);
                    e->y_fp           = (int16_t)(ty * FP_TILE_16);
                    e->state          = ENM_STATE_TUNNEL;
                    e->phase_cooldown = 240u;
                }
            }
        } else {
            /* 5. Normal Tunnel Chase State */
            int16_t speed_fp = enemy_step_due(e, ey == 0) ? ENEMY_STEP_FP : 0;

            /* Check Fygar fire trigger when horizontally aligned & cooldown expired */
            if (e->kind == ENEMY_KIND_FYGAR && !e->escaping) {
                if (e->fire_cooldown > 0u) {
                    --e->fire_cooldown;
                } else if ((ey & 15) == 0 && (e->dir == DIR_LEFT || e->dir == DIR_RIGHT) &&
                           fygar_flame_reach_px(e) >= 16) {
                    e->state       = ENM_STATE_INHALE;
                    e->state_timer = FYGAR_INHALE_TICKS;
                    continue;
                }
            }

            /* Check Ghost-Eyes phase cooldown */
            if (e->phase_cooldown > 0u) {
                --e->phase_cooldown;
            } else if ((e->escaping && ey > 0) || !e->escaping) {
                e->state       = ENM_STATE_GHOST;
                e->state_timer = 0u;
                sdd_audio_play_cue(AUDIO_SFX_PHASE);
                continue;
            }

            /* Evaluate intersection turns when aligned on 16x16 grid */
            static const int8_t k_dx[4] = { 1, 0, -1, 0 };
            static const int8_t k_dy[4] = { 0, -1, 0, 1 };

            if ((ex & 15) == 0 && (ey & 15) == 0) {
                int16_t tx = (int16_t)(ex >> 4);
                int16_t ty = (int16_t)(ey >> 4);

                if (e->escaping && ty == 0) {
                    e->dir          = DIR_LEFT;
                    e->horiz_facing = DIR_LEFT;
                } else {
                    sdd_dir_t rev = opposite_dir(e->dir);
                    int16_t best_dist = 30000;
                    int8_t  best_dir  = -1;

                    for (uint8_t cand = 0u; cand < 4u; ++cand) {
                        if ((sdd_dir_t)cand == rev) {
                            continue;
                        }
                        int16_t ntx = (int16_t)(tx + k_dx[cand]);
                        int16_t nty = (int16_t)(ty + k_dy[cand]);
                        if (enemy_tile_passable(ntx, nty)) {
                            int16_t dman = (int16_t)(abs_i16((int16_t)(ntx * 16 - target_x)) +
                                                     abs_i16((int16_t)(nty * 16 - target_y)));
                            if (dman < best_dist) {
                                best_dist = dman;
                                best_dir  = (int8_t)cand;
                            }
                        }
                    }

                    if (best_dir < 0) {
                        int16_t rtx = (int16_t)(tx + k_dx[rev]);
                        int16_t rty = (int16_t)(ty + k_dy[rev]);
                        if (enemy_tile_passable(rtx, rty)) {
                            best_dir = (int8_t)rev;
                        } else if (e->escaping && ey > 0) {
                            e->state       = ENM_STATE_GHOST;
                            e->state_timer = 0u;
                            continue;
                        }
                    }

                    if (best_dir >= 0) {
                        e->dir = (sdd_dir_t)best_dir;
                        if (e->dir == DIR_LEFT || e->dir == DIR_RIGHT) {
                            e->horiz_facing = e->dir;
                        }
                    }
                }
            }

            /* Verify tile ahead is passable when leaving a grid intersection */
            bool can_advance = true;
            if ((ex & 15) == 0 && (ey & 15) == 0) {
                int16_t ntx = (int16_t)((ex >> 4) + k_dx[e->dir]);
                int16_t nty = (int16_t)((ey >> 4) + k_dy[e->dir]);
                can_advance = enemy_tile_passable(ntx, nty);
            }

            if (can_advance) {
                int16_t nx_fp = e->x_fp;
                int16_t ny_fp = e->y_fp;
                if (e->dir == DIR_RIGHT) {
                    int16_t next_grid = (int16_t)(((ex >> 4) + 1) * FP_TILE_16);
                    nx_fp = (int16_t)(e->x_fp + speed_fp);
                    if (nx_fp > next_grid) nx_fp = next_grid;
                } else if (e->dir == DIR_LEFT) {
                    int16_t prev_grid = (ex == 0) ? 0 : (int16_t)(((ex - 1) >> 4) * FP_TILE_16);
                    nx_fp = (int16_t)(e->x_fp - speed_fp);
                    if (nx_fp < prev_grid) nx_fp = prev_grid;
                } else if (e->dir == DIR_DOWN) {
                    int16_t next_grid = (int16_t)(((ey >> 4) + 1) * FP_TILE_16);
                    ny_fp = (int16_t)(e->y_fp + speed_fp);
                    if (ny_fp > next_grid) ny_fp = next_grid;
                } else if (e->dir == DIR_UP) {
                    int16_t prev_grid = (ey == 0) ? 0 : (int16_t)(((ey - 1) >> 4) * FP_TILE_16);
                    ny_fp = (int16_t)(e->y_fp - speed_fp);
                    if (ny_fp < prev_grid) ny_fp = prev_grid;
                }

                if (nx_fp >= 0 && nx_fp <= 208 * FP_ONE_PX && ny_fp >= 0 && ny_fp <= 208 * FP_ONE_PX) {
                    e->x_fp = nx_fp;
                    e->y_fp = ny_fp;
                }
            }
        }

        /* Lethal body contact check (note: ENM_STATE_INFLATED returned early above -> harmless pass-through!) */
        ex = (int16_t)(e->x_fp >> FP_SHIFT);
        ey = (int16_t)(e->y_fp >> FP_SHIFT);
        if (px + 12 > ex && px + 4 < ex + 16 && py + 12 > ey && py + 4 < ey + 16) {
            hurt_player_if_vulnerable();
        }
    }
}
