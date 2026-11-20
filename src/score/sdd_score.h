/*
 * Super Dig Dug — Authentic 1982 Scoring, Multi-Rock Crush, 18-Round Vegetables & High Scores
 */
#ifndef SDD_SCORE_H
#define SDD_SCORE_H

#include <stdbool.h>
#include <stdint.h>

#define EXTRA_LIFE_FIRST_PTS   20000u
#define EXTRA_LIFE_SECOND_PTS  60000u

typedef struct {
    char     initials[4];  /* e.g. "N.N" */
    uint32_t score;
} sdd_hiscore_entry_t;

extern sdd_hiscore_entry_t g_hiscores[5];
extern uint32_t            g_high_score;

void     sdd_score_init_defaults(void);
uint32_t sdd_score_for_pump_kill(uint8_t stratum, bool is_fygar, bool fygar_horizontal);
uint32_t sdd_score_for_rock_crush(uint8_t monsters_crushed);
uint32_t sdd_score_for_round_vegetable(uint16_t round_num, uint8_t *out_reward_frame_idx);

/* Adds points to player, updates HIGH SCORE, and returns number of extra lives earned (0..2) */
uint8_t  sdd_score_award(uint32_t *io_player_score, uint8_t *io_extra_life_flags, uint32_t pts);
void     sdd_score_register_final(uint32_t final_score, const char initials[4]);

#endif /* SDD_SCORE_H */
