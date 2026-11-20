/*
 * Super Dig Dug — Phase 1 (1982 Dig Dug Replica) Arcade Game Loop & State Machine
 * Supports Title, Attract Demo, 1P/2P Alternating Play, Ready, Stage Clear, Game Over & Viewer.
 */
#include "sdd_game.h"
#include "../actors/sdd_actors.h"
#include "../audio/sdd_audio.h"
#include "../platform/neogeo/neogeo_hw.h"
#include "../render/sdd_render.h"
#include "../score/sdd_score.h"
#include "../world/sdd_world.h"
#include "../../../assets/generated/sdd_assets.h"

sdd_game_session_t g_game;
static sdd_round_def_t s_cur_round_def;

static void start_player_round(bool fresh_round) {
    uint8_t p = g_game.active_player;
    if (fresh_round) {
        sdd_world_init_round(g_game.round_num[p], &s_cur_round_def);
        sdd_actors_spawn_round(&s_cur_round_def);
    } else {
        sdd_actors_respawn_positions(&s_cur_round_def);
    }
    g_game.mode       = GAME_MODE_READY;
    g_game.mode_timer = 90u;
    mvs_fix_clear_all();
    sdd_audio_stop_all();
    sdd_audio_play_cue(AUDIO_STG_READY);
}

static void enter_title(void) {
    g_game.mode       = GAME_MODE_TITLE;
    g_game.mode_timer = 360u;
    mvs_fix_clear_all();
    sdd_audio_stop_all();
}

static void enter_attract_demo(void) {
    g_game.mode          = GAME_MODE_ATTRACT;
    g_game.mode_timer    = 600u;
    g_game.active_player = 0u;
    sdd_world_init_round(1u, &s_cur_round_def);
    sdd_actors_spawn_round(&s_cur_round_def);
    mvs_fix_clear_all();
}

void sdd_game_init(bool boot_into_viewer) {
    sdd_score_init_defaults();
    sdd_audio_init();

    g_game.credits       = 0u;
    g_game.two_player    = false;
    g_game.active_player = 0u;
    g_game.score[0]      = 0u;
    g_game.score[1]      = 0u;
    g_game.lives[0]      = 3u;
    g_game.lives[1]      = 0u;
    g_game.extra_flags[0]= 0u;
    g_game.extra_flags[1]= 0u;
    g_game.round_num[0]  = 1u;
    g_game.round_num[1]  = 1u;

    if (boot_into_viewer) {
        g_game.mode = GAME_MODE_ART_VIEWER;
        sdd_art_viewer_init();
    } else {
        enter_title();
        sdd_audio_play_cue(AUDIO_STG_TITLE);
    }
}

static void begin_new_credit_game(bool two_players) {
    g_game.two_player     = two_players;
    g_game.active_player  = 0u;
    g_game.score[0]       = 0u;
    g_game.score[1]       = 0u;
    g_game.lives[0]       = 3u;
    g_game.lives[1]       = two_players ? 3u : 0u;
    g_game.extra_flags[0] = 0u;
    g_game.extra_flags[1] = 0u;
    g_game.round_num[0]   = 1u;
    g_game.round_num[1]   = 1u;
    start_player_round(true);
}

static void award_session_points(uint32_t pts) {
    if (pts == 0u) {
        return;
    }
    uint8_t p = g_game.active_player;
    uint8_t extra = sdd_score_award(&g_game.score[p], &g_game.extra_flags[p], pts);
    if (extra > 0u) {
        g_game.lives[p] = (uint8_t)(g_game.lives[p] + extra);
        sdd_audio_play_cue(AUDIO_STG_EXTRA_LIFE);
    }
}

