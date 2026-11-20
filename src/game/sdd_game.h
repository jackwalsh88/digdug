/*
 * Super Dig Dug — Phase 1 Game Loop & B0/M0 Art/Hardware Diagnostics Viewer Interface
 */
#ifndef SDD_GAME_H
#define SDD_GAME_H

#include <stdbool.h>
#include <stdint.h>

typedef enum {
    GAME_MODE_TITLE       = 0,
    GAME_MODE_ATTRACT     = 1,
    GAME_MODE_READY       = 2,
    GAME_MODE_PLAYING     = 3,
    GAME_MODE_STAGE_CLEAR = 4,
    GAME_MODE_GAME_OVER   = 5,
    GAME_MODE_ART_VIEWER  = 6,
} sdd_game_mode_t;

typedef struct {
    sdd_game_mode_t mode;
    uint16_t        mode_timer;
    uint8_t         credits;
    bool            two_player;
    uint8_t         active_player;   /* 0 = P1, 1 = P2 */
    uint32_t        score[2];
    uint8_t         lives[2];
    uint8_t         extra_flags[2];
    uint16_t        round_num[2];
} sdd_game_session_t;

extern sdd_game_session_t g_game;

void sdd_game_init(bool boot_into_viewer);
void sdd_game_tick(void);

/* Art & Hardware Diagnostics Viewer (B0 / M0) */
void sdd_art_viewer_init(void);
bool sdd_art_viewer_tick_and_render(void); /* Returns true if user requested exit to Title */

/* Cartridge 68000 C entry point called by crt0_mvs.S */
void sdd_cart_main(void);

#endif /* SDD_GAME_H */
