/*
 * Super Dig Dug — Authentic 1982 Harpoon Reach, Thin-Dirt Pierce, 4-Stage Inflation & Pop
 */
#include "../actors/sdd_actors.h"
#include "../audio/sdd_audio.h"
#include "../platform/neogeo/neogeo_hw.h"
#include "../score/sdd_score.h"

#define HARPOON_MAX_PX         32    /* 2 tiles (32 px) reach */
#define HARPOON_STEP_PX         4    /* Extends 4 px/tick (8 ticks full reach) */
#define HOLD_PUMP_PERIOD_TICKS 18u   /* Rapid button taps pump faster than holding */
#define DEFLATE_DELAY_TICKS    36u

static void inflate_enemy_once(uint8_t e_idx, uint32_t *io_pts) {
    sdd_enemy_t *e = &g_enemies[e_idx];
    if (!e->active || e->state == ENM_STATE_DEAD || e->state == ENM_STATE_POPPING) {
        return;
    }

    ++e->inflate_stage;
    e->deflate_timer = DEFLATE_DELAY_TICKS;

    if (e->inflate_stage >= 4u) {
        /* POP! Award stratum points (doubled if Fygar is facing horizontally!) */
        e->state       = ENM_STATE_POPPING;
        e->state_timer = 18u;

        int16_t ex = (int16_t)(e->x_fp >> FP_SHIFT);
        int16_t ey = (int16_t)(e->y_fp >> FP_SHIFT);
        uint8_t stratum = sdd_world_stratum_for_y(ey);
        bool is_fygar   = (e->kind == ENEMY_KIND_FYGAR);
        bool horiz      = (e->dir == DIR_LEFT || e->dir == DIR_RIGHT);
        uint32_t kpts   = sdd_score_for_pump_kill(stratum, is_fygar, horiz);
        *io_pts += kpts;

        sdd_spawn_score_popup(ex, ey, kpts);
        sdd_audio_play_cue(AUDIO_SFX_MONSTER_POP);

        /* Detach harpoon cleanly */
        g_player.harpoon.latched      = false;
        g_player.harpoon.extending    = false;
        g_player.harpoon.length_px    = 0;
        g_player.harpoon.target_enemy = 0xFFu;
        g_player.state                = PLAYER_ALIVE;
    } else {
        e->state = ENM_STATE_INFLATED;
        sdd_audio_play_cue(AUDIO_SFX_INFLATE_STEP);
    }
}

uint32_t sdd_pump_step(uint16_t p_held, uint16_t p_pressed) {
    uint32_t pts = 0u;
    if (g_player.state != PLAYER_ALIVE && g_player.state != PLAYER_PUMPING) {
        return 0u;
    }

    sdd_harpoon_t *hp = &g_player.harpoon;

    /* 1. Already latched onto an enemy: tap A for fast pump, or hold A for steady pump */
    if (hp->latched) {
        if (hp->target_enemy >= MAX_ENEMIES ||
            !g_enemies[hp->target_enemy].active ||
            g_enemies[hp->target_enemy].state != ENM_STATE_INFLATED) {
            hp->latched      = false;
            hp->length_px    = 0;
            g_player.state   = PLAYER_ALIVE;
            return 0u;
        }

        if (p_pressed & INPUT_BTN_A) {
            hp->hold_timer = HOLD_PUMP_PERIOD_TICKS;
            inflate_enemy_once(hp->target_enemy, &pts);
        } else if (p_held & INPUT_BTN_A) {
            if (hp->hold_timer > 0u) {
                --hp->hold_timer;
            } else {
                hp->hold_timer = HOLD_PUMP_PERIOD_TICKS;
                inflate_enemy_once(hp->target_enemy, &pts);
            }
        } else {
            /* Player released pump button and stood idle: keep tether ready for fast re-tap,
               unless enemy fully deflates back to 0 in sdd_enemies_step() */
            hp->hold_timer = HOLD_PUMP_PERIOD_TICKS;
        }
        return pts;
    }

    /* 2. Extending harpoon */
    if (hp->extending) {
        hp->length_px = (int16_t)(hp->length_px + HARPOON_STEP_PX);
        int16_t px = (int16_t)(g_player.x_fp >> FP_SHIFT);
        int16_t py = (int16_t)(g_player.y_fp >> FP_SHIFT);
        int16_t tip_x = (int16_t)(px + 8);
        int16_t tip_y = (int16_t)(py + 8);

        if (hp->dir == DIR_RIGHT) tip_x = (int16_t)(px + 14 + hp->length_px);
        if (hp->dir == DIR_LEFT)  tip_x = (int16_t)(px + 2  - hp->length_px);
        if (hp->dir == DIR_DOWN)  tip_y = (int16_t)(py + 14 + hp->length_px);
        if (hp->dir == DIR_UP)    tip_y = (int16_t)(py + 2  - hp->length_px);

        /* Bounds check */
        if (tip_x < 0 || tip_x >= PLAYFIELD_PX_W || tip_y < 0 || tip_y >= PLAYFIELD_PX_H) {
            hp->extending  = false;
            hp->length_px  = 0;
            g_player.state = PLAYER_ALIVE;
            return 0u;
        }

        /* Enemy hit check FIRST (allows piercing a single thin <=8px dirt wall into an adjacent pocket!) */
        for (uint8_t i = 0u; i < MAX_ENEMIES; ++i) {
            sdd_enemy_t *e = &g_enemies[i];
            if (!e->active || e->state == ENM_STATE_DEAD || e->state == ENM_STATE_POPPING ||
                e->state == ENM_STATE_ROCK_HELD || e->state == ENM_STATE_ESCAPED) {
                continue;
            }
            /* Ghosts inside solid dirt cannot be pumped; ghosts crossing an open cell can */
            int16_t ex = (int16_t)(e->x_fp >> FP_SHIFT);
            int16_t ey = (int16_t)(e->y_fp >> FP_SHIFT);
            if (e->state == ENM_STATE_GHOST &&
                sdd_world_cell_is_solid((int16_t)((ex + 8) >> 3), (int16_t)((ey + 8) >> 3))) {
                continue;
            }
            if (tip_x >= ex && tip_x <= ex + 16 && tip_y >= ey && tip_y <= ey + 16) {
                hp->extending    = false;
                hp->latched      = true;
                hp->target_enemy = i;
                hp->hold_timer   = HOLD_PUMP_PERIOD_TICKS;
                g_player.state   = PLAYER_PUMPING;
                inflate_enemy_once(i, &pts);
                return pts;
            }
        }

        /* Thick dirt check: allow up to 8px thin partition, stop if >8px inside solid dirt */
        if (hp->length_px > 8 && sdd_world_cell_is_solid((int16_t)(tip_x >> 3), (int16_t)(tip_y >> 3))) {
            hp->extending  = false;
            hp->length_px  = 0;
            g_player.state = PLAYER_ALIVE;
            return 0u;
        }

        if (hp->length_px >= HARPOON_MAX_PX) {
            hp->extending  = false;
            hp->length_px  = 0;
            g_player.state = PLAYER_ALIVE;
        }
        return 0u;
    }

    /* 3. Fire harpoon on fresh button A press */
    if (p_pressed & INPUT_BTN_A) {
        hp->extending    = true;
        hp->latched      = false;
        hp->dir          = g_player.dir;
        hp->length_px    = 4;
        hp->target_enemy = 0xFFu;
        g_player.state   = PLAYER_PUMPING;
        sdd_audio_play_cue(AUDIO_SFX_PUMP_EXTEND);
    }
    return 0u;
}
