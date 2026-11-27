/*
 * Super Dig Dug — Taizo Player Movement, 16px Turn-Grid Alignment, Digging & Bonus Pickup
 */
#include "sdd_actors.h"
#include "../audio/sdd_audio.h"
#include "../platform/neogeo/neogeo_hw.h"
#include "../score/sdd_score.h"

sdd_player_t       g_player;
sdd_enemy_t        g_enemies[MAX_ENEMIES];
sdd_rock_t         g_rocks[MAX_ROCKS];
sdd_bonus_veggie_t g_veggie;
sdd_score_popup_t  g_popups[MAX_SCORE_POPUPS];
bool               g_hurry_up = false;
uint16_t           g_round_ticks = 0u;

/* 1982 original: the player takes a 2-pixel step each time an 8-bit
 * accumulator borrows; the rate is $50 in open tunnel and $40 against dirt
 * (0.625 and 0.5 px per frame). */
#define PLAYER_WALK_RATE       0x50u
#define PLAYER_DIG_RATE        0x40u
#define PLAYER_STEP_FP         (2 * FP_ONE_PX)
static uint8_t s_move_acc = 0u;
static uint8_t s_since_carve_px = 255u; /* distance travelled since dirt was last carved */
#define CORNER_ASSIST_PX        5   /* Auto-align into 16px intersection within 5 px */

void sdd_spawn_score_popup(int16_t px, int16_t py, uint32_t pts) {
    for (uint8_t i = 0u; i < MAX_SCORE_POPUPS; ++i) {
        if (!g_popups[i].active) {
            g_popups[i].active = true;
            g_popups[i].px     = px;
            g_popups[i].py     = py;
            g_popups[i].points = pts;
            g_popups[i].timer  = 48u;
            return;
        }
    }
    g_popups[0].active = true;
    g_popups[0].px     = px;
    g_popups[0].py     = py;
    g_popups[0].points = pts;
    g_popups[0].timer  = 48u;
}

static void reset_player_at_spawn(void) {
    s_move_acc           = 0u;
    s_since_carve_px     = 255u;
    g_player.x_fp        = (int16_t)(PLAYER_SPAWN_PX_X * FP_ONE_PX);
    g_player.y_fp        = (int16_t)(PLAYER_SPAWN_PX_Y * FP_ONE_PX);
    g_player.dir         = DIR_RIGHT;
    g_player.state       = PLAYER_ALIVE;
    g_player.moving      = false;
    g_player.digging     = false;
    g_player.anim_tick   = 0u;
    g_player.state_timer = 0u;
    g_player.harpoon.extending    = false;
    g_player.harpoon.latched      = false;
    g_player.harpoon.length_px    = 0;
    g_player.harpoon.target_enemy = 0xFFu;
    g_player.harpoon.hold_timer   = 0u;
}

void sdd_actors_spawn_round(const sdd_round_def_t *def) {
    reset_player_at_spawn();
    g_hurry_up    = false;
    g_round_ticks = 0u;
    g_veggie.active = false;

    for (uint8_t i = 0u; i < MAX_SCORE_POPUPS; ++i) {
        g_popups[i].active = false;
    }

    for (uint8_t i = 0u; i < MAX_ENEMIES; ++i) {
        g_enemies[i].active = false;
        if (def && i < def->enemy_count) {
            const sdd_enemy_spawn_t *es = &def->enemies[i];
            g_enemies[i].active         = true;
            g_enemies[i].kind           = (sdd_enemy_kind_t)es->kind;
            g_enemies[i].state          = ENM_STATE_TUNNEL;
            g_enemies[i].x_fp           = (int16_t)((int16_t)es->tx * FP_TILE_16);
            g_enemies[i].y_fp           = (int16_t)((int16_t)es->ty * FP_TILE_16);
            g_enemies[i].dir            = es->tunnel_vertical ? DIR_DOWN : DIR_RIGHT;
            g_enemies[i].horiz_facing   = DIR_RIGHT;
            g_enemies[i].inflate_stage  = 0u;
            g_enemies[i].deflate_timer  = 0u;
            g_enemies[i].phase_cooldown = (uint16_t)(180u + (uint16_t)i * 55u);
            g_enemies[i].fire_cooldown  = (uint16_t)(150u + (uint16_t)i * 40u);
            g_enemies[i].state_timer    = 0u;
            g_enemies[i].anim_tick      = 0u;
            g_enemies[i].crushing_rock  = 0xFFu;
            g_enemies[i].escaping       = false;
            g_enemies[i].speed_acc      = 0u;
        }
    }

    for (uint8_t r = 0u; r < MAX_ROCKS; ++r) {
        g_rocks[r].active = false;
        if (def && r < def->rock_count) {
            g_rocks[r].active          = true;
            g_rocks[r].state           = ROCK_SUPPORTED;
            g_rocks[r].x_fp            = (int16_t)((int16_t)def->rocks[r].tx * FP_TILE_16);
            g_rocks[r].y_fp            = (int16_t)((int16_t)def->rocks[r].ty * FP_TILE_16);
            g_rocks[r].fall_start_y_px = (int16_t)(def->rocks[r].ty * 16u);
            g_rocks[r].state_timer     = 0u;
            g_rocks[r].crushed_count   = 0u;
            g_rocks[r].crushed_player  = false;
        }
    }
}

