# Feature & Asset Backlog Status (`FEATURES.md`)

Tracks the baseline (`base`) foundation and all **48 curated additions** (`01`–`48`) across gameplay milestones (`M0`–`M9`) and sprite production batches (`B0`–`B7`).

**Status Legend:**
- Gameplay: `not_started` → `host_sim` → `rom_built` → `mame_verified`
- Art families (tracked per manifest): `missing` → `concept` → `pixel_master` → `animated` → `exported` → `rom_tested` → `approved` *(reserved for explicit user approval)*

---

## Baseline Systems (`base` — Phase 1: 1982 *Dig Dug* Replica on Neo Geo MVS)

| System / Asset Family | Milestone / Batch | Gameplay Status | Art Status | Notes & Constraints |
|---|---|---|---|---|
| 4-way movement, digging & `28×28` cell / `14×14` tile occupancy (`tile_topsoil`, `fx_dig`) | Phase 1 (M0–M1 / B0) | `host_sim` (C99 + Python) | `exported` (`standin_placeholder` in CI; `imported_unreviewed` via `PACK=`) | `Q12.4` fixed-point, `16`px turn-grid cornering, 16 quadrant masks (`0x00..0x0F`), 14 vertical sprite strips (`x=0..223`) |
| Falling rocks & support checks (`prop_rocks`) | Phase 1 (M1 / B0) | `host_sim` (C99 + Python) | `exported` | `SUPPORTED` → `HELD_BY_PLAYER` (indefinite hold!) → `WOBBLE` → `FALLING` → `SHATTER`; `1,000..15,000` multi-crush; 2-rock veggie spawn |
| `96×224` Side-Panel FIX HUD & Arcade Font (`ui_font`, `ui_hud`) | Phase 1 (M0–M2 / B0–B1) | `host_sim` (C99 + Python) | `exported` | `12×28` S-ROM `8×8` tiles (`x=224..319`, `0` sprite strips!), `HIGH SCORE`, `1UP`/`2UP`, helmet lives, round flowers |
| Player 1 (`chr_player_1`) & Standard Harpoon Pump (`tool_standard_pump`, `fx_pump`) | Phase 1 (M2 / B1) | `host_sim` (C99 + Python) | `exported` | `32`px reach, thin-dirt (`≤8`px) pierce, tap vs hold pump cadence, harmless inflated pass-through (`1..3`), deflation decay |
| Baseline Enemies (`enm_pooka`, `enm_fygar`, `fx_enemy_attacks`) | Phase 1 (M2 / B1) | `host_sim` (C99 + Python) | `exported` | Manhattan tunnel chase, ghost-eyeball dirt phasing, Fygar horizontal inhale telegraph + 3-tile flame, hurry-up & top-left `(0,0)` escape |
| Arcade Loop, Stratum/2× Fygar Scoring & 18-Round Vegetables (`pick_rewards`, `ui_logo`) | Phase 1 (M2 / B1) | `host_sim` (C99 + Python) | `exported` | Title/attract demo, 1P/2P alternating, `200..500` (`2×` horiz Fygar), `400..8,000` veggies, `20k`/`60k` extra lives, safe Round 256+ wrap |
| M0/B0 Art & Hardware Diagnostics Viewer (`src/game/art_viewer.c`) | M0 / B0 | `host_sim` (C99) | `exported` | Browses all 65 families & 2,074 frames, background luminance toggle, 16-mask grid test, VBlank/input/strip telemetry, V-ROM cue audition |

---

## Curated 48 Additions (`01` – `48`)

