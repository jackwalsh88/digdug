/*
 * Super Dig Dug — Playfield Grid, Excavation Masks, and Authentic 1982 Round Generator
 */
#include "sdd_world.h"
#include "../../assets/generated/sdd_assets.h"

sdd_world_t g_world;

static void recompute_tile_mask(uint8_t tx, uint8_t ty) {
    if (tx >= WORLD_TILES_W || ty >= WORLD_TILES_H) {
        return;
    }
    uint8_t cx = (uint8_t)(tx * 2u);
    uint8_t cy = (uint8_t)(ty * 2u);
    uint8_t mask = 0u;
    if (g_world.cells[cy][cx])         mask |= QUAD_NW;
    if (g_world.cells[cy][cx + 1u])    mask |= QUAD_NE;
    if (g_world.cells[cy + 1u][cx])    mask |= QUAD_SW;
    if (g_world.cells[cy + 1u][cx + 1u]) mask |= QUAD_SE;
    if (g_world.tile_mask[ty][tx] != mask) {
        g_world.tile_mask[ty][tx] = mask;
        g_world.dirty_cols |= (uint16_t)(1u << tx);
    }
}

static void recompute_all_masks(void) {
    for (uint8_t ty = 0u; ty < WORLD_TILES_H; ++ty) {
        for (uint8_t tx = 0u; tx < WORLD_TILES_W; ++tx) {
            recompute_tile_mask(tx, ty);
        }
    }
    g_world.dirty_cols = (uint16_t)((1u << WORLD_TILES_W) - 1u);
}

uint8_t sdd_world_stratum_for_y(int16_t py) {
    if (py < 64)  return 0u;  /* Surface + Dirt Layer 1 (ty = 0..3): 200 / 400 pts */
    if (py < 128) return 1u;  /* Dirt Layer 2 (ty = 4..7):           300 / 600 pts */
    if (py < 192) return 2u;  /* Dirt Layer 3 (ty = 8..11):          400 / 800 pts */
    return 3u;                /* Dirt Layer 4 (ty = 12..13):         500 / 1000 pts */
}

uint8_t sdd_world_palette_for_tile_row(uint8_t ty) {
    if (ty == 0u) return PAL_DD1982_SURFACE;
    if (ty <= 3u) return PAL_DD1982_STRATUM_0;
    if (ty <= 7u) return PAL_DD1982_STRATUM_1;
    if (ty <= 11u) return PAL_DD1982_STRATUM_2;
    return PAL_DD1982_STRATUM_3;
}

bool sdd_world_cell_is_solid(int16_t cx, int16_t cy) {
    if (cx < 0 || cx >= WORLD_CELLS_W || cy < 0 || cy >= WORLD_CELLS_H) {
        return false;
    }
    return g_world.cells[cy][cx] != 0u;
}

bool sdd_world_tile_is_open(int16_t tx, int16_t ty) {
    if (tx < 0 || tx >= WORLD_TILES_W || ty < 0 || ty >= WORLD_TILES_H) {
        return false;
    }
    return g_world.tile_mask[ty][tx] == 0u;
}

uint8_t sdd_world_carve_cell(int16_t cx, int16_t cy) {
    if (cx < 0 || cx >= WORLD_CELLS_W || cy < 0 || cy >= WORLD_CELLS_H) {
        return 0u;
    }
    if (g_world.cells[cy][cx] == 0u) {
        return 0u;
    }
    g_world.cells[cy][cx] = 0u;
    recompute_tile_mask((uint8_t)(cx >> 1), (uint8_t)(cy >> 1));
    return 1u;
}

