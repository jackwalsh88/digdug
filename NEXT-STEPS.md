# Next Steps & Active Work Order (`NEXT-STEPS.md`)

## Current Position

- **Phase 1 (1982 *Dig Dug* Replica on Neo Geo MVS) + Complete 65-Family Asset & Audio Pipeline: COMPLETE IN SOURCE & HOST-VERIFIED (`17/17` tests passing)**
  - Dual-mode asset & YM2610 ADPCM-A audio compiler (`tools/assets/pack_pipeline.py`) compiles all **65** families (`2,074` frames → `8,203` C-ROM tiles, `512` S-ROM tiles) and **51** runtime audio cues (`134 KB` stand-in / `Super-Dig-Dug-Complete-Asset-Pack.zip` ready via `make assets PACK=...`).
  - Zero-dependency Z80 + YM2610 M1 sound driver (`tools/build_m1_z80.py` + `src/audio/z80_driver.asm`) builds `128 KB` `build/m1.bin` with sample-locked 3-stem music (`groove` + movement-linked `melody` + `danger` percussion) and 3-channel SFX.
  - Portable C99 Neo Geo MVS platform layer (`src/platform/neogeo/`), M0/B0 Art & Hardware Diagnostics Viewer (`src/game/art_viewer.c`), and Phase 1 1982 *Dig Dug (Rev. 2)* engine (`src/{world,score,actors,combat,render,game}/`) are implemented for the confirmed **Horizontal `320×224` (`224×224` playfield + `96×224` FIX Side-HUD)** layout.

---

## Immediate Local Verification on macOS (Phase 1 Sign-Off)

1. Install 68000 cross-compiler & MAME via Homebrew (if not already installed):
   ```sh
   brew install m68k-elf-gcc mame
   ```
2. Pack your real 150 MB asset archive, run native C99 + Python tests, build the MVS cartridge, and launch in MAME:
   ```sh
   make assets PACK=/path/to/Super-Dig-Dug-Complete-Asset-Pack.zip
   make asset-check
   make test
   make rom
   NEOGEO_BIOS_DIR=/path/to/dir_containing_neogeo_zip make run
   ```
   *(Tip: Press `START + SELECT` at any time in-game—or build `make art-viewer`—to open the M0/B0 Art & Hardware Diagnostics Viewer and inspect all 65 real sprite families and V-ROM audio cues inside MAME!)*

---

## Phase 2 Roadmap — Expanding *Dig Dug* into *Super Dig Dug* (48 Additions)

Once Phase 1 boots and plays to your satisfaction in MAME, we proceed milestone-by-milestone across the already-packed 65-family asset catalog:
1. **Milestone `M2` (`#01` Mecha-Pooka, `#22` Turbo Hose, `#48` Expanded Combat Animation)**
2. **Milestone `M3` (`#11` Air Cannon, `#17` Dig Bomb, `#40` Technique Bonus, Pre-Zone Equipment Select)**
3. **Milestone `M4` (Mid-tier enemies `#02, #03, #04, #07, #09`, `#18` Remote Charge, `#20` Decoy Turnip, `#23` Long Tom, `#35–#37` Pickups, `#39` Pop Chain, `#41` Clean Clear, `#43–#44` Bonus Stages)**
4. **Milestone `M5` (Advanced enemies `#05, #06, #08, #10` & tools/traps `#12–#16, #19, #21, #24`)**
5. **Milestone `M6–M7` (6 New Worlds `#25–#30`, 4 Bosses `#31–#34`, `#38` Bonus Balloon, `#42` Garden Panic, `#46` Boss Rush, `#47` Reactive Boss Music)**
6. **Milestone `M8–M9` (`#45` Simultaneous 2P Co-op Rescue & Final Balance/Soak Sign-Off)**
