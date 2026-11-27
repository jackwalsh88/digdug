/*
 * Super Dig Dug — Neo Geo MVS Playfield Strip, Actor Meta-Sprite & Side-HUD FIX Renderer
 */
#ifndef SDD_RENDER_H
#define SDD_RENDER_H

#include <stdbool.h>
#include <stdint.h>

void sdd_render_draw_side_hud(
    uint32_t p1_score,
    uint32_t p2_score,
    uint8_t  active_player,
    bool     two_player_game,
    uint8_t  lives_remaining,
    uint16_t round_num,
    uint8_t  credits
);

void sdd_render_playfield_and_actors(void);
void sdd_render_hide_playfield(void); /* title, viewer: hide the terrain layer */
void sdd_render_draw_frame_desc(uint16_t global_frame_idx, int16_t anchor_x, int16_t anchor_y, uint8_t pal_override, bool hflip);

#endif /* SDD_RENDER_H */
