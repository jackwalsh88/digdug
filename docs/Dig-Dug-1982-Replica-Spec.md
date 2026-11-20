# Phase 1 Specification — 1982 *Dig Dug* (Rev 2) Replica on Neo Geo MVS

**Authority:** Explicit user direction (Decision Precedence #1) + `Super-Dig-Dug-Neo-Geo-MVS-Handoff.md` + `Super-Dig-Dug-Coding-Agent-Sprite-Production.md`  
**Target Platform:** SNK Neo Geo MVS (`320×224`, 68000 @ 12 MHz + Z80/YM2610) inside MAME  
**Screen Layout:** **Horizontal `320×224` with Side-Panel HUD (`96×224`) + Adapted Height (`224×224` Playfield)**

---

## 1. Verified Source ROM Set Inventory (`digdug` — Namco 1982, Rev 2)

Confirmed from the user-supplied `digdug` archive directory listing (19 ROM/PROM chips):

| Chip Filename | Size | Original Hardware Region | Purpose in Disassembly / Reference |
|---|---:|---|---|
| `dd1a.1` – `dd1a.4` | 4 × 4,096 B (16 KiB) | CPU 0 (`$0000–$3FFF`) | Main Z80: game state machine, player movement/digging/pumping, stage setup, scoring, HUD |
| `dd1a.5` – `dd1a.6` | 2 × 4,096 B (8 KiB) | CPU 1 (`$0000–$1FFF`) | Sub Z80: Pooka & Fygar AI, ghost/eyeball phasing, fire-breath timing, rock triggers |
| `dd1.7` | 4,096 B (4 KiB) | CPU 2 (`$0000–$0FFF`) | Sound Z80: movement melody, danger speed-up cue, SFX sequencer, WSG register writes |
| `dd1.10b` | 4,096 B (4 KiB) | Stage Tilemap ROM | Initial dirt strata & carved starter tunnel layouts per round |
| `dd1.9` | 2,048 B (2 KiB) | `8×8` 1bpp FG Tiles | Original HUD glyphs / score font reference |
| `dd1.11` | 4,096 B (4 KiB) | `8×8` 2bpp BG Tiles | Original excavated dirt edge masks reference |
| `dd1.12` – `dd1.15` | 4 × 4,096 B (16 KiB) | `16×16` 2bpp Sprites | Original sprite pose counts & animation frame order reference |
| `136007.109` – `136007.110` | 2 × 256 B | Namco WSG PROMs | `8 × 32` 4-bit sound waveforms for authentic SFX/melody timbre reference |
| `136007.111` – `136007.112` | 2 × 256 B | Sprite & Tile CLUTs | Original strata color cycling across rounds |
| `136007.113` | 32 B | Master RGB PROM | 32-entry resistor-network RGB reference colors |

**Local Disassembly Workflow:**
Run `python3 tools/disasm_digdug1982.py /path/to/digdug.zip` (or `digdug_b64.txt`) locally to generate `build/disasm_1982/{cpu0_main.asm,cpu1_sub_ai.asm,cpu2_sound.asm,digdug1982_tables.json,rom_manifest.json}`. Raw 1982 ROM binaries are never committed or linked into the Neo Geo ROM.

---

## 2. Hardware Architecture Translation (Namco Galaga 3×Z80 → Neo Geo MVS)

| Subsystem | 1982 Namco Arcade Board | Neo Geo MVS Port Architecture |
|---|---|---|
| **CPUs** | 3 × Z80 @ 3.072 MHz interleaved across scanlines (`$8000–$9FFF` shared RAM) | Single deterministic **12 MHz 68000** simulation step (`cpu0` → `cpu1` update order per VBlank) + **Z80/YM2610** sound driver via command port |
| **Frame Rate** | `60.606 Hz` (`264` lines × `192` cycles) | `59.192 Hz` MVS NTSC VBlank (~2.3% cadence delta; speeds/timers preserved per-tick for crisp pixel step parity, or scaled cleanly via `Q12.4` fixed-point) |
| **Playfield Layer** | `36×28` `8×8` rotated tilemap (`224×288` TATE) | **14 vertical Neo Geo sprite strips** (`x = 0..223`, 16px wide each × 14 tiles tall) using generated 16-mask `16×16` C-ROM dirt tiles + updated early-1990s pixel art (`B0`/`B1`) |
| **HUD / Text** | Top row (`1UP / HIGH SCORE`) + bottom row (`lives / flowers`) on `8×8` FG layer | Right-hand **`96×224` (`12×28` `8×8` tiles) Neo Geo S-ROM FIX panel** (`x = 224..319`) |
| **Actors & FX** | Up to 64 `16×16` / `32×32` 2bpp hardware sprites | Neo Geo `16×16` 4bpp C-ROM sprite strips (`32×32` normal canvas, `48×48` inflated canvas; well under the `< 80` strips/scanline budget) |
| **Persistence** | ER2055 EAROM high-score table (`N.N / A.A / M.M / C.C / O.O` defaults) | MVS Backup RAM / soft-DIP high-score table (with identical 5-entry default table) |

---

## 3. Exact `320×224` Horizontal Side-HUD Playfield Mapping

Original 1982 *Dig Dug* uses a **`14 × 18` grid of `16×16` blocks** (`224 × 288` pixels):
- **Horizontal width (`224` px = `14` columns of `16×16` blocks = `28` `8×8` cells):** Fits on Neo Geo `320×224` **1:1 with zero horizontal scaling or cropping!**
  - Playfield occupies **`x = 0..223`** (`14` columns × `16` px).
  - Side HUD panel occupies **`x = 224..319`** (`96` px = `12` FIX `8×8` columns), separated by a crisp 2px brass/steel arcade bezel line.
- **Vertical height adaptation (`288` px → `224` px = `14` rows of `16×16` blocks = `28` `8×8` cells):**
  - Moving the top score row (`16` px) and bottom lives/flower row (`16` px) into the `96×224` Side HUD immediately recovers **`32` pixels** (`288 - 32 = 256` px = `16` rows: `1` sky/surface row + `15` dirt rows across 4 strata `[4, 4, 4, 3]`).
  - Adapting those `16` playfield rows to **`14` rows (`224` px)** trims just **2 dirt rows** across the 4 underground strata while preserving `16×16` tunnel spacing, `16`-pixel turn-grid snap centers, rock footprints, and pump reach 1:1:
    - **Row `0` (`y = 0..15`):** Surface / Sky / Top-Left Last-Enemy Escape Lane & Stage Flowers.
    - **Rows `1..3` (`y = 16..63`, 3 rows):** Dirt Layer 1 (Top Stratum — `200` / `400` pts).
    - **Rows `4..7` (`y = 64..127`, 4 rows):** Dirt Layer 2 (Upper-Mid Stratum — `300` / `600` pts).
    - **Rows `8..10` (`y = 128..175`, 3 rows):** Dirt Layer 3 (Lower-Mid Stratum — `400` / `800` pts).
    - **Rows `11..13` (`y = 176..223`, 3 rows):** Dirt Layer 4 (Bottom Stratum — `500` / `1000` pts).
  - Starter tunnels & rock/enemy coordinates from `dd1.10b` map deterministically from the 15-row dirt space (`0..14`) into the 13-row dirt space (`1..13`) while keeping center player spawn, horizontal columns (`0..13`), and relative rock-above-tunnel relationships intact.
  - **Seamless Phase 2 Bridge:** The `96×224` Side HUD panel already reserves clean slots below `ROUND` / `LIVES` for *Super Dig Dug*'s Pump Module icon, Special Weapon icon + ammo counter, and Pop Chain / Clean Clear badges.

---

## 4. Authentic 1982 Gameplay Rules & Extracted Tables

### 4.1 Player Movement, Turn Grid & Digging
- **Turn Grid Alignment:** Dig Dug moves along `16`-pixel corridor centerlines and can only execute 90° turns at aligned grid intersections (with small input cornering assist into the nearest intersection). Screen edges (`x=0`, `x=223`, `y=0`, `y=223`) clamp movement (no wrap-around).
- **Tunnel vs. Dig Speed:** Faster walk speed through cleared tunnels; reduced dig speed while carving intact `8×8` dirt cells; `+10` points awarded per newly dug dirt sub-cell.
- **Movement-Linked Music:** Yuriko Keino's signature walking melody advances only while the player is actively moving, pausing cleanly the instant movement stops.

### 4.2 Harpoon Pump, Inflation & Deflation
- **Thin-Dirt Reach:** Harpoon extends up to 2 tiles (`32` px) from Dig Dug and can pierce a thin (`≤ 4–8` px) dirt partition to latch onto an enemy in an adjacent pocket (intact thick soil blocks it).
- **Inflation Stages (`0` = normal, `1..3` = inflated/harmless, `4` = pop/kill):**
  - Tap pumping advances inflation faster than steady button holding.
  - Partially inflated enemies (`stages 1..3`) are immobilized and **harmless to walk through** (`pass-through rule`).
  - Releasing or breaking tether lets the monster deflate stage-by-stage back to `0` and resume pursuit.
- **Pump Kill Scoring (by Depth Stratum & Fygar Direction):**

| Underground Stratum | Pooka (Any Dir) / Fygar (Vertical) | Fygar (Horizontal — Left/Right) |
|---|---:|---:|
| Surface or Layer 1 (`y = 0..63`) | `200` | `400` |
| Layer 2 (`y = 64..127`) | `300` | `600` |
| Layer 3 (`y = 128..175`) | `400` | `800` |
| Layer 4 (`y = 176..223`) | `500` | `1,000` |

### 4.3 Rocks & Multi-Crush Scoring
- **States:** `SUPPORTED` → `HELD_BY_PLAYER` (undercut, **waits indefinitely** while Dig Dug remains directly underneath!) → `WOBBLE` (jitter telegraph once player clears) → `FALLING` (crushes enemies, ghosts, **and** Dig Dug; points still count even if Dig Dug is also crushed) → `SHATTER` (breaks at tunnel floor after falling ≥ 1 tunnel height) → `RETIRED`.
- **Rock Crush Score Table (per single rock drop):**

| Monsters Crushed | Points Awarded |
|---:|---:|
| 1 | `1,000` |
| 2 | `2,500` |
| 3 | `4,000` |
| 4 | `6,000` |
| 5 | `8,000` |
| 6 | `10,000` |
| 7 | `12,000` |
| 8 | `15,000` |

### 4.4 Bonus Vegetables / Prizes (Triggered After 2nd Rock Drop per Round)
Spawns at the central player start chamber after **2 rocks** have fallen in the current round; persists ~10 seconds (~600 ticks):

| Round(s) | Bonus Item | Points |
|---|---|---:|
| Round 1 | Carrot | `400` |
| Round 2 | Turnip | `600` |
| Round 3 | Mushroom | `800` |
| Rounds 4–5 | Cucumber / Zucchini | `1,000` |
| Rounds 6–7 | Eggplant | `2,000` |
| Rounds 8–9 | Green Pepper | `3,000` |
| Rounds 10–11 | Tomato | `4,000` |
| Rounds 12–13 | Garlic | `5,000` |
| Rounds 14–15 | Watermelon | `6,000` |
| Rounds 16–17 | Galaxian Flagship | `7,000` |
| Round 18+ | Pineapple | `8,000` |

### 4.5 Monster AI (Pooka, Fygar, Ghosting, Fire & Escape)
- **Pooka:** Slightly faster base tunnel speed than Fygar; chases along tunnels via Manhattan/intersection pathing; periodically enters **Ghost (eyeball) form** to drift straight through dirt toward an open tunnel near Dig Dug (lethal on contact, unpumpable in solid dirt, crushable by rocks).
- **Fygar:** Slightly slower than Pooka; shares tunnel chase & ghosting; periodically stops horizontally, **flashes/inhales as a clear telegraph**, and breathes a horizontal 3-tile flame (left or right only, never vertical; can singe through a thin dirt wall).
- **Hurry-Up & Last-Enemy Escape:**
  - When enemy count drops or round timer advances, danger fanfare plays and music/enemy tempo increases.
  - When **1 enemy remains**, it enters escape mode—heading upward (phasing if needed) to Row `0` (surface) and fleeing off the **top-left exit** (`x = 0, y = 0`). Escaping advances the round cleanly without awarding that monster's kill points.
- **Cabinet Defaults & Round 256 Policy:**
  - Default `3` starting lives; extra lives at `20,000` and `60,000` pts; alternating 1P/2P support in Phase 1 replica (expanding to simultaneous `#45` Co-op Rescue in Phase 2 M8).
  - Round counter wraps cleanly after Round 255 to loop high-round layouts without triggering the 1982 Round-0 Pooka-on-player softlock bug (toggleable in debug/classic flags if desired).
