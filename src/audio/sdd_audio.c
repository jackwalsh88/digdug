/*
 * Super Dig Dug — 68000 Audio State & Movement-Linked Stem Controller
 * Keeps Z80 command bus traffic minimal by only sending stem-mask deltas.
 */
#include "sdd_audio.h"
#include "../platform/neogeo/neogeo_hw.h"

static uint8_t s_active_suite = 0xFFu;
static uint8_t s_stem_mask    = 0x00u;

void sdd_audio_init(void) {
    s_active_suite = 0xFFu;
    s_stem_mask    = 0x00u;
    mvs_snd_send(SND_CMD_SILENCE_ALL);
}

void sdd_audio_stop_all(void) {
    s_active_suite = 0xFFu;
    s_stem_mask    = 0x00u;
    mvs_snd_send(SND_CMD_SILENCE_ALL);
}

void sdd_audio_start_music(bool boss_suite) {
    uint8_t target = boss_suite ? SND_CMD_SUITE_BOSS : SND_CMD_SUITE_TOPSOIL;
    if (s_active_suite != target) {
        s_active_suite = target;
        s_stem_mask = STEM_BIT_GROOVE;
        mvs_snd_send(target);
    }
}

void sdd_audio_update_stems(bool groove_on, bool player_moving, bool danger_active) {
    uint8_t mask = 0u;
    if (groove_on)     mask |= STEM_BIT_GROOVE;
    if (player_moving) mask |= STEM_BIT_MOTION_MELODY;
    if (danger_active) mask |= STEM_BIT_DANGER_PERC;

    if (mask != s_stem_mask) {
        s_stem_mask = mask;
        mvs_snd_send((uint8_t)(SND_CMD_STEM_MASK_BASE | (mask & 0x07u)));
    }
}

void sdd_audio_play_cue(sdd_audio_cue_id_t cue) {
    if ((uint16_t)cue < SDD_AUDIO_CUE_COUNT) {
        mvs_snd_send((uint8_t)(SND_CMD_PLAY_CUE_BASE + (uint8_t)cue));
    }
}

uint8_t sdd_audio_current_stem_mask(void) {
    return s_stem_mask;
}