void sdd_actors_respawn_positions(const sdd_round_def_t *def) {
    reset_player_at_spawn();
    g_veggie.active = false;
    uint8_t slot = 0u;
    for (uint8_t i = 0u; i < MAX_ENEMIES; ++i) {
        if (g_enemies[i].active && g_enemies[i].state != ENM_STATE_DEAD && g_enemies[i].state != ENM_STATE_ESCAPED) {
            if (def && slot < def->enemy_count) {
                const sdd_enemy_spawn_t *es = &def->enemies[i < def->enemy_count ? i : slot];
                g_enemies[i].x_fp          = (int16_t)((int16_t)es->tx * FP_TILE_16);
                g_enemies[i].y_fp          = (int16_t)((int16_t)es->ty * FP_TILE_16);
            }
            g_enemies[i].state          = ENM_STATE_TUNNEL;
            g_enemies[i].inflate_stage  = 0u;
            g_enemies[i].deflate_timer  = 0u;
            g_enemies[i].phase_cooldown = (uint16_t)(180u + (uint16_t)i * 45u);
            g_enemies[i].fire_cooldown  = 150u;
            ++slot;
        }
    }
}

uint8_t sdd_actors_alive_enemy_count(void) {
    uint8_t n = 0u;
    for (uint8_t i = 0u; i < MAX_ENEMIES; ++i) {
        if (g_enemies[i].active &&
            g_enemies[i].state != ENM_STATE_DEAD &&
            g_enemies[i].state != ENM_STATE_ESCAPED) {
            ++n;
        }
    }
    return n;
}

bool sdd_actors_any_rock_busy(void) {
    for (uint8_t r = 0u; r < MAX_ROCKS; ++r) {
        if (g_rocks[r].active &&
            (g_rocks[r].state == ROCK_WOBBLE ||
             g_rocks[r].state == ROCK_FALLING ||
             g_rocks[r].state == ROCK_SHATTER)) {
            return true;
        }
    }
    return false;
}

static bool blocked_by_supported_rock(int16_t next_px, int16_t next_py) {
    for (uint8_t r = 0u; r < MAX_ROCKS; ++r) {
        if (!g_rocks[r].active || g_rocks[r].state == ROCK_RETIRED || g_rocks[r].state == ROCK_FALLING || g_rocks[r].state == ROCK_SHATTER) {
            continue;
        }
        int16_t rx = (int16_t)(g_rocks[r].x_fp >> FP_SHIFT);
        int16_t ry = (int16_t)(g_rocks[r].y_fp >> FP_SHIFT);
        if (next_px + 14 > rx && next_px + 2 < rx + 16 &&
            next_py + 14 > ry && next_py + 2 < ry + 16) {
            return true;
        }
    }
    return false;
}

