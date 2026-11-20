/*
 * Super Dig Dug — Cartridge 68000 Main Loop Entry Point
 */
#include "sdd_game.h"
#include "../platform/neogeo/neogeo_hw.h"

void sdd_cart_main(void) {
    mvs_hw_init();

#ifdef SDD_ART_VIEWER_ONLY
    sdd_game_init(true);
#else
    sdd_game_init(false);
#endif

    for (;;) {
        mvs_wait_vblank();
        mvs_video_commit_vblank();
        mvs_poll_inputs();
        sdd_game_tick();
    }
}
