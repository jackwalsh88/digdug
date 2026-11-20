/*
 * Super Dig Dug — Playfield Grid, 4-Bit Quadrant Occupancy, and 1982 Round Layouts
 * Confirmed Screen Layout:
 *   - 224x224 px playfield (x=0..223, y=0..223)
 *   - 14x14 visual 16x16 tiles (tx=0..13, ty=0..13)
 *   - 28x28 logical 8x8 dirt cells (cx=0..27, cy=0..27)
 *   - Row ty=0 (cy=0..1): Open sky / surface escape lane (top-left exit at x=0, y=0)
 *   - Rows ty=1..13: 4 depth strata [3, 4, 3, 3]
 */
#ifndef SDD_WORLD_H
#define SDD_WORLD_H

#include <stdbool.h>
#include <stdint.h>

#define WORLD_TILES_W      14
#define WORLD_TILES_H      14
#define WORLD_CELLS_W      28
#define WORLD_CELLS_H      28

/* Player central start chamber (center of playfield: tile (6, 7) -> pixel (96, 112)) */
#define PLAYER_SPAWN_PX_X   96
#define PLAYER_SPAWN_PX_Y  112

/* Quadrant bit definitions inside each 16x16 tile (matching occupancy_v1_00..0f) */
#define QUAD_NW            0x01u
#define QUAD_NE            0x02u
#define QUAD_SW            0x04u
#define QUAD_SE            0x08u
#define QUAD_FULL          0x0Fu

typedef enum {
    ENEMY_KIND_POOKA = 0,
    ENEMY_KIND_FYGAR = 1,
} sdd_enemy_kind_t;

typedef struct {
    uint8_t tx;
    uint8_t ty;
    uint8_t len_tiles;
    uint8_t vertical;    /* 0 = horizontal tunnel, 1 = vertical tunnel */
} sdd_tunnel_span_t;

typedef struct {
    uint8_t tx;
    uint8_t ty;
    uint8_t kind;        /* sdd_enemy_kind_t */
    uint8_t tunnel_vertical;
    uint8_t tunnel_len;
} sdd_enemy_spawn_t;

typedef struct {
    uint8_t tx;
    uint8_t ty;
} sdd_rock_spawn_t;

typedef struct {
    uint8_t           enemy_count;
    uint8_t           rock_count;
    sdd_enemy_spawn_t enemies[8];
    sdd_rock_spawn_t  rocks[5];
} sdd_round_def_t;

typedef struct {
    /* 1 = solid dirt, 0 = excavated open space */
    uint8_t  cells[WORLD_CELLS_H][WORLD_CELLS_W];
    /* Cached 4-bit quadrant mask (0x00..0x0F) per 16x16 visual tile */
    uint8_t  tile_mask[WORLD_TILES_H][WORLD_TILES_W];
    uint16_t round_num;          /* 1..255 (wraps safely after 255 -> 240 loop) */
    uint8_t  rocks_dropped;      /* Counts rocks shattered this round (2 -> spawns bonus veggie!) */
    bool     veggie_spawned;
} sdd_world_t;

extern sdd_world_t g_world;

void    sdd_world_init_round(uint16_t round_num, sdd_round_def_t *out_def);
uint8_t sdd_world_stratum_for_y(int16_t py);
uint8_t sdd_world_palette_for_tile_row(uint8_t ty);

bool    sdd_world_cell_is_solid(int16_t cx, int16_t cy);
bool    sdd_world_tile_is_open(int16_t tx, int16_t ty);
uint8_t sdd_world_carve_cell(int16_t cx, int16_t cy);
uint8_t sdd_world_carve_footprint_16x16(int16_t px_top_left, int16_t py_top_left);
void    sdd_world_carve_tile_box(uint8_t tx, uint8_t ty, uint8_t w_tiles, uint8_t h_tiles);

#endif /* SDD_WORLD_H */
