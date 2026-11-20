# Verification & Test Report (`TEST-REPORT.md`)

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
