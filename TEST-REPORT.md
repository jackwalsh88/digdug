# Verification & Test Report (`TEST-REPORT.md`)

## 0. MAME verification — 2026-11-27 (latest)

Environment: Ubuntu 24.04 container, MAME 0.264, `m68k-neogeo-elf-gcc` 15.3.0, ngdevkit 0.5, nullbios 0.5, real asset pack (65 atlases, 53 WAVs fetched from Drive). Runs are headless (`tools/mame_smoke.py`, `-video none`); evidence is PNG snapshots, memory peeks and a WAV capture under `build/smoke/`.

| Scenario | Result |
|---|---|
| `boot` | Title with logo, cast and high-score table; attract demo with terrain, rocks, enemies. |
| `play` | Coin: BIOS credits 0 → 1, `BIOS_USER_MODE` 1. Start: credits 1 → 0, `BIOS_USER_MODE` 2, READY, play. Digging scores, pump harpoon, inflation, deaths and respawn observed in snapshots. |
| `play` timing | 598 game ticks in 600 VBlanks during play; 8 overrun VBlanks in the first 1,500 frames, all at screen transitions. |
| `viewer` | Opens from the title with P1 SELECT; family/frame browsing, 16-mask terrain grid, cue audition. Runs at roughly half rate (diagnostics redraw every tick). |
| `soak` | 18,000 frames (five emulated minutes) of scripted play with repeated coins and starts: no CPU exception, no hang; several full games through game over and high-score entry. Restarts seen in the VBlank counter are the BIOS's coin restart (USER request 3), not watchdog resets. |
| Audio | MAME output cross-correlates 0.998 with the source `Stingers/title.wav` (0.25 s window, replay rate 18,518.5 Hz). |

Measured sizes: 68000 program 58,168 bytes of 512 KiB; `.data` + `.bss` 17,140 bytes of the 56 KiB RAM region; V1 912 KiB of 1 MiB; C1/C2 50% of one 1 MiB pair. The `budgets` RAM and scanline figures remain estimates from the asset pipeline, not target measurements.

Defects fixed on the way to this result: crt0 did not assemble (unprefixed registers); `memcpy` was missing; the tick took about three frames (per-strip scanline telemetry and full terrain/HUD redraws); the Z80 driver never enabled NMI; the ADPCM-A tables did not match the YM2610; the TEST input was read from the RTC bit; title text assumed FIX row r is at y = 8r (it is 8(r − 2)).

Known limitations: not run under a commercial BIOS; P2 controls and 2P start not exercised in MAME; hard reset and the test switch not exercised; gameplay values are the prior session's estimates and have not been compared with the 1982 original; a coin on the title resets the RAM high-score table; music stems restart on a polled end flag, so a loop seam of a few milliseconds is possible; stack depth is not instrumented.

Sections below are the earlier host-only report from the previous session, kept for history.

## 1. Environment Audit

Probed via `python3 tools/sdd.py status` inside the Ubuntu 24.04 (`x86_64`) cloud container:

| Tool / Dependency | Status | Observed Version / Notes |
|---|---|---|
| `python3` | **Present** | Python `3.12.3` (`numpy`, `pandas`, `pyyaml` pre-installed) |
| `git` | **Present** | `git version 2.43.0` |
| `make` | **Missing in container** | `python3 tools/sdd.py <cmd>` provides 1:1 target parity; `Makefile` ready for macOS/Linux |
| `gcc` / `clang` | **Missing in container** | `tools/sdd.py test` auto-compiles & runs `tests/c_test_phase1.c` when `gcc`/`clang` is present on macOS/Linux |
| `m68k-neogeo-elf-gcc` / `m68k-elf-gcc` | **Missing in container** | Required locally to link `0482-p1.p1` (`brew install m68k-elf-gcc` or `ngdevkit`) |
| Z80 M1 Sound Assembler | **Built-in (`tools/build_m1_z80.py`)** | Emits verified `128 KB` `m1.bin` directly from Python (no external SDCC install required!) |
| `mame` | **Missing in container** | Required locally for Gate `M0`/`M1` runtime boot verification (see `MAME-SETUP.md`) |

---

## 2. Verified Automated Test & Hardware Budget Results (Executed in Container)

All host checks below were executed and **PASSED (`exit code 0`)**:

