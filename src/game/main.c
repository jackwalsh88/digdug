/*
 * Super Dig Dug — Cartridge 68000 Main Loop Entry Point
 */
#include "sdd_game.h"
#include "../platform/neogeo/neogeo_hw.h"

volatile uint32_t g_tick_counter = 0u; /* game ticks since boot (compare with g_vblank_counter) */

void sdd_cart_main(uint32_t bios_request) {
    (void)bios_request; /* 2 = demo, 3 = title after a coin: both open on the title */
    mvs_hw_init();

#ifdef SDD_ART_VIEWER_ONLY
    sdd_game_init(true);
#else
    sdd_game_init(false);
#endif

    for (;;) {
        ++g_tick_counter;
        mvs_wait_vblank();
        mvs_video_commit_vblank();
        mvs_poll_inputs();
        sdd_game_tick();
    }
}
