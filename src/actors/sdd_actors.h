/*
 * Super Dig Dug — Phase 1 (1982 Replica) Deterministic Actor, Pump, Enemy & Rock State
 * Fixed-point coordinates: Q12.4 (16 units = 1 screen pixel; top-left of 16x16 logical body).
 */
#ifndef SDD_ACTORS_H
#define SDD_ACTORS_H

#include <stdbool.h>
#include <stdint.h>
#include "../world/sdd_world.h"

#define FP_SHIFT           4
#define FP_ONE_PX          16
#define FP_TILE_16         (16 * FP_ONE_PX)

#define MAX_ENEMIES        8u
#define MAX_ROCKS          5u
#define MAX_SCORE_POPUPS   4u

typedef enum {
    DIR_RIGHT = 0,
    DIR_UP    = 1,
    DIR_LEFT  = 2,
    DIR_DOWN  = 3,
} sdd_dir_t;

typedef enum {
    PLAYER_ALIVE   = 0,
    PLAYER_PUMPING = 1,
    PLAYER_CRUSHED = 2,
    PLAYER_DYING   = 3,
    PLAYER_DEAD    = 4,
} sdd_player_state_t;

typedef struct {
    bool     extending;
    bool     latched;
    sdd_dir_t dir;
    int16_t  length_px;        /* 0..32 px */
    uint8_t  target_enemy;     /* 0..MAX_ENEMIES-1 when latched */
    uint8_t  hold_timer;       /* ticks until next auto-pump when button held */
} sdd_harpoon_t;

typedef struct {
    int16_t            x_fp;   /* Q12.4 top-left of 16x16 logical body */
    int16_t            y_fp;
    sdd_dir_t          dir;
    sdd_player_state_t state;
    bool               moving;
    bool               digging;
    uint8_t            anim_tick;
    uint8_t            state_timer;
    sdd_harpoon_t      harpoon;
} sdd_player_t;

typedef enum {
    ENM_STATE_TUNNEL     = 0,
    ENM_STATE_GHOST      = 1,
    ENM_STATE_INHALE     = 2,  /* Fygar pre-fire telegraph */
    ENM_STATE_FIRE       = 3,  /* Fygar horizontal 3-tile flame */
    ENM_STATE_INFLATED   = 4,  /* inflate_stage 1..3 (harmless pass-through!) */
    ENM_STATE_POPPING    = 5,  /* inflate_stage 4 burst */
    ENM_STATE_ROCK_HELD  = 6,  /* dragged downward by falling rock */
    ENM_STATE_DEAD       = 7,
    ENM_STATE_ESCAPED    = 8,  /* Last enemy fled out top-left surface exit */
} sdd_enemy_state_t;

typedef struct {
    bool              active;
    sdd_enemy_kind_t  kind;
    sdd_enemy_state_t state;
    int16_t           x_fp;
    int16_t           y_fp;
    sdd_dir_t         dir;
    sdd_dir_t         horiz_facing; /* Last horizontal facing (DIR_LEFT or DIR_RIGHT) */
    uint8_t           inflate_stage;/* 0 = normal, 1..3 = harmless inflated, 4 = pop */
    uint8_t           deflate_timer;
    uint16_t          phase_cooldown;
    uint16_t          fire_cooldown;
    uint8_t           state_timer;
    uint8_t           anim_tick;
    uint8_t           crushing_rock;
    bool              escaping;
} sdd_enemy_t;

typedef enum {
    ROCK_SUPPORTED      = 0,
    ROCK_HELD_BY_PLAYER = 1,  /* Undercut, held indefinitely until player clears below! */
    ROCK_WOBBLE         = 2,
    ROCK_FALLING        = 3,
    ROCK_SHATTER        = 4,
    ROCK_RETIRED        = 5,
} sdd_rock_state_t;

typedef struct {
    bool             active;
    sdd_rock_state_t state;
    int16_t          x_fp;
    int16_t          y_fp;
    int16_t          fall_start_y_px;
    uint8_t          state_timer;
    uint8_t          crushed_count;
    bool             crushed_player;
} sdd_rock_t;

typedef struct {
    bool     active;
    int16_t  px;
    int16_t  py;
    uint16_t timer;            /* ~600 ticks (10 seconds) */
    uint8_t  reward_frame_idx;
    uint32_t points;
} sdd_bonus_veggie_t;

typedef struct {
    bool     active;
    int16_t  px;
    int16_t  py;
    uint32_t points;
    uint8_t  timer;
} sdd_score_popup_t;

extern sdd_player_t       g_player;
extern sdd_enemy_t        g_enemies[MAX_ENEMIES];
extern sdd_rock_t         g_rocks[MAX_ROCKS];
extern sdd_bonus_veggie_t g_veggie;
extern sdd_score_popup_t  g_popups[MAX_SCORE_POPUPS];
extern bool               g_hurry_up;
extern uint16_t           g_round_ticks;

void    sdd_actors_spawn_round(const sdd_round_def_t *def);
void    sdd_actors_respawn_positions(const sdd_round_def_t *def);
uint8_t sdd_actors_alive_enemy_count(void);
bool    sdd_actors_any_rock_busy(void);
void    sdd_spawn_score_popup(int16_t px, int16_t py, uint32_t pts);

/* Per-frame deterministic update steps (called in exact 1982 CPU0 -> CPU1 order) */
uint32_t sdd_player_step(uint16_t p_held, uint16_t p_pressed);
uint32_t sdd_pump_step(uint16_t p_held, uint16_t p_pressed);
uint32_t sdd_rocks_step(void);
void     sdd_enemies_step(uint32_t *io_awarded_pts);

#endif /* SDD_ACTORS_H */