1. **`python3 tools/sdd.py assets` & `python3 tools/sdd.py asset-check` — PASS**
   - **Families / Frames:** `65` families, `2,074` native frames, `335` animation clips (`0` broken references).
   - **C-ROM (`C1`/`C2`):** `8,203` `16×16` 4bpp tiles (`512 KB` C1 + `512 KB` C2 = **`50.07%`** of a single `1 MB` C1/C2 pair) — **100% passed independent bitplane round-trip decode** (right `8×16` half first, LSB = leftmost pixel).
   - **S-ROM (`S1`):** `512` `8×8` 4bpp FIX tiles (`16 KB` S1 = **`12.5%`** of `4,096` tiles) — **100% passed independent column-pair `(4,5),(6,7),(0,1),(2,3)` round-trip decode**.
   - **Terrain Masks:** All **`336`** quadrant occupancy tiles (`7` biomes × `3` variants × `16` masks) verified for exact `NW/NE/SW/SE` quadrant solidity/transparency; all **`22`** intentional blank frames accounted for (`0` accidental blank frames).
   - **Palette RAM (`256 × 16` words):** Entry `0` (`$8000` reference black/transparent) verified across all `256` palettes; `$401FFE` backdrop verified `$8000`.
   - **V-ROM (`V1` YM2610 ADPCM-A):** All **`51`** runtime cues (`6` music stems + `36` SFX + `9` stingers) verified `256`-byte page aligned (`134 KB` stand-in V1; `~1–2 MB` with real WAV pack).
   - **Approval Status Honesty:** Stand-in build marked `standin_placeholder`; real pack build marked `imported_unreviewed` until visual review in MAME.

2. **`python3 tools/sdd.py asset-preview` — PASS**
   - Generated and visually inspected `1×` and `8×` decoded hardware preview sheets in `assets/review/`:
     - `phase1_core_sheet_{1x,8x}.png`
     - `topsoil_4strata_masks_{1x,8x}.png`
     - `fix_font_and_hud_{1x,8x}.png`

3. **`python3 tools/sdd.py budgets` — PASS**
   - **68000 Work RAM Estimate:** `41,536` / `62,208` user bytes (`66.77%`), leaving `> 20 KB` safety margin below BIOS `$10F300`.
   - **Worst-Case Scanline Sprite Strips:** **`58` strips/scanline** (`14` playfield terrain strips + `0` Side-HUD FIX strips + actors/projectiles/bosses) — well within the **`84`-strip engineering ceiling** (`96` hardware max).

4. **`python3 tools/sdd.py test` — `17 / 17` Unit & Simulation Tests PASS (`0.64s`)**
   - `test_z80_disasm.py` (`4` tests): Z80 unprefixed/CB/ED/DD/FD disassembly, relative labels, Namco WSG & RGB PROM decoders.
   - `test_asset_pipeline.py` (`7` tests): PNG RGBA/Indexed round-trip, Neo Geo palette words, `C1`/`C2` bit order, `S1` column-pair order, multi-palette scene partitioning, YM2610 ADPCM-A correlation, and synthetic `Super-Dig-Dug-Complete-Asset-Pack.zip` ingestion.
   - `test_phase1_digdug1982.py` (`6` tests): `16` quadrant excavation masks & `+10`pt digging, tap vs hold pumping, harmless inflated pass-through & deflation decay, stratum & `2×` horizontal Fygar scoring, `1..8` monster multi-crush table, indefinite player rock-hold, `2`-rock bonus vegetable spawn (`400..8,000` pts), last-enemy surface escape to `(0, 0)`, safe Round `256+` wrap, Z80 `m1.bin` cue-table verification, and C99 asset symbol cross-check.

---

## 3. Pending Target Hardware / MAME Verification (Local Mac Workstation)

- **68000 Cartridge Link (`make art-viewer`, `make rom`):** C99 & 68000 assembly sources (`src/**`) and Z80 `m1.bin` builder are complete; linking `0482-p1.p1` awaits running `make rom` on a machine with `m68k-elf-gcc` or `ngdevkit`.
- **MAME Execution (`make run`):** **NOT YET EXECUTED IN MAME** (`0` emulated frames in cloud container). Run locally on macOS per `MAME-SETUP.md` to certify Gates `M0`, `B0/B1`, and Phase 1 replica sign-off.
