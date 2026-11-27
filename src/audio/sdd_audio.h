/*
 * Super Dig Dug — 68000 -> Z80/YM2610 Audio Command & Sample-Locked Stem Mixer Interface
 */
#ifndef SDD_AUDIO_H
#define SDD_AUDIO_H

#include <stdbool.h>
#include <stdint.h>
#include "../../assets/generated/sdd_assets.h"

/* Z80 Command Byte Protocol (written to REG_SOUND $320000) */
#define SND_CMD_RESET_DRIVER     0x03u   /* BIOS-defined: restart the Z80 driver */
#define SND_CMD_SILENCE_ALL      0x07u
#define SND_CMD_SUITE_TOPSOIL    0x10u
#define SND_CMD_SUITE_BOSS       0x11u
#define SND_CMD_STEM_MASK_BASE   0x20u   /* 0x20 | (danger<<2 | moving<<1 | groove) */
#define SND_CMD_PLAY_CUE_BASE    0x80u   /* 0x80 + sdd_audio_cue_id_t (0..50) */

#define STEM_BIT_GROOVE          0x01u
#define STEM_BIT_MOTION_MELODY   0x02u
#define STEM_BIT_DANGER_PERC     0x04u

void sdd_audio_init(void);
void sdd_audio_stop_all(void);
void sdd_audio_start_music(bool boss_suite);
void sdd_audio_update_stems(bool groove_on, bool player_moving, bool danger_active);
void sdd_audio_play_cue(sdd_audio_cue_id_t cue);

uint8_t sdd_audio_current_stem_mask(void);

#endif /* SDD_AUDIO_H */
