# Super Dig Dug (Neo Geo MVS)

Fan-made early-1990s style arcade sequel to *Dig Dug* targeting **SNK Neo Geo MVS** inside **MAME** (`320×224`, 68000 main CPU + Z80/YM2610 audio).

- **Gameplay & Engineering Authority:** [`docs/Super-Dig-Dug-Neo-Geo-MVS-Handoff.md`](docs/Super-Dig-Dug-Neo-Geo-MVS-Handoff.md)
- **Sprite, Terrain & Conversion Authority:** [`docs/Super-Dig-Dug-Coding-Agent-Sprite-Production.md`](docs/Super-Dig-Dug-Coding-Agent-Sprite-Production.md)

## Current Status

**Stage:** Repository Bootstrap Complete (`pre-M0` / `pre-B0`)
- Authoritative specifications saved in `docs/`.
- Complete runtime (`src/`), asset (`assets/`), level (`levels/`), tooling (`tools/`), emulator (`mame/`), and test (`tests/`) directory structure initialized.
- Canonical shared 16-entry baseline palette [`assets/palettes/metal_red_cyan_v1.json`](assets/palettes/metal_red_cyan_v1.json) created.
- Unified task runner [`tools/sdd.py`](tools/sdd.py) and [`Makefile`](Makefile) initialized.
- **No game ROM or MAME boot has been executed yet.** See [`TEST-REPORT.md`](TEST-REPORT.md) and [`MAME-SETUP.md`](MAME-SETUP.md) for current environment verification status.

## Repository Layout

| Path | Purpose |
|---|---|
| `docs/` | Authoritative gameplay handoff and sprite/tile production specs |
| `src/platform/neogeo/` | Neo Geo MVS startup, input sampling, VBlank/IRQ, watchdog, VRAM & Z80 audio bridge |
| `src/game/` | Session state machine (`title`, `attract`, `play`, `death`, `clear`, `game_over`) |
| `src/world/` | `36×22` (`8×8` logical cell) occupancy, materials, connectivity, rock support, mutations |
| `src/actors/` | Player, enemy, rock, and modular boss state machines |
| `src/combat/` | Pump tethers, inflation, status effects, bombs, and bounded tunnel-wave propagation |
| `src/items/` | Pickups, finite ammo, pump modules, and pre-zone loadout selection |
| `src/score/` | Single-commit death attribution, depth/rock rewards, Pop Chain, Technique, Clean Clear |
| `src/render/` | Dirty vertical terrain strips, metasprite poses, palette & safe VRAM staging |
| `src/audio/` | 68000 sound-command queue and Z80/YM2610 driver integration |
| `src/data/` | Read-only ROM tuning tables, enemy/tool definitions, and compiled level tables |
| `assets/concepts/` | Unmodified reference images and concept provenance mappings |
| `assets/source/` | Editable masters (`characters/`, `equipment/`, `terrain/`, `effects/`, `ui/`, `audio/`) |
| `assets/palettes/` | Named 16-color art palettes and hardware-quantized Neo Geo palette tables |
| `assets/export/` | Native indexed PNG sprite sheets and frame/tag/pivot/hitbox/socket JSON manifests |
| `assets/generated/` | Packed C-ROM sprite data, S-ROM FIX tiles, palettes, and runtime C tables |
| `assets/review/` | `1×` and `8×` nearest-neighbor contact sheets and animation review strips |
| `levels/` | Offline JSON level definitions |
| `tools/` | `sdd.py` CLI dispatcher, ROM packagers, budget analyzers, and `tools/assets/` converters |
| `tests/` | Host-buildable deterministic gameplay, asset-validation, and bitplane round-trip tests |
| `mame/` | Isolated MAME software-list/loader configs and launch scripts (never stores commercial BIOS files) |
| `build/`, `dist/` | Ephemeral build intermediates and versioned release packages |

## Project Commands

On a developer machine with GNU Make:

```sh
make status          # Probe installed compilers, ngdevkit, MAME, and Aseprite
make assets          # Export masters, generate 16 terrain masks, pack C-ROM/S-ROM tiles
make asset-check     # Run palette, alpha, hitbox, mask, strip-budget, and decode checks
make asset-preview   # Render 1x/8x nearest-neighbor review sheets
make art-viewer      # Build the Neo Geo MVS art-viewer / diagnostics ROM
make rom             # Build the Super Dig Dug Neo Geo MVS ROM
make test            # Run host unit, simulation, and asset tests
make budgets         # Report RAM, ROM, tile, and per-scanline sprite-strip usage
make run             # Launch in MAME via proven isolated configuration
make debug           # Launch in MAME with debugger enabled
make package         # Build clean distributable package in dist/
```

In minimal environments without `make` installed, invoke the dispatcher directly:

```sh
python3 tools/sdd.py status
```

## Governance & Tracking Documents

- [`MAME-SETUP.md`](MAME-SETUP.md) — Target toolchain, BIOS prerequisites, and isolated MAME loading procedure.
- [`FEATURES.md`](FEATURES.md) — Status, milestone, asset family mapping, and constraints for all 48 selected features (`01`–`48`) plus baseline families.
- [`DECISIONS.md`](DECISIONS.md) — Confirmed rules vs. reversible engineering defaults and sandbox adaptations.
- [`TEST-REPORT.md`](TEST-REPORT.md) — Recorded environment audit and verification results.
- [`NEXT-STEPS.md`](NEXT-STEPS.md) — Current milestone (`M0` / `B0`), concrete next actions, and active blockers.