void sdd_game_tick(void) {
    /* Coin insertion (SELECT on AES/dev or COIN chute on MVS) */
    if ((g_input.sys_pressed & INPUT_COIN) || (g_input.pressed[0] & INPUT_SELECT)) {
        if (g_game.credits < 99u && !(g_input.held[0] & INPUT_START)) {
            ++g_game.credits;
            sdd_audio_play_cue(AUDIO_SFX_PICKUP);
        }
    }

    /* Hardware TEST switch or START+SELECT opens B0/M0 Art & Hardware Diagnostics Viewer */
    if ((g_input.sys_pressed & INPUT_TEST) ||
        ((g_input.held[0] & INPUT_START) && (g_input.pressed[0] & INPUT_SELECT) && g_game.mode != GAME_MODE_ART_VIEWER)) {
        g_game.mode = GAME_MODE_ART_VIEWER;
        sdd_art_viewer_init();
        return;
    }

    if (g_game.mode == GAME_MODE_ART_VIEWER) {
        if (sdd_art_viewer_tick_and_render()) {
            enter_title();
        }
        return;
    }

    /* Allow starting 1P or 2P from Title or Attract (free-play allowed via START if credits==0 in dev build) */
    if (g_game.mode == GAME_MODE_TITLE || g_game.mode == GAME_MODE_ATTRACT) {
        if (g_input.pressed[0] & INPUT_START) {
            if (g_game.credits > 0u) --g_game.credits;
            begin_new_credit_game(false);
            return;
        }
        if (g_input.pressed[1] & INPUT_START) {
            if (g_game.credits >= 2u) g_game.credits = (uint8_t)(g_game.credits - 2u);
            else g_game.credits = 0u;
            begin_new_credit_game(true);
            return;
        }
    }

    mvs_sprites_begin();

    switch (g_game.mode) {
        case GAME_MODE_TITLE: {
            /* Draw UI Logo wordmark + cast showcase + NAMCO 1982 default high-score table */
            uint16_t logo_f = sdd_families[FAM_UI_LOGO].first_frame;
            sdd_render_draw_frame_desc(logo_f, 112, 42, PAL_UI_LOGO, false);

            sdd_render_draw_frame_desc(
                (uint16_t)(sdd_families[FAM_CHR_PLAYER_1].first_frame + 27u),
                64, 96, PAL_CHR_PLAYER_1, false
            );
            sdd_render_draw_frame_desc(
                (uint16_t)(sdd_families[FAM_ENM_POOKA].first_frame + 25u),
                112, 96, PAL_ENM_POOKA, false
            );
            sdd_render_draw_frame_desc(
                (uint16_t)(sdd_families[FAM_ENM_FYGAR].first_frame + 25u),
                160, 96, PAL_ENM_FYGAR, true
            );

            mvs_fix_print(4u,  9u,  PAL_FIX_GOLD, "1982 ARCADE REPLICA EDITION");
            mvs_fix_print(7u,  15u, PAL_FIX_P1,   "TOP 5 DIGGERS");
            for (uint8_t i = 0u; i < 5u; ++i) {
                mvs_fix_print(7u, (uint8_t)(17u + i), PAL_FIX_TEXT, g_hiscores[i].initials);
                mvs_fix_print_u32(13u, (uint8_t)(17u + i), 8u, PAL_FIX_GOLD, g_hiscores[i].score);
            }
            mvs_fix_print(4u, 24u, PAL_FIX_P2,   "PRESS 1P OR 2P START");
            mvs_fix_print(3u, 26u, PAL_FIX_TEXT, "SELECT:COIN  START+SEL:VIEWER");

            sdd_render_draw_side_hud(g_game.score[0], g_game.score[1], 0u, false, 3u, 1u, g_game.credits);

            if (g_game.mode_timer > 0u) {
                --g_game.mode_timer;
            } else {
                enter_attract_demo();
            }
            break;
        }

        case GAME_MODE_ATTRACT: {
            /* Deterministic scripted attract demo: Taizo digs right, then pumps! */
            uint16_t script_held = 0u;
            uint16_t script_press = 0u;
            uint16_t elapsed = (uint16_t)(600u - g_game.mode_timer);
            if (elapsed < 90u) {
                script_held = INPUT_DOWN;
            } else if (elapsed < 160u) {
                script_held = INPUT_LEFT;
            } else if ((elapsed & 15u) == 0u) {
                script_held  = INPUT_BTN_A;
                script_press = INPUT_BTN_A;
            }
            (void)sdd_player_step(script_held, script_press);
            (void)sdd_pump_step(script_held, script_press);
            (void)sdd_rocks_step();
            uint32_t dummy = 0u;
            sdd_enemies_step(&dummy);

            sdd_render_playfield_and_actors();
            sdd_render_draw_side_hud(g_game.score[0], g_game.score[1], 0u, false, 3u, 1u, g_game.credits);
            mvs_fix_print(9u, 13u, PAL_FIX_GOLD, "GAME  OVER");
            mvs_fix_print(7u, 15u, PAL_FIX_P1,   "PRESS  START");

            if (g_game.mode_timer > 0u) {
                --g_game.mode_timer;
            } else {
                enter_title();
            }
            break;
        }

        case GAME_MODE_READY: {
            uint8_t p = g_game.active_player;
            sdd_render_playfield_and_actors();
            sdd_render_draw_side_hud(
                g_game.score[0], g_game.score[1], p, g_game.two_player,
                g_game.lives[p], g_game.round_num[p], g_game.credits
            );
            mvs_fix_print(8u, 13u, PAL_FIX_P1, (p == 0u) ? "PLAYER 1" : "PLAYER 2");
            mvs_fix_print(9u, 15u, PAL_FIX_GOLD, "READY!");

            if (g_game.mode_timer > 0u) {
                --g_game.mode_timer;
            } else {
                mvs_fix_clear_all();
                g_game.mode = GAME_MODE_PLAYING;
                sdd_audio_start_music(false);
            }
            break;
        }

        case GAME_MODE_PLAYING: {
            uint8_t  p   = g_game.active_player;
            uint16_t hld = g_input.held[p];
            uint16_t prs = g_input.pressed[p];

            /* Deterministic CPU0 -> CPU1 simulation step */
            uint32_t pts = 0u;
            pts += sdd_player_step(hld, prs);
            pts += sdd_pump_step(hld, prs);
            pts += sdd_rocks_step();
            sdd_enemies_step(&pts);
            award_session_points(pts);

            /* Update sample-locked YM2610 3-stem music: motion melody plays ONLY while Taizo moves! */
            sdd_audio_update_stems(true, g_player.moving, g_hurry_up);

            sdd_render_playfield_and_actors();
            sdd_render_draw_side_hud(
                g_game.score[0], g_game.score[1], p, g_game.two_player,
                g_game.lives[p], g_game.round_num[p], g_game.credits
            );

            /* Check Stage Clear (all monsters popped/crushed/escaped and no rock mid-fall) */
            if (g_player.state != PLAYER_DYING && g_player.state != PLAYER_DEAD &&
                g_player.state != PLAYER_CRUSHED &&
                sdd_actors_alive_enemy_count() == 0u && !sdd_actors_any_rock_busy()) {
                g_game.mode       = GAME_MODE_STAGE_CLEAR;
                g_game.mode_timer = 110u;
                sdd_audio_stop_all();
                sdd_audio_play_cue(AUDIO_STG_STAGE_CLEAR);
                break;
            }

            /* Check Player Death completion */
            if (g_player.state == PLAYER_DEAD) {
                sdd_audio_stop_all();
                if (g_game.lives[p] > 0u) {
                    --g_game.lives[p];
                }
                if (g_game.two_player) {
                    uint8_t other = (uint8_t)(p ^ 1u);
                    if (g_game.lives[other] > 0u) {
                        g_game.active_player = other;
                        start_player_round(true);
                        break;
                    }
                }
                if (g_game.lives[p] > 0u) {
                    start_player_round(false);
                } else {
                    sdd_score_register_final(g_game.score[p], (p == 0u) ? "P.1" : "P.2");
                    g_game.mode       = GAME_MODE_GAME_OVER;
                    g_game.mode_timer = 150u;
                    sdd_audio_play_cue(AUDIO_STG_GAME_OVER);
                }
            }
            break;
        }

        case GAME_MODE_STAGE_CLEAR: {
            uint8_t p = g_game.active_player;
            sdd_render_playfield_and_actors();
            sdd_render_draw_side_hud(
                g_game.score[0], g_game.score[1], p, g_game.two_player,
                g_game.lives[p], g_game.round_num[p], g_game.credits
            );
            mvs_fix_print(8u, 14u, PAL_FIX_GOLD, "ROUND CLEAR!");

            if (g_game.mode_timer > 0u) {
                --g_game.mode_timer;
            } else {
                ++g_game.round_num[p];
                start_player_round(true);
            }
            break;
        }

        case GAME_MODE_GAME_OVER: {
            uint8_t p = g_game.active_player;
            sdd_render_playfield_and_actors();
            sdd_render_draw_side_hud(
                g_game.score[0], g_game.score[1], p, g_game.two_player,
                0u, g_game.round_num[p], g_game.credits
            );
            mvs_fix_print(9u, 14u, PAL_FIX_DANGER, "GAME  OVER");

            if (g_game.mode_timer > 0u) {
                --g_game.mode_timer;
            } else {
                enter_title();
            }
            break;
        }

        default:
            break;
    }
}
