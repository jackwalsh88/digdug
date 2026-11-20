# Next Steps & Active Work Order (`NEXT-STEPS.md`)

## Current Position

- **Repository State:** Bootstrapped in `/workspace` with authoritative docs (`docs/`), directory tree, baseline palette (`assets/palettes/metal_red_cyan_v1.json`), `Makefile` + `tools/sdd.py`, and tracking docs.
- **Confirmed Phase 1 Objective:** Ingest & disassemble the 1982 *Dig Dug* arcade Z80 ROM set (`digdug.zip` / `digdugat.zip` uploaded as Base64 `.txt` to avoid chat binary stripping), extract exact speeds/AI/pump/rock/round/scoring tables, and build a faithful **68000 Neo Geo MVS replica** on a **Horizontal `320×224` Side-Panel HUD + Adapted Height (`224×224` playfield + `96×224` side HUD)** layout with updated Neo Geo graphics (`B0`/`B1`), before expanding into Phase 2 (*Super Dig Dug*).
- **Active Gameplay Milestone:** **Phase 1 Disassembly & Spec** → **M0/M1/M2** (1982 *Dig Dug* MVS Replica) → **M3–M9** (*Super Dig Dug* 48 additions).
- **Active Art Batch:** **B0** (`tile_topsoil`, `prop_rocks`, `fx_dig`, `ui_font`) + **B1** (`chr_player_1`, `enm_pooka`, `enm_fygar`, `tool_standard_pump`, `fx_pump`, `fx_enemy_attacks`, `pick_rewards`, `ui_hud`).

---

## Concrete Next Tasks

### Track A — Sprite, Terrain & Bitplane Pipeline (`B0` → `B1`, fully runnable in this sandbox)
1. Implement zero-dependency indexed PNG + JSON reader/writer and Neo Geo palette word converter in `tools/assets/`.
2. Implement Neo Geo `16×16` C-ROM (`C1`/`C2`) and `8×8` S-ROM (`S1`) bitplane encoders + independent known-answer unit tests.
3. Implement `asset-check` validator (index 0 transparency, ≤16 colors/tile, stable pivots/hitboxes/sockets, terrain quadrant occupancy, `< 80` scanline strip calculator) and `asset-preview` (`1×` and `8×` nearest-neighbor contact sheets).
4. Author deterministic **B0** pixel masters (`ui_font`, `tile_topsoil` 16 occupancy masks + 3 solid variants + surface/bedrock, `prop_rocks`, `fx_dig`), generate review sheets in `assets/review/`, and visually inspect them.
5. Expand to **B1** masters (`chr_player_1`, `enm_pooka`, `enm_fygar`, `enm_mecha_pooka`, `tool_standard_pump`, `module_turbo_hose`, `fx_pump`, `fx_enemy_attacks`, `pick_rewards`, `ui_hud`) and emit C tables into `assets/generated/`.

### Track B — Gameplay Core & Native Neo Geo MVS Code (`M0` → `M1`)
1. Define the shared terrain occupancy & fixed-point math contracts (`src/world/`, `src/actors/`) with matching Python reference/binding tests so host unit tests run inside this container even without `gcc`.
2. Write the `ngdevkit`-compatible **M0 diagnostics ROM** & **MAME `art-viewer` ROM** C sources (`src/platform/neogeo/`, `src/render/`, `src/audio/`) plus linker/RAM budget script and isolated `mame/run_mame.sh` launcher.
3. Implement the **M1 digging sandbox** (`36×22` logical grid, smooth `Q12.4` 4-way movement/digging, dirty vertical terrain sprite strips, rock support/wobble/fall state machine) and verify edge cases via `python3 tools/sdd.py test`.

---

## Active Environment Blockers (Named Precisely per Handoff §1 & §13)

1. **`ngdevkit` (`m68k-neogeo-elf-gcc`, Z80 SDCC) and `mame` are not installed in this cloud sandbox**, and outbound access to package mirrors/GitHub is blocked (`HTTP 403`).
   - *Mitigation:* All C sources, headers, `ngdevkit` build rules, and `mame/run_mame.sh` scripts will be authored cleanly for target compilation, while distinguishing host-verified Python/asset/simulation outputs from local MAME hardware verification.
2. **External concept PNGs (`Armored Mecha-Pooka pixel sprite.png`, `Pixel Air Cannon Pickup.png`) are not yet in `assets/concepts/`.**
   - *Mitigation:* Author `enm_mecha_pooka` and `tool_air_cannon` from the detailed written briefs in `docs/Super-Dig-Dug-Coding-Agent-Sprite-Production.md`; user can supply the concept PNGs later if closer visual matching is desired.
