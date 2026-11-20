/*
 * Super Dig Dug — Authentic 1982 Scoring & High-Score Implementation
 */
#include "sdd_score.h"

sdd_hiscore_entry_t g_hiscores[5];
uint32_t            g_high_score = 10000u;

/* Base pump pop points by stratum 0..3; doubled when popping Fygar horizontally! */
static const uint16_t k_pump_base_pts[4] = { 200u, 300u, 400u, 500u };

/* Single-rock crush score table for 1..8 monsters crushed */
static const uint16_t k_rock_crush_pts[9] = {
    0u, 1000u, 2500u, 4000u, 6000u, 8000u, 10000u, 12000u, 15000u
};

void sdd_score_init_defaults(void) {
    static const char k_names[5][4] = { "N.N", "A.A", "M.M", "C.C", "O.O" };
    static const uint32_t k_vals[5] = { 10000u, 8000u, 6000u, 4000u, 2000u };
    for (uint8_t i = 0u; i < 5u; ++i) {
        g_hiscores[i].initials[0] = k_names[i][0];
        g_hiscores[i].initials[1] = k_names[i][1];
        g_hiscores[i].initials[2] = k_names[i][2];
        g_hiscores[i].initials[3] = '\0';
        g_hiscores[i].score = k_vals[i];
    }
    g_high_score = g_hiscores[0].score;
}

uint32_t sdd_score_for_pump_kill(uint8_t stratum, bool is_fygar, bool fygar_horizontal) {
    if (stratum > 3u) {
        stratum = 3u;
    }
    uint32_t pts = k_pump_base_pts[stratum];
    if (is_fygar && fygar_horizontal) {
        pts *= 2u;
    }
    return pts;
}

uint32_t sdd_score_for_rock_crush(uint8_t monsters_crushed) {
    if (monsters_crushed == 0u) {
        return 0u;
    }
    if (monsters_crushed > 8u) {
        monsters_crushed = 8u;
    }
    return k_rock_crush_pts[monsters_crushed];
}

/*
 * Exact 1982 18-round bonus vegetable point progression:
 *   R1=400, R2=600, R3=800, R4-5=1000, R6-7=2000, R8-9=3000,
 *   R10-11=4000, R12-13=5000, R14-15=6000, R16-17=7000, R18+=8000
 */
uint32_t sdd_score_for_round_vegetable(uint16_t round_num, uint8_t *out_reward_frame_idx) {
    uint32_t pts;
    uint8_t  frame_idx;

    if (round_num <= 1u)      { pts = 400u;  frame_idx = 0u; /* carrot */ }
    else if (round_num == 2u) { pts = 600u;  frame_idx = 1u; /* turnip */ }
    else if (round_num == 3u) { pts = 800u;  frame_idx = 2u; /* radish/mushroom slot */ }
    else if (round_num <= 5u) { pts = 1000u; frame_idx = 2u; }
    else if (round_num <= 7u) { pts = 2000u; frame_idx = 3u; }
    else if (round_num <= 9u) { pts = 3000u; frame_idx = 3u; }
    else if (round_num <= 11u){ pts = 4000u; frame_idx = 4u; }
    else if (round_num <= 13u){ pts = 5000u; frame_idx = 4u; }
    else if (round_num <= 15u){ pts = 6000u; frame_idx = 5u; }
    else if (round_num <= 17u){ pts = 7000u; frame_idx = 5u; }
    else                      { pts = 8000u; frame_idx = 5u; /* pineapple */ }

    if (out_reward_frame_idx) {
        *out_reward_frame_idx = frame_idx;
    }
    return pts;
}

uint8_t sdd_score_award(uint32_t *io_player_score, uint8_t *io_extra_life_flags, uint32_t pts) {
    uint8_t earned = 0u;
    uint32_t next = *io_player_score + pts;
    if (next > 9999990u) {
        next = 9999990u;
    }
    *io_player_score = next;
    if (next > g_high_score) {
        g_high_score = next;
    }

    if ((*io_extra_life_flags & 0x01u) == 0u && next >= EXTRA_LIFE_FIRST_PTS) {
        *io_extra_life_flags |= 0x01u;
        ++earned;
    }
    if ((*io_extra_life_flags & 0x02u) == 0u && next >= EXTRA_LIFE_SECOND_PTS) {
        *io_extra_life_flags |= 0x02u;
        ++earned;
    }
    return earned;
}

void sdd_score_register_final(uint32_t final_score, const char initials[4]) {
    for (uint8_t i = 0u; i < 5u; ++i) {
        if (final_score >= g_hiscores[i].score) {
            for (int j = 4; j > (int)i; --j) {
                g_hiscores[j] = g_hiscores[j - 1];
            }
            g_hiscores[i].initials[0] = initials ? initials[0] : 'P';
            g_hiscores[i].initials[1] = initials ? initials[1] : '.';
            g_hiscores[i].initials[2] = initials ? initials[2] : '1';
            g_hiscores[i].initials[3] = '\0';
            g_hiscores[i].score = final_score;
            g_high_score = g_hiscores[0].score;
            return;
        }
    }
}
