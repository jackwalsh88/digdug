# Architectural & Production Decisions (`DECISIONS.md`)

Records confirmed constraints from the specifications alongside reversible engineering choices and environment adaptations.

---

## 1. Locked Platform & Gameplay Rules (Authority: Handoff §1–§3)

- **Target Hardware:** Standard SNK Neo Geo MVS (`320×224`, 12 MHz 68000, Z80 + YM2610, 64 KiB Work RAM, 96 sprite strips/scanline hardware max, 80 strips/scanline working ceiling).
- **Controls & Loadout:** 4-way movement/digging, Button `A` = unlimited pump (with 1 pre-zone pump module), Button `B` = finite-ammo special (1 pre-zone tool or bomb). No in-combat inventory switching.
- **Universal Solvability:** Every normal enemy and boss encounter must remain completable using movement, digging, standard pumping, and rocks after special ammo is exhausted.

---

## 2. Reversible Working Defaults

| ID | Area | Decision / Working Default | Rationale & Reversibility |
|---|---|---|---|
| **D-01** | Arena Geometry | Playfield `288×176` at screen `(x=16, y=32)`: `18×11` visual `16×16` tiles = `36×22` logical `8×8` occupancy cells. Top `32px` (`y=0..31`) reserved for HUD + surface strip; `16px` left/right side margins. | Matches Handoff §5 provisional layout; requires only **18 vertical sprite strips** for the entire dirt playfield, leaving 62 strips within the 80-strip budget for actors, rocks, bosses, and FX. Tunable after M2/M8 density checks. |
| **D-02** | Fixed-Point Coordinates | World positions use signed `Q12.4` (`1/16` pixel subpixel precision, `int16_t`) relative to screen top-left. | Fits cleanly in 16-bit 68000 registers without overflow across `320×224`, supports smooth tunnel vs. dig speeds, and serializes identically on host and 68000. |
| **D-03** | Frame Timing & Authoring Ticks | Simulation runs at 1 tick per VBlank (`~59.1921 Hz` MVS NTSC, `~16.894 ms/tick`). Offline animation converter maps milliseconds to integer ticks via `max(1, round(ms * 59.1921 / 1000.0))`. | Satisfies Handoff §6 and Sprite Guide §2B ("do not assume exactly 60 Hz"). |
| **D-04** | Shared Terrain Mask Contract | Each `16×16` visual tile encodes filled `8×8` quadrants as `bit0=TL`, `bit1=TR`, `bit2=BL`, `bit3=BR` (`0`=empty tunnel, `15`=solid earth). Generated into a single shared header/module consumed by both Python asset tools and C runtime. | Eliminates any drift between collision occupancy and visual dirt tiles (Sprite Guide §3). |
| **D-05** | Same-Frame Precedence | Within a frame: (1) terrain edits & rock support checks, (2) rock crush / blast / projectile hits, (3) pump pop resolution. First lethal cause in priority order commits death and awards score once (with combined technique flags attached prior to commit). Simultaneous last-enemy death and player death resolves player death first (stage does not clear if no live player remains). | Explicit deterministic rule required by Handoff §6; covered by host unit tests. |
| **D-06** | Editable Pixel Master Fallback | Because `aseprite` is not installed in the current build container, canonical editable masters are stored as deterministic Python pixel-construction scripts + native indexed PNG sheets + JSON metadata (`canvas`, `pivot`, `hitbox`, `duration_ticks`, `sockets`, `animations`). No fake `.aseprite` files are created. | Explicitly permitted and prescribed by Sprite Guide §2A. |
| **D-07** | Zero-Dependency PNG & Bitplane Tooling | Asset scripts in `tools/assets/` use Python 3.12 standard library (`zlib`, `struct`, `json`) + `numpy` to read/write exact `PLTE`/`tRNS` 4bpp/8bpp indexed PNGs and encode/decode Neo Geo C-ROM (`C1`/`C2`) and S-ROM (`S1`) tiles without requiring Pillow or external network installs. | Keeps the asset pipeline 100% deterministic, self-contained, and runnable inside air-gapped containers. |
| **D-08** | Neo Geo Palette Word Conversion | Editable RGB888 colors convert to 16-bit Neo Geo palette RAM words (`bit15` dark bit, `bits14..12` R0/G0/B0 LSBs, `bits11..8` R4..R1, `bits7..4` G4..G1, `bits3..0` B4..B1) via a dedicated tested encoder/decoder in `tools/assets/`. | Prevents assuming standard packed RGB555 order (Sprite Guide §4). |
| **D-09** | Missing Concept PNG Handling | `Armored Mecha-Pooka pixel sprite.png` and `Pixel Air Cannon Pickup.png` are not yet present in `assets/concepts/`. Initial `enm_mecha_pooka` and `tool_air_cannon` pixel masters follow the written visual briefs; user review will confirm or supply the PNGs if closer visual matching is desired. | Follows Sprite Guide §1 ("If those images are absent, use the written art briefs and simple pixel placeholders... Do not claim to have inspected an unavailable image"). |
| **D-10** | Build Orchestration | Top-level `Makefile` delegates to `python3 tools/sdd.py <subcommand>` so workstations with GNU Make can run `make <target>` while minimal containers without `make` run `python3 tools/sdd.py <target>`. | Bridges sandbox constraints (`make` absent) with requested project interface (`make assets`, `make rom`, etc.). |