uint32_t sdd_player_step(uint16_t p_held, uint16_t p_pressed) {
    (void)p_pressed;
    uint32_t pts = 0u;
    ++g_round_ticks;

    /* Tick floating score popups */
    for (uint8_t i = 0u; i < MAX_SCORE_POPUPS; ++i) {
        if (g_popups[i].active) {
            if (g_popups[i].timer > 0u) {
                --g_popups[i].timer;
            } else {
                g_popups[i].active = false;
            }
        }
    }

    /* Tick bonus vegetable & pickup check */
    if (g_veggie.active) {
        if (g_veggie.timer > 0u) {
            --g_veggie.timer;
        } else {
            g_veggie.active = false;
        }
    }

    if (g_player.state == PLAYER_CRUSHED) {
        g_player.moving = false;
        return 0u;
    }

    if (g_player.state == PLAYER_DYING) {
        g_player.moving = false;
        if (g_player.state_timer > 0u) {
            --g_player.state_timer;
        } else {
            g_player.state = PLAYER_DEAD;
        }
        return 0u;
    }

    if (g_player.state == PLAYER_DEAD) {
        g_player.moving = false;
        return 0u;
    }

    /* If harpoon is actively extending or latched and player hasn't moved off it */
    int8_t want_dir = -1;
    if (p_held & INPUT_RIGHT)      want_dir = (int8_t)DIR_RIGHT;
    else if (p_held & INPUT_LEFT)  want_dir = (int8_t)DIR_LEFT;
    else if (p_held & INPUT_UP)    want_dir = (int8_t)DIR_UP;
    else if (p_held & INPUT_DOWN)  want_dir = (int8_t)DIR_DOWN;

    /* Moving while latched immediately detaches the pump tether (classic 1982 rule!) */
    if (want_dir >= 0 && g_player.harpoon.latched) {
        g_player.harpoon.latched   = false;
        g_player.harpoon.extending = false;
        g_player.harpoon.length_px = 0;
        g_player.state             = PLAYER_ALIVE;
    }

    if (g_player.harpoon.extending || g_player.harpoon.latched) {
        g_player.moving  = false;
        g_player.digging = false;
        return 0u;
    }

    g_player.moving  = false;
    g_player.digging = false;

    if (want_dir >= 0) {
        sdd_dir_t d = (sdd_dir_t)want_dir;
        int16_t px = (int16_t)(g_player.x_fp >> FP_SHIFT);
        int16_t py = (int16_t)(g_player.y_fp >> FP_SHIFT);

        /* Enforce 16px corridor centerline alignment on perpendicular turns */
        bool want_horiz = (d == DIR_LEFT || d == DIR_RIGHT);
        if (want_horiz && (py & 15) != 0) {
            int16_t rem = (int16_t)(py & 15);
            if (rem <= CORNER_ASSIST_PX) {
                d = DIR_UP;
            } else if (rem >= (16 - CORNER_ASSIST_PX)) {
                d = DIR_DOWN;
            } else {
                d = g_player.dir;
            }
        } else if (!want_horiz && (px & 15) != 0) {
            int16_t rem = (int16_t)(px & 15);
            if (rem <= CORNER_ASSIST_PX) {
                d = DIR_LEFT;
            } else if (rem >= (16 - CORNER_ASSIST_PX)) {
                d = DIR_RIGHT;
            } else {
                d = g_player.dir;
            }
        }

        /* Snap orthogonal axis cleanly onto 16px centerline */
        if (d == DIR_LEFT || d == DIR_RIGHT) {
            g_player.y_fp = (int16_t)(((py + 8) & ~15) * FP_ONE_PX);
        } else {
            g_player.x_fp = (int16_t)(((px + 8) & ~15) * FP_ONE_PX);
        }

        /* Determine if destination overlaps intact dirt -> dig speed vs walk speed */
        int16_t probe_px = (int16_t)(g_player.x_fp >> FP_SHIFT);
        int16_t probe_py = (int16_t)(g_player.y_fp >> FP_SHIFT);
        if (d == DIR_RIGHT) probe_px += 2;
        if (d == DIR_LEFT)  probe_px -= 2;
        if (d == DIR_DOWN)  probe_py += 2;
        if (d == DIR_UP)    probe_py -= 2;

        bool hits_dirt =
            sdd_world_cell_is_solid((int16_t)((probe_px + 2) >> 3),  (int16_t)((probe_py + 2) >> 3)) ||
            sdd_world_cell_is_solid((int16_t)((probe_px + 13) >> 3), (int16_t)((probe_py + 2) >> 3)) ||
            sdd_world_cell_is_solid((int16_t)((probe_px + 2) >> 3),  (int16_t)((probe_py + 13) >> 3)) ||
            sdd_world_cell_is_solid((int16_t)((probe_px + 13) >> 3), (int16_t)((probe_py + 13) >> 3));

        /* A dirt cell is carved as soon as the body overlaps it, so keep the
         * dig rate until the body has travelled the rest of that 8-px cell;
         * otherwise half of every cell would be crossed at walking speed. */
        if (s_since_carve_px < 8u) {
            hits_dirt = true;
        }

        uint8_t rate     = hits_dirt ? PLAYER_DIG_RATE : PLAYER_WALK_RATE;
        uint8_t acc_prev = s_move_acc;
        s_move_acc       = (uint8_t)(s_move_acc - rate);
        int16_t step_fp  = (s_move_acc > acc_prev) ? PLAYER_STEP_FP : 0; /* borrow -> step */
        int16_t nx_fp   = g_player.x_fp;
        int16_t ny_fp   = g_player.y_fp;

        if (d == DIR_RIGHT) nx_fp = (int16_t)(nx_fp + step_fp);
        if (d == DIR_LEFT)  nx_fp = (int16_t)(nx_fp - step_fp);
        if (d == DIR_DOWN)  ny_fp = (int16_t)(ny_fp + step_fp);
        if (d == DIR_UP)    ny_fp = (int16_t)(ny_fp - step_fp);

        /* Clamp to 224x224 playfield bounds (16x16 body -> 0..208 px) */
        if (nx_fp < 0) nx_fp = 0;
        if (ny_fp < 0) ny_fp = 0;
        if (nx_fp > 208 * FP_ONE_PX) nx_fp = 208 * FP_ONE_PX;
        if (ny_fp > 208 * FP_ONE_PX) ny_fp = 208 * FP_ONE_PX;

        if (!blocked_by_supported_rock((int16_t)(nx_fp >> FP_SHIFT), (int16_t)(ny_fp >> FP_SHIFT))) {
            /* Moving and digging describe intent, not this tick's sub-step, so
             * the walk music and sprite do not flicker between 2-pixel steps. */
            g_player.dir     = d;
            g_player.moving  = true;
            g_player.digging = hits_dirt;
            g_player.x_fp    = nx_fp;
            g_player.y_fp    = ny_fp;
            ++g_player.anim_tick;
            if (step_fp != 0 && s_since_carve_px < 250u) {
                s_since_carve_px = (uint8_t)(s_since_carve_px + 2u);
            }

            uint8_t carved = sdd_world_carve_footprint_16x16(
                (int16_t)(g_player.x_fp >> FP_SHIFT),
                (int16_t)(g_player.y_fp >> FP_SHIFT)
            );
            if (carved > 0u) {
                s_since_carve_px = 0u;
                g_player.digging = true;
                pts += (uint32_t)carved * 10u;
                sdd_audio_play_cue(AUDIO_SFX_DIG);
            }
        }
    }

    /* Bonus vegetable collection check */
    if (g_veggie.active) {
        int16_t px = (int16_t)(g_player.x_fp >> FP_SHIFT);
        int16_t py = (int16_t)(g_player.y_fp >> FP_SHIFT);
        if (px + 14 > g_veggie.px && px + 2 < g_veggie.px + 16 &&
            py + 14 > g_veggie.py && py + 2 < g_veggie.py + 16) {
            pts += g_veggie.points;
            sdd_spawn_score_popup(g_veggie.px, g_veggie.py, g_veggie.points);
            g_veggie.active = false;
            sdd_audio_play_cue(AUDIO_SFX_PICKUP);
        }
    }

    return pts;
}