| ID | Feature | Milestone | Art Batch | Primary Asset Families | Gameplay Status | Evidence | Core Constraint |
|---:|---|---:|---:|---|---|---|---|
| **01** | Mecha-Pooka | M2 | B1 | `enm_mecha_pooka` | `not_started` | — | Extra inflation stage first; directional frontal armor later; rocks still counter |
| **02** | Borer Beetle | M4 | B3 | `enm_borer_beetle`, `fx_dig` | `not_started` | — | Telegraphed permanent tunnel carving; can undercut rocks |
| **03** | Clod | M4 | B3 | `enm_clod`, `fx_dig` | `not_started` | — | Refills soft diggable earth behind it; never entombs actors or seals hard |
| **04** | Goopy | M4 | B3 | `enm_goopy` | `not_started` | — | Full pump kills cleanly; interrupted pump splits at most once under strict cap |
| **05** | Fusebug | M5 | B4 | `enm_fusebug`, `fx_blast` | `not_started` | — | Pump arms visible fuse, next pump pushes; rock kill works before arming |
| **06** | Volty | M5 | B4 | `enm_volty`, `fx_enemy_attacks` | `not_started` | — | Cycles sparking armored vs. cooling vulnerable; fires slow tunnel spark |
| **07** | Gecko | M4 | B3 | `enm_gecko` | `not_started` | — | Ceiling ambush after tail-twitch warning; vulnerable during ground recovery |
| **08** | Echo | M5 | B4 | `enm_echo` | `not_started` | — | Tracks digging/blasts; stopping breaks tracking; solid vulnerability window |
| **09** | Mimic Pooka | M4 | B3 | `enm_mimic_pooka` | `not_started` | — | Vegetable disguise with periodic blink tell; standard pump safely reveals |
| **10** | Rootmaw | M5 | B4 | `enm_rootmaw`, `fx_enemy_attacks` | `not_started` | — | Stationary bulb with capped roots/spores; popping bulb clears all its roots |
| **11** | Air Cannon | M3 | B2 | `tool_air_cannon`, `fx_air`, `ui_equipment_menu` | `not_started` | — | Signature +1 inflation + tunnel knockback bolt; blocked by intact soil |
| **12** | Drill Missile | M5 | B4 | `tool_drill_missile`, `fx_dig`, `ui_equipment_menu` | `not_started` | — | Short straight soft-earth cut for remote rock drops; stopped by hard terrain |
| **13** | Freeze Sprayer | M5 | B4 | `tool_freeze_sprayer`, `fx_status`, `ui_equipment_menu` | `not_started` | — | Single-target temporary heavy ice block with thaw warning; no infinite player trap |
| **14** | Ricochet Disc | M5 | B4 | `tool_ricochet_disc`, `ui_equipment_menu` | `not_started` | — | Bounded rebounds in open space; predictable right-angle crystal redirects |
| **15** | Sonic Lance | M5 | B4 | `tool_sonic_lance`, `fx_status`, `ui_equipment_menu` | `not_started` | — | Open-corridor pulse forces phasing enemies solid; blocked by intact soil |
| **16** | Foam Launcher | M5 | B4 | `tool_foam_launcher`, `ui_equipment_menu` | `not_started` | — | Max 1 temporary tunnel plug per owner; cannot spawn on actors/rocks |
| **17** | Dig Bomb | M3 | B2 | `trap_dig_bomb`, `fx_dig`, `fx_blast`, `ui_equipment_menu` | `not_started` | — | Timed flash charge clears small pocket, stuns monsters, drops rocks, harms player |
| **18** | Remote Charge | M4 | B3 | `trap_remote_charge`, `fx_blast`, `ui_equipment_menu` | `not_started` | — | Max 1 active charge per owner; second B press detonates |
| **19** | Pressure Bomb | M5 | B4 | `trap_pressure_bomb`, `fx_blast`, `ui_equipment_menu` | `not_started` | — | Bounded BFS tunnel wave over snapshot; pops inflated, stuns uninflated, no double-hit |
| **20** | Decoy Turnip | M4 | B3 | `trap_decoy_turnip`, `ui_equipment_menu` | `not_started` | — | Non-explosive wind-up lure for nearby monsters; never overrides bosses |
| **21** | Cryo Bomb | M5 | B4 | `trap_cryo_bomb`, `fx_blast`, `fx_status`, `ui_equipment_menu` | `not_started` | — | Brief in-place group freeze (distinct from movable Freeze Sprayer block) |
| **22** | Turbo Hose | M2 | B1 | `module_turbo_hose`, `fx_pump`, `ui_equipment_menu` | `not_started` | — | Pre-zone pump module: faster inflation cadence at shorter reach |
| **23** | Long Tom Hose | M4 | B3 | `module_long_tom`, `fx_pump`, `ui_equipment_menu` | `not_started` | — | Pre-zone pump module: extended reach, slower cadence, unchanged player hitbox |
| **24** | Tri-Pump | M5 | B4 | `module_tri_pump`, `fx_pump`, `ui_equipment_menu` | `not_started` | — | Short 3-prong fan tether, slower cadence, each prong clipped by soil |
| **25** | Crystal Caverns | M6 | B5 | `tile_crystal_caverns`, `ui_world_cards` | `not_started` | — | Fixed-angle crystal reflectors & hard mineral veins; telegraphed reflections |
| **26** | Frozen Depths | M6 | B5 | `tile_frozen_depths`, `ui_world_cards` | `not_started` | — | Brittle ice supports & falling icicles; no forced floor sliding |
| **27** | Fungal Hollows | M6 | B5 | `tile_fungal_hollows`, `ui_world_cards` | `not_started` | — | Capped temporary spore clouds & marked root regrowth; no fog-of-war darkness |
| **28** | Sunken Temple | M6 | B5 | `tile_sunken_temple`, `ui_world_cards` | `not_started` | — | Indestructible stone blocks & failing pillars; water visual only, always solvable |
| **29** | Lost Machinery | M6 | B5 | `tile_lost_machinery`, `ui_world_cards` | `not_started` | — | Timed valves & fixed-direction warning air jets; no teleporters |
| **30** | Molten Core | M6 | B5 | `tile_molten_core`, `ui_world_cards` | `not_started` | — | Marked finite lava pockets drain bounded steps downward; no global rising lava |
| **31** | King Pooka | M6 | B6 | `boss_king_pooka` | `not_started` | — | Charge vs. vulnerable inhale cycle, capped minion spawns, beatable with base pump |
| **32** | King Fygar | M7 | B6 | `boss_king_fygar`, `fx_enemy_attacks` | `not_started` | — | Single-arena fire bait, exposed cheek sacs, safe rock regeneration for finisher |
| **33** | Iron Mole | M7 | B6 | `boss_iron_mole` | `not_started` | — | Telegraphed drill routes, rock drops crack armor to expose pumpable bellows |
| **34** | World Worm | M7 | B6 | `boss_world_worm` | `not_started` | — | Modular `32×32`/`48×48` segments within strip/RAM budgets; drive into collapse trap |
| **35** | Hard Hat | M4 | B3 | `pick_hard_hat`, `fx_status`, `ui_hud` | `not_started` | — | Absorbs 1 contact/shot/blast hit + brief i-frames; rock crush & lava stay lethal |
| **36** | Tunnel Boots | M4 | B3 | `pick_tunnel_boots`, `ui_hud` | `not_started` | — | Timed speed boost in open tunnels only; dig speed & cornering stay crisp |
| **37** | Soil Scanner | M4 | B3 | `pick_soil_scanner`, `ui_hud` | `not_started` | — | Reveals buried items & marked pockets; lethal hazards remain readable without it |
| **38** | Bonus Balloon | M6 | B5 | `pick_bonus_balloon` | `not_started` | — | Surface balloon cycles real equipment icons on first hit, locks reward on next |
| **39** | Pop Chain | M4 | B2/B1 | `fx_score`, `ui_font`, `ui_hud` | `not_started` | — | Capped kill-window multiplier; anti-farming guard on splits & boss minions |
| **40** | Technique Bonus | M3 | B2/B1 | `fx_score`, `ui_font`, `ui_hud` | `not_started` | — | Explicit action-flag bonus (*inflate → launch → crush*, *freeze → drop*) |
| **41** | Clean Clear | M4 | B2/B1 | `fx_score`, `ui_font`, `ui_hud` | `not_started` | — | Stage-clear no-hit bonus; forfeited even if Hard Hat absorbs a hit |
| **42** | Garden Panic | M6 | B5 | `bonus_garden`, `ui_font` | `not_started` | — | Timed crop-recovery bonus stage; score-only (failure never costs a life) |
| **43** | Rockfall Rally | M4 | B3 | `bonus_rockfall`, `ui_font` | `not_started` | — | Limited-rock puzzle chamber bonus stage; score-only |
| **44** | Pressure Test | M4 | B3 | `bonus_pressure_test`, `ui_font` | `not_started` | — | Timed multi-target inflation juggling bonus stage; no dependency on Pressure Bomb |
| **45** | Co-op Rescue | M8 | B7 | `chr_player_2`, `fx_coop`, `ui_font` | `not_started` | — | Shared arena P2, non-blocking partners, timed capture/rescue without deadlocks |
| **46** | Boss Rush | M7 | B2 | `ui_font`, `ui_screen_frames` | `not_started` | — | Fixed-loadout replay of the 4 bosses with separate score table |
| **47** | Reactive Music | M7 | B6 | Audio driver + optional `ui_audio_cue` | `not_started` | — | Movement-linked YM2610/ADPCM music with boss/danger state layer |
| **48** | Expanded Combat Animation | M2–M7 | B0–B7 | Cross-catalog animation states | `not_started` | — | Distinct anticipation, inflation, armor-break, freeze & defeat poses within strip budget |
