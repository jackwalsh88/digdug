# Next Steps (`NEXT-STEPS.md`)

## Current position (2026-11-27)

- Latest bootable revision: branch `claude/admiring-bohr-c8n1oq`.
- Phase 1 (1982 *Dig Dug* replica on MVS) builds with ngdevkit and runs in MAME 0.264 under nullbios with the real art and audio pack. See `TEST-REPORT.md` §0 for evidence and `MAME-SETUP.md` for the exact procedure.
- Handoff gates: M0 is met except for the items left unchecked in `MAME-SETUP.md` §6; M1 (digging sandbox) behaviour is present inside the Phase 1 loop but has not been reviewed against its pass criteria one by one.

## To resume in a fresh environment

```sh
sudo tools/setup_linux.sh
# place the asset pack at ./Super-Dig-Dug-Art (Drive: digdug/Super-Dig-Dug-Art; only
# Assets/*/*/atlas.{png,json}, palette.json and Audio/**/*.wav are needed)
make assets && make rom && make bios
make test && make smoke SCENARIO=play
```

## Next concrete tasks, in order

1. **Owner play-test** of `mame/roms/superdigdug.zip` (interactive `make run`), ideally also under a real MVS BIOS, and feedback on feel.
2. **Fidelity pass against the 1982 original — in progress.** Done from the ROM (`digdug.zip`, Drive folder `digdug`, git-ignored): the 15 round layouts, layout selection, strata, player and monster speed model (`docs/Dig-Dug-1982-Replica-Spec.md` Appendix A). Remaining: pump and harpoon timing, deflation, rock wobble/fall, Fygar fire, ghost behaviour, hurry-up, the speed-tier flags. These are best measured on the running original; MAME's `digdug` driver additionally needs `namco51.zip` and `namco53.zip` (device ROMs `51xx.bin`, `53xx.bin`). Without them, continue by static analysis of `build/disasm_1982/`.
3. **Finish M0/M1 evidence:** P2 inputs and 2P start in MAME; hard reset; high-score table in the backup-RAM block; stack watermark; target-side worst-case strip count instead of the pipeline estimate.
4. **Presentation polish for Phase 1:** title layout (logo is 256 px wide on a 224 px playfield), round-flower and lives icons, death/pop animation frames, art-viewer tick cost.
5. **Phase 2, milestone M2:** #01 Mecha-Pooka (extra inflation stage), #22 Turbo Hose, first #48 warning poses; then M3 (#11 Air Cannon, #17 Dig Bomb, #40 Technique Bonus, equipment select).

## Open decisions for the owner

- Whether to commit the ~7 MB asset subset (atlases, JSON, WAVs) to the repository so builds do not depend on Drive.
- Provide `namco51.zip` and `namco53.zip` so the original can be run in MAME for timing measurements (optional; static analysis is the fallback).
- Confirm the vertical adaptation in D-22 (keep original rows 3..15) or choose the alternative.