/* Carves the 2x2 8x8 cells overlapped by a 16x16 digger body and returns newly dug cell count */
uint8_t sdd_world_carve_footprint_16x16(int16_t px_top_left, int16_t py_top_left) {
    uint8_t newly_dug = 0u;
    int16_t cx0 = (int16_t)((px_top_left + 2) >> 3);
    int16_t cx1 = (int16_t)((px_top_left + 13) >> 3);
    int16_t cy0 = (int16_t)((py_top_left + 2) >> 3);
    int16_t cy1 = (int16_t)((py_top_left + 13) >> 3);

    for (int16_t cy = cy0; cy <= cy1; ++cy) {
        for (int16_t cx = cx0; cx <= cx1; ++cx) {
            newly_dug = (uint8_t)(newly_dug + sdd_world_carve_cell(cx, cy));
        }
    }
    return newly_dug;
}

void sdd_world_carve_tile_box(uint8_t tx, uint8_t ty, uint8_t w_tiles, uint8_t h_tiles) {
    for (uint8_t dy = 0u; dy < h_tiles; ++dy) {
        for (uint8_t dx = 0u; dx < w_tiles; ++dx) {
            uint8_t x = (uint8_t)(tx + dx);
            uint8_t y = (uint8_t)(ty + dy);
            if (x < WORLD_TILES_W && y < WORLD_TILES_H) {
                g_world.cells[y * 2u][x * 2u]         = 0u;
                g_world.cells[y * 2u][x * 2u + 1u]    = 0u;
                g_world.cells[y * 2u + 1u][x * 2u]    = 0u;
                g_world.cells[y * 2u + 1u][x * 2u + 1u] = 0u;
                g_world.tile_mask[y][x] = 0u;
                g_world.dirty_cols |= (uint16_t)(1u << x);
            }
        }
    }
}

/* The original picks layout = round for rounds 1..15, then cycles 12..15. */
uint8_t sdd_world_layout_index(uint16_t round_num) {
    if (round_num == 0u) {
        round_num = 1u;
    }
    if (round_num >= 16u) {
        round_num = (uint16_t)((round_num & 3u) + 12u);
    }
    return (uint8_t)(round_num - 1u);
}

/* Speed tables are indexed by the round, clamped at 15. */
uint8_t sdd_world_round_step(void) {
    uint16_t r = g_world.round_num;
    if (r == 0u) {
        r = 1u;
    }
    if (r > DD82_ROUND_STEPS) {
        r = DD82_ROUND_STEPS;
    }
    return (uint8_t)(r - 1u);
}

void sdd_world_init_round(uint16_t round_num, sdd_round_def_t *out_def) {
    if (round_num == 0u) {
        round_num = 1u;
    }
    /* Safe Round 256+ wrap: loops rounds 13..20 cleanly with zero spawn-collision bug */
    if (round_num > 255u) {
        round_num = (uint16_t)(13u + ((round_num - 256u) & 7u));
    }

    g_world.round_num      = round_num;
    g_world.rocks_dropped  = 0u;
    g_world.veggie_spawned = false;

    /* Fill Row 0 (cy=0..1) as open sky/surface, Rows 1..13 (cy=2..27) as solid dirt */
    for (uint8_t cy = 0u; cy < WORLD_CELLS_H; ++cy) {
        uint8_t solid = (cy < 2u) ? 0u : 1u;
        for (uint8_t cx = 0u; cx < WORLD_CELLS_W; ++cx) {
            g_world.cells[cy][cx] = solid;
        }
    }

    /* Carve central entry shaft (tx=6, ty=0..7) and 3-tile central chamber (tx=5..7, ty=7) */
    sdd_world_carve_tile_box(6u, 0u, 1u, 8u);
    sdd_world_carve_tile_box(5u, 7u, 3u, 1u);

    sdd_round_def_t def = k_dd82_layouts[sdd_world_layout_index(round_num)];

    /* Carve the layout's pre-dug tunnels */
    for (uint8_t i = 0u; i < def.tunnel_count; ++i) {
        const sdd_tunnel_span_t *t = &def.tunnels[i];
        if (t->vertical) {
            sdd_world_carve_tile_box(t->tx, t->ty, 1u, t->len_tiles);
        } else {
            sdd_world_carve_tile_box(t->tx, t->ty, t->len_tiles, 1u);
        }
    }

    recompute_all_masks();
    if (out_def) {
        *out_def = def;
    }
}
