# Super Dig Dug — Neo Geo MVS Coding-Agent Handoff

**Version:** 1.0  
**Date:** November 17, 2026  
**Status:** Design and implementation roadmap; no game code, toolchain build, or ROM has been produced or tested in this conversation.  
**Confirmed platform:** SNK Neo Geo MVS, running inside MAME.  
**Immediate objective:** Build a reproducible native MVS development ROM, then a small playable Super Dig Dug combat slice.

## 1. Mission and authority

Build **Super Dig Dug**, a fan-made arcade sequel with the character of a lost early-1990s release. Preserve digging, pump inflation, and falling-rock traps. The signature new sequence is **inflate → reposition → crush**. Later, add pressure blasts whose paths are determined by the tunnels the player dug.

The user has confirmed Neo Geo MVS. This supersedes the original plan to patch the 1982 Dig Dug Z80 ROM. Implement a new 68000 game for MVS; original Dig Dug ROM disassembly and original-board free-space searches are no longer prerequisites. A desktop or browser prototype may help development, but completion requires the native ROM running in MAME.

The user supplied seven concept pitches and accepted a curated 48-addition selection. All 48 are reproduced below with stable IDs. They are a phased target, not simultaneous requirements for the first build. Preserve these IDs in the backlog and changelog.

### Decision precedence

1. Subsequent explicit user direction.
2. Confirmed Neo Geo MVS platform and the gameplay decisions in this handoff.
3. The 48 selected feature descriptions and constraints.
4. The raw seven pitches as optional inspiration.

The earlier **Super-Dig-Dug-Curated-48.md** remains the source of the feature selection. Its original-ROM audit, tentative hardware choice, and original-cabinet input concerns are superseded by this handoff. Its remark about auditing original sound resources is replaced by budgeting the new MVS sound driver and assets.

### Confirmed scope versus working defaults

| Item | Status |
|---|---|
| Title: Super Dig Dug | Confirmed project identity |
| Neo Geo MVS inside MAME | Explicit user choice |
| Curated 48 additions | Accepted design target |
| Native game implementation instead of patching the original ROM | Necessary consequence of the platform change |
| Standard MVS clocks, memory, graphics and cartridge interfaces | Recommended implementation baseline |
| 320 × 224 landscape, single-screen arenas | Working default carried forward from the platform recommendation |
| C with ngdevkit, small assembly support | Recommended toolchain; pin and prove it |
| One pump module plus one special slot | Selected design rule |
| Two gameplay buttons; no in-combat inventory | Selected design rule |
| Exact art, level count, campaign sequence, numbers and balance | Open; use the defaults below and document changes |
| Physical MVS cartridge release | Not requested; MAME validation does not establish physical-board compatibility |

Do not restart platform selection or request routine design confirmations. Resolve reversible implementation choices, document assumptions, and produce playable increments. A genuine missing dependency should be named precisely; continue independent work while it is unavailable.

## 2. Game identity and non-negotiable behavior

- Four-direction movement and digging; no jumping, diagonal movement, or general-purpose physics engine.
- A fully visible arena. The initial release has no scrolling camera or fog of war.
- Pooka, Fygar, the normal pump, dirt and falling rocks form the baseline and are not part of the 48-addition count.
- Every normal enemy must be beatable with movement, digging, pumping and rocks. Special ammunition must never be a mandatory key.
- The standard pump is unlimited. Special weapons have limited ammunition.
- Select one pump module and one special tool before a zone. Bombs and projectile tools share the special slot.
- Readable warning animations precede dangerous attacks. Physical state changes communicate inflation, armor, freezing and boss vulnerability.
- Chains reward planning. No unlimited piercing beams, routine screen clears, uncapped summons or uncapped splitting.
- Retain depth-sensitive scoring and multi-enemy rock rewards as baseline concepts. Exact original formulas are not asserted here.
- Excluded from this roadmap: versus mode, procedural endless mode, shops, currency, weapon XP, mandatory element matching, full fluid simulation, island sinking, forced ice sliding, gravity flips and global collapse clocks.
- Co-op Rescue and Boss Rush are later modes. Reserve clean support for two player identities, but ship the first slice for one player.
- The pitches disagree on historical details and original statistics. Do not encode their unverified pump counts or claims about Super Space Invaders '91 as facts.

## 3. Target hardware and toolchain

Use the existing MVS hardware model. A development registration or loading change in MAME is acceptable if needed; increasing emulated CPU speed, RAM or sprite limits is a separate architecture change and is not the default.

### Hardware constraints that affect the design

| Area | Development implication |
|---|---|
| 12 MHz 68000-class main CPU | Integer/fixed-point gameplay; small predictable update costs |
| Z80 sound subsystem and YM2610 | Separate sound driver; explicit sound-command protocol |
| 64 KiB main work RAM | Budget globals, stack, SDK data and BIOS reservations together |
| 320 × 224 nominal active display | Landscape arena; test visible safe margins in the selected MAME machine |
| Sprite-based scene construction | Terrain and characters consume sprite strips; do not assume a conventional scrolling background layer |
| 16 × 16 sprite tiles, 15 visible colors plus transparency per tile palette | Build indexed assets and validate palette use |
| 96 sprite strips per scanline | Count strips, including terrain, bosses and effects, not gameplay objects |
| Graphics stored in cartridge ROM | Change tile references to show digging; do not write new pixel graphics into cartridge ROM or treat VRAM as a framebuffer |

The hardware references in section 15 document these facts. Verify the selected SDK's usable RAM region and startup requirements; BIOS-reserved memory is not game scratch space.

### Toolchain choice

Start with **ngdevkit**, plus its matching examples. Use C for gameplay and the minimum assembly needed by startup, interrupts or measured hot paths. Start from working SDK conventions rather than inventing boot code.

Pin:
- ngdevkit and example revisions;
- compiler/binutils versions;
- asset converter and sound tooling versions;
- MAME version and, if customized, its exact source revision and patch;
- chosen BIOS and cartridge configuration, identified by filename and hash in local configuration.

Linux or WSL is a reasonable build default. Keep asset scripts portable. Add macOS setup instructions if verified; do not claim cross-platform support based only on an SDK README.

An SDK-provided development BIOS may help the first test. Verify that the selected MAME machine can actually load it and enumerate any remaining system-ROM requirements. Passing under a development BIOS is not proof of compatibility with every MVS BIOS.

## 4. First critical gate: make the ROM load in MAME

**A ZIP filename does not register a new arcade game in MAME.** Prove the loader before writing substantial gameplay.

1. Inspect the installed MAME version and its Neo Geo machine/slot/software definitions.
2. Build an unmodified small ngdevkit example and establish a repeatable boot path in MAME.
3. Prefer a supported cartridge/software-list route if the pinned MAME configuration exposes one.
4. If necessary, add a minimal project-specific ROM registration in a reproducible custom MAME build using the existing MVS hardware. Keep this patch separate from the game.
5. If an SDK initially uses a donor game's registration, keep all substituted files in an isolated project ROM directory. Document the temporary mapping; do not overwrite the user's ROM collection or ship the result under a commercial game's identity.
6. Record byte ordering, interleaving, ROM-region sizes, padding and hashes from the proven pipeline.
7. Write a launch script with the exact tested arguments and separate config, NVRAM and screenshot directories.
8. Test a clean cold boot, reset, credit/start input and sound initialization.

The expected content families are P (68000 program), C (sprites), S (FIX text), M (Z80 program), and V (samples). Their precise filenames, sizes and interleaving belong to the chosen cartridge/loader definition. Use the SDK's packing conventions and verify them against the selected MAME definition.

Produce **MAME-SETUP.md** containing the actual command, machine name, BIOS prerequisites and loading method. No untested `mame superdigdug` promise. A project launcher may provide a short command after the real setup is proven.

## 5. Display, terrain and movement design

### Provisional screen layout

Use 320 × 224 with a compact HUD, surface strip, and centered underground arena. A starting arena is **288 × 176 at x=16, y=32**: 18 × 11 visual tiles. This is a prototype layout, not a locked art specification. Check enemy density and co-op space before finalizing it.

- FIX layer: HUD, scores, lives, equipment and menus.
- Background sprite strips: soil and tunnel presentation.
- Foreground strips: actors, rocks, weapons, warning effects and bosses.
- Keep primary warnings visible even when cosmetic effects are dropped.

### Terrain representation

Do not recreate arbitrary pixel erosion at the outset.

Recommended first implementation:
- 8 × 8 logical terrain cells, grouped four at a time into a 16 × 16 visual tile.
- For the provisional arena this is 36 × 22 logical cells.
- A four-bit occupancy mask gives 16 basic excavated/filled combinations per visual tile. Generate these tile variants offline for each material.
- Keep semantic material and occupancy data separate from visual tile IDs.
- Move actors smoothly in fixed-point coordinates. Dig with an actor-sized swept footprint; do not move the actor in 8-pixel jumps.
- Use temporary dust/edge animation to soften excavation transitions without changing collision truth.
- Add richer edge patterns only after the small tile vocabulary is proven.

All digging, explosions, borers, roots, foam and rock supports must query the same authoritative terrain model. Emit a bounded terrain-change record and dirty the affected visual tiles. Dirty rendering must not delay authoritative collision changes, and large visible changes must be staged coherently so a player never collides with a substantially stale display.

### Renderer implementation

A soil column can use a vertical strip of tile references, rather than allocating one hardware sprite per dirt tile. Allocate stable ranges for terrain, actors, HUD effects and bosses. Characters larger than 16 pixels require several strips.

Use dirty tile/attribute updates and measured VRAM write timing. Read and reuse the SDK's safe access routines. Do not copy hundreds of tiles every frame when only a few changed. Build staging commands outside the critical interrupt and commit a bounded batch at a safe time. Full-screen loads may use a transition screen.

The render list may be double-buffered in ordinary RAM if budget permits; do not assume Neo Geo offers a conventional framebuffer swap.

### Movement and collision defaults

- Four-direction input with explicit opposite-key handling and a small buffered-turn window near corridor centers.
- Separate move speed through open tunnels from dig speed through earth.
- Tick-based action timers. Tap A attaches/starts pumping; holding A performs controlled repeated pumps. Leaving range or releasing long enough breaks commitment and allows deflation.
- Resolve movement in bounded substeps or swept tests so fast knockback and projectiles cannot pass through solid obstacles.
- Use stable actor handles (slot plus generation) so a tether cannot attach to an object that reused a deleted enemy's slot.
- Keep collision rules separate for soil, hard walls, falling rocks, frozen bodies, foam and actors.

Original-game reference play, when available, should inform turn timing, pump commitment and rock warning delays. It is optional research, not a reason to block a fresh implementation. Label intentional differences.

## 6. Architecture and data flow

Keep gameplay deterministic and independent of MAME internals. The emulator executes the game; it does not implement the game.

| Module | Responsibility |
|---|---|
| `platform/neogeo/` | Startup integration, input sampling, interrupts, watchdog, video/audio submission, BIOS interactions |
| `game/` | Title/attract/play/death/clear/game-over state machine and session rules |
| `world/` | Terrain occupancy, materials, connectivity, support checks, terrain mutations |
| `actors/` | Player, enemy, rock and boss state machines |
| `combat/` | Pump tethers, inflation, attacks, status effects, bombs and bounded chain events |
| `items/` | Pickups, ammunition, modules and pre-zone equipment choice |
| `score/` | Kill attribution, depth/rock scoring, chains and technique flags |
| `render/` | Terrain tiles, actor poses, strip allocation, palette/VRAM commands |
| `audio/` | 68000 command producer and separately built sound driver integration |
| `data/` | Read-only tuning tables, compiled levels, enemy/weapon definitions |
| `tools/` | Asset conversion, level validation, ROM packaging, budget reporting and run scripts |
| `tests/` | Host-buildable gameplay tests and MAME smoke/replay scenarios |

Use enums and compact tagged structs rather than a heap-heavy object framework. Read-only level and tuning data stays in ROM. No heap allocations during gameplay, recursive flood fills, floating-point physics or OS calls in the runtime.

### Frame loop

Drive one simulation update per emulated vertical refresh; derive timing from the selected machine. Neo Geo NTSC is approximately 59.19 Hz, not exactly 60. Treat “60 fps” as a colloquial performance goal, not a timer constant.

1. Capture input and frame counter through the platform layer.
2. Apply buffered input, movement and equipment actions.
3. Update enemies and telegraphed attacks in a fixed order.
4. Resolve terrain changes, support checks and bounded moving objects.
5. Resolve hit events, deaths and scores in a stable order.
6. Apply bounded secondary events and stage-completion rules.
7. Prepare render changes and sound commands.
8. Commit using the tested interrupt/video schedule; service the watchdog and BIOS callbacks as required.

Document same-frame precedence: for example, a scored death can be committed only once even if a rock and a bomb hit together. Choose an explicit policy for simultaneous player death and last-enemy defeat and test it.

Keep critical interrupt handlers short. Do not run the full AI or asset decoding in an interrupt. Track missed frame deadlines rather than hiding them with emulator frameskip or CPU overclocking.

### Status and event model

Model moving, inflating, stunned, frozen, charging, dying and dead explicitly. Avoid a collection of contradictory booleans. Some status combinations should be disallowed by design.

Events should carry stable source/target handles, owner/player identity, cause and relevant technique flags. Award points once, on committed death. Clear or invalidate pending events that reference objects destroyed during a stage transition.

For Pressure Bomb, use a fixed queue and visited mask over a snapshot of connected open terrain at detonation. Cap travel distance and active waves. Soil blocks the wave; uninflated targets stun while inflated targets pop. Animate propagation and guard against loops revisiting a target. Later terrain changes do not retroactively rewrite an already-emitted wave.

## 7. Resource budgets and overload policy

These are initial engineering budgets, not claims that the game has already met them.

| Resource | Starting target | Required evidence |
|---|---|---|
| Main static game data | At most 40 KiB | Linker map and a per-module RAM report |
| Stack allowance | Reserve and measure approximately 8 KiB | Stack watermark/canary; account for interrupts |
| Remaining work RAM | SDK globals, BIOS reservation, safety margin | Entire usable linker region checked; no overlap |
| Program ROM | Aim for first 1 MiB initially | Proven SDK ROM layout; add banking only when justified |
| Render load | Aim below 80 strips on any scanline | Include background, sprites, effects and boss parts |
| CPU load | Aim for at least 20% frame headroom under stress | Target-side timing or defensible cycle/frame instrumentation |
| Gameplay update | One per native frame | No unexplained dropped simulation frames |

The game's 40 KiB and 8 KiB targets do not authorize using reserved memory. Size the complete image against the SDK/BIOS usable region; lower these budgets if necessary.

Initial fixed pools: 2 player slots, 24 enemy slots, 8 rock/heavy-object slots, 16 projectile slots, 4 planted-charge slots, 8 pickup slots, 16 cosmetic effects and 64 event entries. These are provisional and should be reduced or repartitioned if actual structure sizes or screen density demand it. Per-weapon limits can be stricter; Remote Charge and Foam each allow only one active object per owner.

On pool pressure:
- Reject an action before consuming ammo if it cannot create its required gameplay object.
- Drop optional cosmetic particles first.
- For splitting/summoning, use a documented safe fallback; do not corrupt the remaining-enemy count or score.
- Never silently discard an authoritative death, damage or terrain event. Reserve capacity, process bounded batches, or defer the initiating action safely.
- Debug builds report the high-water marks and overload occurrence.
- Avoid large full-map arrays on the stack. Use a bounded shared work buffer when its lifetime permits.

## 8. Gameplay foundation

### Pump and enemies

The baseline needs more than an enemy following a player. Implement tunnel movement, deliberate phasing transitions, inflation levels, temporary immobilization, deflation, defeat, and a readable Fygar attack cycle. Confirm target eligibility independently of rendering poses.

Use table-driven values for range, pump cadence, stages to pop, deflation delay, speeds and scores. Start with tunable provisional values; do not advertise arcade-perfect behavior without comparison.

Mecha-Pooka's first version is a visible extra inflation stage. Directional armor is a later refinement. Turbo Hose changes cadence and range using the same pump implementation.

### Rocks and heavy objects

Suggested states: supported → warning/wobble → falling → impact/settle or break → retired. Decide exact landing behavior and use it consistently. Rocks damage players as well as enemies. Deduplicate multi-target crush scoring.

Support checks run after terrain edits in the affected neighborhood. Provide tests for a rock spanning partially removed support, multiple simultaneous rock drops and chain reactions. Frozen bodies can reuse the heavy-object machinery later without becoming indistinguishable from ordinary rocks.

### Special weapons

B fires or places the selected special. A Remote Charge's second B activation detonates the existing charge. Require a release before rearming a newly selected tool to prevent held-button misfires.

Air Cannon must push enemies into valid open space, stop at hard obstructions, add bounded inflation and preserve ownership for technique scoring. It must not overwrite another object's state arbitrarily.

Dig Bomb clears bounded soft terrain, stuns monsters and releases rocks. It can harm the player. A level transition cancels remaining charges and projectiles.

### Equipment and scoring

Use a pre-zone selection screen; A confirms, directions change choice. Keep standard pump available. For development, a clearly marked stage selector can exercise all tools while respecting one special slot at a time.

Initially, use three lives per credit and simple finite ammunition; these are tuning defaults. No health bar. For Hard Hat, the proposed rule is protection from one ordinary contact/projectile/blast hit; falling-rock crush and lava remain lethal. Show this distinction in play and revise if testing finds it confusing.

A Clean Clear is lost on any hit, including a shield hit. Bound chain multipliers. Avoid farming unlimited split children or boss minions. Original depth and multi-crush rewards are baseline systems, not extra IDs.

## 9. Art, audio and content pipeline

### Art

Use readable early-1990s pixel art: strong silhouettes, saturated strata colors, exaggerated inflation, compact UI. Prioritize placeholder art with correct collision and state readability before finished sprites.

Store editable source assets and generated ROM assets separately. An asset manifest records frame dimensions, pivot, palette, tile ranges, animation durations, collision metadata and provenance. Collision boxes should be explicit data, not guessed from transparent pixels each frame.

Offline validation must catch:
- excess palette colors or bad transparency;
- nonconforming tile dimensions;
- missing frames or duplicate tile-range assignments;
- invalid frame/animation indices;
- boss strip counts that exceed the measured rendering budget.

No smooth alpha blending or modern shaders are assumed inside the emulated game. Optional CRT display effects belong to MAME configuration and must not conceal rendering defects.

### Sound

Start with a tested sound-driver example and a few clear cues: dig, pump, pop, rock warning, rock impact, player death, stage clear and special activation. Define command IDs and acknowledgement behavior explicitly. A failed sound handshake must not lock the main CPU forever.

Add one original placeholder loop first, then movement-linked variation and later #47 Reactive Music. Budget music/SFX priorities so a rapid chain cannot mask a critical warning. Avoid restarting music samples every frame as the player moves.

Keep sound sources, tracker data and converted samples reproducible. Record licenses for imported code and assets; a game's ROM package should not casually bundle third-party system BIOS files.

### Levels

Use a simple authoring format, such as JSON, compiled offline into compact ROM data. No runtime JSON parser.

A level should declare dimensions, material layout, open cells, start positions, rocks/supports, enemy spawns, buried supplies, available equipment, goals and seed. Validate bounds, spawn overlap, reachable starting space and required boss resources.

Start with hand-authored levels. Every stage must remain finishable after specials run out. Phasing enemies can help escape isolation, but cannot excuse broken level-clear accounting.

## 10. Roadmap with acceptance gates

Milestones are ordered by dependency, not calendar estimates. Keep the game bootable between them. “Complete” means tested in MAME and documented, not merely implemented in source.

### M0 — Reproducible platform bring-up

**Deliver:** pinned toolchain, proven cartridge mapping, build/package/run scripts, setup notes, linker map and a small diagnostics ROM.

**Scope:** title text, one moving sprite, palette test, P1/P2 input display, coin/start, VBlank counter, watchdog-safe loop, one sound cue.

**Pass:** clean checkout builds; cold boot/reset work; both input ports are read; sound command returns; exact MAME launch is recorded; five-minute diagnostic run has no resets or stalls.

**If blocked:** report the precise missing tool/BIOS/loading capability. Keep building independent code and tests. Do not report another emulator's success as MAME success.

### M1 — Digging sandbox

**Deliver:** playable arena with smooth movement, digging, rock supports, falling rocks and debug terrain/strip overlays.

**Scope:** shared terrain representation, safe VRAM updates, baseline actor footprint and rock states.

**Pass:** all four directions, corners and reversals behave consistently; terrain collision and visuals agree; undercutting a rock triggers a warning and fall; reset reliably clears the sandbox; worst-case dig edits remain within budget.

### M2 — Baseline arcade loop plus first two additions

**Deliver:** title/attract → credit/start → three short stages → death/game over/restart, with Pooka, Fygar, rocks and the pump.

**Features:** #01 Mecha-Pooka (extra-stage version), #22 Turbo Hose. Essential #48 warning poses begin here but the full feature remains in progress.

**Pass:** baseline enemies move, phase, inflate, deflate and die; Fygar telegraphs fire; rock kills and depth scoring work; every stage can clear; losing lives and restarting leaves no stale objects; Standard and Turbo differ visibly and mechanically.

This is the **first playable ROM milestone**, not the final expansion.

### M3 — Signature Super Dig Dug slice

**Deliver:** a polished small slice of roughly six short stages with pre-stage equipment choice.

**Features:** #11 Air Cannon, #17 Dig Bomb, #40 Technique Bonus. Continue #48.

**Pass:** demonstrate inflate → launch → rock crush with one score award; Dig Bomb opens terrain and releases rocks; exhausting ammunition still permits completion; both specials are selectable across runs/stages without requiring a second special slot.

**Review evidence:** ROM/package, exact run instructions, short gameplay capture, actual RAM/strip/timing measurements and a list of known defects.

### M4 — Tactical variety, rewards and small challenges

**Features:** #02 Borer Beetle, #03 Clod, #04 Goopy, #07 Gecko, #09 Mimic Pooka; #18 Remote Charge, #20 Decoy Turnip, #23 Long Tom Hose; #35 Hard Hat, #36 Tunnel Boots, #37 Soil Scanner; #39 Pop Chain, #41 Clean Clear; #43 Rockfall Rally, #44 Pressure Test.

**Deliver:** small reusable systems for timed pickups, attraction, terrain refill, safe splitting and score-only bonus stages.

**Pass:** Clod cannot entomb an actor; Goopy splits at most once and respects caps; scanners never become required for spotting lethal danger; level-clear accounting survives splits; chain scoring cannot be farmed indefinitely; shield hits invalidate Clean Clear; bonus-stage failure does not remove a life.

### M5 — Advanced tools and bounded reactions

**Features:** #05 Fusebug, #06 Volty, #08 Echo, #10 Rootmaw; #12 Drill Missile, #13 Freeze Sprayer, #14 Ricochet Disc, #15 Sonic Lance, #16 Foam Launcher; #19 Pressure Bomb, #21 Cryo Bomb, #24 Tri-Pump.

**Deliver:** robust statuses, connected-tunnel blast propagation, reflectors, frozen heavy objects and limited terrain growth.

**Pass:** cyclic tunnels cannot create infinite blasts; one enemy cannot be hit twice by the same pressure wave; soil blocks normal shots; drill range is bounded; frozen blocks thaw safely; foam cannot appear inside occupied cells; Rootmaw's death clears its growth; every enemy still has a baseline counter.

### M6 — Worlds and first boss

**Features:** #25–#30 environments, #31 King Pooka, #38 Bonus Balloon, #42 Garden Panic.

**Deliver:** functional biome demonstrations and a short campaign skeleton. Introduce one hazard at a time. A palette swap alone does not complete an environment.

**Pass:** each biome demonstrates its signature rule; molten pockets use finite tile updates; temple objectives remain possible after collapses; balloons lock rewards predictably; Garden Panic has clear recoverable crops and a timer; King Pooka is beatable with basic tools.

The exact campaign order and stage count remain provisional. Use a stage selector until the sequence is balanced. Four bosses do not require a boss at the end of each of six biomes.

### M7 — Bosses, presentation and single-player release candidate

**Features:** #32 King Fygar, #33 Iron Mole, #34 World Worm, #46 Boss Rush, #47 Reactive Music; complete #48 Expanded Combat Animation.

**Deliver:** a finite single-player campaign, ending, functioning bonuses, boss replay mode, finished equipment UI, high-score initials and versioned persistence through supported MVS/BIOS facilities.

**Pass:** no boss becomes impossible after ammunition or supplied rocks are spent; Boss Rush uses the implemented four bosses; all attack warnings are clear; final audio supports simultaneous warnings; a full campaign and repeated death/reset paths pass.

Single-player RC covers **47 of 48 additions**. #45 remains explicitly pending.

### M8 — Co-op Rescue and full selected-scope release

**Feature:** #45 Co-op Rescue.

**Deliver:** second player, shared terrain, capture/rescue state, ownership rules, shared score default, joining and game-over rules.

**Working defaults:** player bodies do not block each other; pump and direct tool hits do not hurt the partner; falling rocks, terrain hazards and explosions threaten both. Captures have a visible timeout; the free player can defeat the captor to rescue. Timeout costs the captured player a life. If both players are incapacitated, resolve a team life-loss/reset without a deadlock. Capture availability is capped and requires a reachable rescue path.

**Pass:** one player can continue when the other is absent/out of lives; capture/rescue cannot strand the team; simultaneous interactions score once; maximum two-player load stays within the target budgets.

### M9 — Packaging and regression pass

**Deliver:** versioned game ROM package, sources, build/run instructions, source/asset notices, dependency lock, loader definition or MAME patch if required, content manifest and test report.

**Pass:** a fresh environment reproduces the build and starts the game with the documented prerequisites; no dependency on another emulator is hidden; no ROM collection is overwritten; latest full campaign, Boss Rush, bonus rounds and co-op regression paths pass.

All 48 additions are “complete” only after M8/M9 evidence exists. Do not label the small first slice as the full sequel.

## 11. Test strategy

Use targeted tests for mechanics that can lose progress, corrupt state, or produce hard-to-reproduce bugs. Do not spend time writing tests that only mirror constants.

### Host tests for pure gameplay logic

- Terrain edit and support checks at corners and partial support.
- Pump attach/release, deflation and target handle reuse.
- Last-enemy accounting after splitting, spawning and same-frame deaths.
- Pressure-wave propagation in a loop, at a junction, behind soil and at the map edge.
- Single scoring/ownership resolution for overlapping hits.
- Fixed-pool exhaustion, delayed event resolution and stage cleanup.
- Reachability/counter availability in authored levels.
- Deterministic replay checksum for the same input stream and seed.

Use explicit integer widths and serialization. Host tests must not hide target bugs from endianness, alignment, signed overflow or structure size. Run representative scenarios on the 68000 build.

### MAME integration checks

- Cold boot, reset, title/attract, coin/start, game over and return.
- Sprite palettes, layer ordering, maximum inflation size and full boss width.
- Rapid digs, explosions, roots and refill with no collision/display mismatch.
- Simultaneous sound effects and music, including a stalled sound-driver test path.
- Stress arena with worst-case visible actors, terrain updates and secondary effects.
- At least a 30-minute soak for a release candidate, with no watchdog resets, pool leaks or uncontrolled score growth.
- P1/P2 controls and the full capture/rescue cycle once enabled.

A deterministic in-game input/seed recorder may be simpler than emulator automation initially. If using MAME Lua or input recordings, verify the pinned version's API. Emulator process exit code and screenshots alone are insufficient proof that the game is functioning.

For every milestone record: version, build hash, MAME/BIOS setup, scenario, result, frame misses, RAM high-water, maximum strips per line and known limitations. Capture video for visual/input review; do not invent measured performance.

## 12. Project organization and deliverables

Suggested repository folders:

| Path | Contents |
|---|---|
| `src/platform/neogeo/` | Hardware boundary |
| `src/game/`, `src/world/`, `src/actors/`, `src/combat/` | Main runtime |
| `src/render/`, `src/audio/`, `src/items/`, `src/score/` | Shared systems |
| `assets/source/` | Editable art and audio |
| `assets/generated/` | Deterministic conversion outputs |
| `levels/` | Authoring data |
| `tools/` | Build helpers, converters, packer and launcher |
| `tests/` | Gameplay and integration scenarios |
| `mame/` | Proven software definition or minimal registration patch |
| `docs/` | Hardware decisions, setup, feature status and test reports |
| `build/`, `dist/` | Intermediate and packaged outputs; keep out of source commits as appropriate |

Provide project commands such as `make assets`, `make rom`, `make test`, `make run`, `make debug`, `make budgets` and `make package`. These are target interface names to implement, not existing SDK commands.

Maintain:
- **README.md:** what currently works and how to run it.
- **MAME-SETUP.md:** exact tested configuration and prerequisites.
- **FEATURES.md:** IDs 01–48, status, milestone, evidence and known limitations.
- **DECISIONS.md:** reversible choices and any architecture deviations.
- **TEST-REPORT.md:** actual verification results.
- **NEXT-STEPS.md:** current milestone, next concrete tasks and blockers.

Keep milestone commits small enough to revert. Every handoff should name the latest bootable revision and exact next action.

## 13. Initial work order for the coding agent

Begin implementation with M0, then continue into M1 while the build stays healthy.

1. Inspect the repository/environment and preserve existing work.
2. Record available compiler, SDK and emulator versions.
3. Pin ngdevkit and build a minimal example.
4. Resolve and prove the MAME loading route.
5. Produce the diagnostics ROM and its exact launch instructions.
6. Add input/VBlank/audio tests and a resource report.
7. Implement a minimal soil grid with smooth digging and one falling rock.
8. Report the playable result, measured constraints and next milestone.

Do not start by generating all 48 features or polished artwork. Do not substitute a browser-only demonstration for native progress. Do not wait for an original Dig Dug ROM to create the new game. If MAME cannot run in the current environment, distinguish build-only evidence from emulator-tested evidence and supply a concrete local test procedure.

The next substantive user review should be a running MVS sandbox or first playable slice, rather than another platform proposal.

## 14. Complete 48-addition backlog

The following entries preserve the selected concepts and constraints. Milestone assignments indicate first planned delivery; dependent refinements can continue later. Source labels refer to the supplied proposal authors/filenames, not external historical evidence.

### 01. Mecha-Pooka — M2

An armored Pooka with a visible extra inflation stage; advanced version blocks frontal shots but exposes its rear.

**Constraint:** Start with the extra pump requirement. Add directional armor later; rocks remain a valid counter.

**Proposal sources:** Particle: Helmeted Pookas; Hydrogen: Mecha-Pooka; Mimo: Clawzer.

### 02. Borer Beetle — M4

Carves permanent tunnels toward you and can accidentally release supported rocks.

**Constraint:** Telegraph digging; reuse the player's terrain-removal rules where possible.

**Proposal sources:** Hydrogen: Borer-Beetle; Muse: Moggy; Longcat: Tunnelmite; Particle: Grubber.

### 03. Clod — M4

Refills the tunnel behind it with soft, diggable earth.

**Constraint:** Never creates indestructible seals; give fresh earth a brief visual cue.

**Proposal sources:** Astra: Clod; Mimo: Golemite.

### 04. Goopy — M4

Leaves a temporary slowing trail; an interrupted inflation splits it into two smaller slimes.

**Constraint:** Adaptation: completed pumping kills it cleanly. Splitting happens once, with a strict entity cap.

**Proposal sources:** Muse: Goopy; Hydrogen: Mitosis Slime; Flint: Split Squiggle.

### 05. Fusebug — M5

Inflation arms its blinking fuse; another pump pushes it toward a group before it explodes.

**Constraint:** A moving trap, with a clear fuse and bounded blast. Permit an early rock kill before arming.

**Proposal sources:** Astra: Fusebug; Longcat: Fuse Pooka.

### 06. Volty — M5

Alternates between a sparking armored state and a vulnerable cooling state; fires a slow spark down a tunnel.

**Constraint:** Distinct charge animation and sound. Pump during cooldown or crush with a rock.

**Proposal sources:** Muse: Volty.

### 07. Gecko — M4

Hangs from a tunnel ceiling and drops after a warning twitch.

**Constraint:** A compact ambush enemy; bait its drop and pump it while it recovers.

**Proposal sources:** Astra: Gecko.

### 08. Echo — M5

Tracks digging and explosions through soil, then becomes solid before attacking.

**Constraint:** Stopping movement breaks its tracking. Always provide a normal pump vulnerability window.

**Proposal sources:** Astra: Echo; Muse: Sand Shark; Longcat: Specter-Gazer.

### 09. Mimic Pooka — M4

Disguises itself as a vegetable but periodically blinks or wiggles.

**Constraint:** Adaptation: a cautious pump reveals it, so no special tool is mandatory. Keep real rewards clearly legible.

**Proposal sources:** Particle: Mimic Pooka.

### 10. Rootmaw — M5

A stationary bulb sends visible roots into nearby tunnels and produces slow spores.

**Constraint:** Pump the exposed bulb to clear all its roots. Growth and spore counts are capped.

**Proposal sources:** Astra: Rootmaw; Particle: Sporeling; Mimo: Golemite (terrain denial).

### 11. Air Cannon — M3

A pressure bolt adds one inflation stage and knocks an enemy down a tunnel.

**Constraint:** Signature tool: inflate, reposition, then crush. Soil stops the shot; tune range and knockback after the baseline is measured.

**Proposal sources:** Astra: Air Cannon; Longcat: Gale Pellet; Mimo: Pneumatic Bolt.

### 12. Drill Missile — M5

Cuts a short straight passage through soft earth, removing rock supports remotely.

**Constraint:** Hard terrain stops it; strictly limited range and ammunition. Newly opened routes also help enemies.

**Proposal sources:** Astra: Drill Missile; Mimo: Drill Launcher; Muse: Drill Harpoon; Longcat: Core Sampler.

### 13. Freeze Sprayer — M5

Freezes one enemy into a temporary block that can fall when its support is removed.

**Constraint:** Precise single-target control. Thaw warning; prevent falling blocks from trapping a player indefinitely.

**Proposal sources:** Astra: Freeze Sprayer; Muse: Frost Pump; Particle: Frost Pump; Flint: Cryo Stream.

### 14. Ricochet Disc — M5

A disc rebounds a limited number of times inside cleared spaces.

**Constraint:** Adaptation: use explicit reflective faces for predictable right-angle redirects; ordinary rebounds do not magically follow tunnel bends.

**Proposal sources:** Astra: Ricochet Disc; Particle: Rock Sling.

### 15. Sonic Lance — M5

A narrow pulse passes through enemies in one open corridor and briefly makes phasing enemies solid.

**Constraint:** Utility damage is secondary to exposing enemies for the pump. Intact soil blocks it.

**Proposal sources:** Astra: Sonic Lance; Mimo: Sonic Wave; Longcat: Air-Tickler.

### 16. Foam Launcher — M5

Places one temporary plug in an empty tunnel tile to divide a group or delay pursuit.

**Constraint:** One active plug; visible cracking before expiry. Cannot be placed on the player, an enemy, or a falling rock.

**Proposal sources:** Astra: Foam Launcher; Muse: Inkto (inverted into player utility).

### 17. Dig Bomb — M3

A flashing timed charge clears a small earth pocket, stuns nearby monsters, and releases unsupported rocks.

**Constraint:** Keep an escape window. Direct blast is dangerous to the player; rock drops supply the main lethal payoff.

**Proposal sources:** Astra: Dig Bomb; Muse: Dirt Bomb; Flint: Dynamite; Particle: Dynamite; Mimo: Standard Bomb.

### 18. Remote Charge — M4

Place one charge and detonate it with a second activation.

**Constraint:** One charge at a time; same bounded terrain rules as Dig Bomb, trading immediate use for preparation.

**Proposal sources:** Astra: Remote Charge.

### 19. Pressure Bomb — M5

A finite pressure wave follows connected open tunnels and pops already-inflated enemies.

**Constraint:** Uninflated enemies are briefly stunned. Soil blocks propagation; wave distance and branch count are bounded.

**Proposal sources:** Particle: Pressure Bomb; Astra: Tunnel Bomb.

### 20. Decoy Turnip — M4

A squeaking turnip attracts nearby monsters to a chosen junction.

**Constraint:** Choose the non-explosive version to keep it distinct from Remote Charge. Never overrides boss behavior or draws the whole map.

**Proposal sources:** Muse: Decoy Turnip; Mimo: Decoy Bomb; Particle: Bait Bomb.

### 21. Cryo Bomb — M5

Briefly freezes a small group, buying time to prepare a rock drop.

**Constraint:** Distinct from Freeze Sprayer: frozen enemies stay in place and thaw; they do not become movable ice blocks.

**Proposal sources:** Flint: Ice Bomb; Particle: Cryo Bomb; Mimo: Flash Bomb (crowd-control role).

### 22. Turbo Hose — M2

Faster inflation at shorter reach.

**Constraint:** Selectable between zones. The first weapon experiment can use only a speed change before a range trade-off is implemented.

**Proposal sources:** Muse: Turbo Hose; Longcat: Brisk.

### 23. Long Tom Hose — M4

Longer reach with slower inflation.

**Constraint:** Preserves the commitment of a tethered pump; avoid unlimited distance.

**Proposal sources:** Muse: Long Tom Hose; Longcat: Lance Pump.

### 24. Tri-Pump — M5

A short spread can engage multiple adjacent enemies, with slower pumping.

**Constraint:** Needs wide open space; soil blocks each prong independently. Standard pump remains available as the default.

**Proposal sources:** Muse: Scatter Pump; Longcat: Wide Boy.

### 25. Crystal Caverns — M6

Readable crystal faces redirect selected shots; hard mineral veins constrain excavation.

**Constraint:** Fixed reflector orientations. Limit reflected enemy attacks and show their charge paths.

**Proposal sources:** Astra: Crystal Caverns; Flint: Crystal Caverns; Mimo: Crystal Caverns; Longcat: Crystal Warrens.

### 26. Frozen Depths — M6

Cracked ice supports can break, dropping icicles or previously frozen monsters.

**Constraint:** Choose brittle supports over forced sliding: retain precise movement. Introduce the hazard without requiring Freeze Sprayer.

**Proposal sources:** Astra: Frozen Depths; Hydrogen: Permafrost Glacier; Muse: Crystal Frost Mines.

### 27. Fungal Hollows — M6

Breached spore pockets release slow, temporary clouds; roots regrow in marked areas.

**Constraint:** No darkness requirement. Cap cloud coverage; players must always retain a usable escape route.

**Proposal sources:** Astra: Fungal Hollows; Particle: Spore Forest; Longcat: Root Labyrinth.

### 28. Sunken Temple — M6

Permanent stone chokepoints and visibly cracked pillars create planned ceiling collapses.

**Constraint:** Adaptation: water is initially visual. Full flooding is deferred; every reachable enemy must remain defeatable.

**Proposal sources:** Hydrogen: Sunken Jungle Ruins; Mimo: Ancient Ruins; Flint: Ancient Sunken Ruins; Muse: Sunken Temple.

### 29. Lost Machinery — M6

Timed valves and air jets propel enemies and loose objects through marked tunnels.

**Constraint:** Fixed jet directions and warning lamps. Avoid combining conveyors, teleporters, and jets in the same introductory stage.

**Proposal sources:** Astra: Lost Machinery; Hydrogen: Subterranean Cyber-Factory; Muse: Neon Mole City.

### 30. Molten Core — M6

Small marked lava pockets drain a limited distance into connected lower cells when breached.

**Constraint:** Discrete, capped tile updates rather than free fluid simulation. No surprise global rising-lava timer.

**Proposal sources:** Astra: Molten Core; Hydrogen: Magma Core; Flint: Magma Tunnels; Particle: Cinder Caverns.

### 31. King Pooka — M6

A giant inflatable Pooka alternates a charge with a vulnerable inhale and releases a limited number of minions.

**Constraint:** First boss candidate. Visible inflation stages communicate damage; cap adds.

**Proposal sources:** Longcat: King Pooka; Muse: Queen Pookarina; Mimo: Gigantor; Particle: Great Pooka.

### 32. King Fygar — M7

Bait a fire attack, dig around it, and pump exposed air sacs before a finishing rock drop.

**Constraint:** One fully visible arena. Regenerate required rocks safely so the encounter cannot become unwinnable.

**Proposal sources:** Astra: King Fygar; Hydrogen: King Fygar; Muse: King Fygar Inferno.

### 33. Iron Mole — M7

A drilling machine cuts new routes; dropped rocks break its armor and expose pumpable bellows.

**Constraint:** Show its next route before movement. Use a small number of destructible support points.

**Proposal sources:** Astra: Iron Mole; Muse: MOTHERBRAIN Mole Tank; Particle: Drill Automaton.

### 34. World Worm — M7

A segmented worm crosses along telegraphed routes; inflate exposed segments to drive it into a collapse trap.

**Constraint:** Largest implementation risk among bosses. Segment count must fit actual rendering, RAM, and CPU budgets.

**Proposal sources:** Astra: World Worm; Hydrogen: Leviathan Drill-Worm; Mimo: Queen Boreworm.

### 35. Hard Hat — M4

A pickup absorbs one hit, breaks visibly, and grants brief recovery invulnerability.

**Constraint:** Optional protection, not a universal health bar. Decide explicitly how crush damage interacts with it.

**Proposal sources:** Muse: Hard Hat; Hydrogen: Hardhat Shield.

### 36. Tunnel Boots — M4

A timed boost increases movement in already-dug tunnels.

**Constraint:** Adaptation: normal digging speed and responsive grid alignment are retained.

**Proposal sources:** Muse: Spiked Boots; Mimo: Dig Speed Boost; Particle: speed boots.

### 37. Soil Scanner — M4

Temporarily highlights buried supplies and marked hazard pockets.

**Constraint:** Information tool only. Essential hazards remain readable without it; ordinary item hiding is part of this feature.

**Proposal sources:** Mimo: Soil Scanner; Mimo: Sonic Wave (item reveal).

### 38. Bonus Balloon — M6

A surface balloon cycles equipment icons when pumped; another hit locks in a reward.

**Constraint:** One cycling reward system replaces competing capsule schemes. No permanent weapon XP tree.

**Proposal sources:** Muse: Bonus Balloon; Hydrogen: Drill-Saucer capsules; Particle: weapon capsules.

### 39. Pop Chain — M4

Successive kills within a short window build a capped multiplier.

**Constraint:** Tune the timer in playtests. Boss minions and repeatedly split enemies cannot generate unlimited bonuses.

**Proposal sources:** Longcat: Pop Chain; Particle: Chain Pop; Mimo: Combo Chain.

### 40. Technique Bonus — M3

Extra points for combining actions on the same target: inflate, launch, then crush, or freeze then drop.

**Constraint:** Uses explicit recent-action flags. Preserve existing depth and rock scoring; new bonuses are additive and bounded.

**Proposal sources:** Astra: inflate-launch-crush; Mimo: shatter and cascade bonuses.

### 41. Clean Clear — M4

A stage-end bonus for finishing without a hit.

**Constraint:** A shield hit forfeits it. This rewards control alongside aggressive chains.

**Proposal sources:** Mimo: no-damage clear bonuses.

### 42. Garden Panic — M6

Intercept vegetable-stealing monsters and recover their oversized crops before time expires.

**Constraint:** Adaptation: score-only, no lost lives. Use existing movement and pumping wherever possible.

**Proposal sources:** Astra: Garden Panic; Muse: Fruit Rescue; Hydrogen: Farm Defense; Longcat: Crop Mutation (vegetable theme).

### 43. Rockfall Rally — M4

Clear a chamber with a limited number of rocks and carefully dug release paths.

**Constraint:** A compact puzzle using the established mechanics. No new combat weapon required.

**Proposal sources:** Astra: Rockfall Rally; Particle: Rock Drop; Mimo: Crush Frenzy.

### 44. Pressure Test — M4

Inflate a timed sequence of balloon monsters without letting unfinished targets deflate.

**Constraint:** Score-only challenge that teaches pump commitment and changing targets.

**Proposal sources:** Astra: Pressure Test; Particle: Vegetable Garden (timed inflation).

### 45. Co-op Rescue — M8

Two diggers share a playfield; one can free the other from an enemy capture.

**Constraint:** Optional major expansion. Requires a second player state, input path, collision rules, and rescue behavior; exclude from initial ROM milestone.

**Proposal sources:** Particle: Co-op capture rescue; Longcat: co-op revival; Mimo: Co-op.

### 46. Boss Rush — M7

Replay the four bosses with a fixed loadout and a separate score.

**Constraint:** Unlock or expose only after all bosses exist. No extra bosses are hidden in this item.

**Proposal sources:** Mimo: Boss Rush; Particle: Boss Rush.

### 47. Reactive Music — M7

Movement-linked music gains or changes a layer when a boss or dangerous situation is active.

**Constraint:** Budget the new MVS sound driver and assets first. Use small pattern changes if extra voices or storage are unavailable.

**Proposal sources:** Astra: movement-linked music; Particle: layered stratum music; Hydrogen: walking-theme remix.

### 48. Expanded Combat Animation — M7

Additional anticipation, inflation, armor-break, freeze, and defeat poses make new states readable.

**Constraint:** Use a coherent sprite budget and distinct silhouettes; preserve the original game's readable scale.

**Proposal sources:** Astra: warning animations and physical boss changes; Particle: presentation; Muse: cartoon sequel tone.


## 15. References and provenance

Technical documentation checked while preparing this handoff; pin revisions during implementation.

- [ngdevkit](https://github.com/dciabrin/ngdevkit): SDK, hardware headers, startup/runtime, graphics tools and sound toolchain.
- [ngdevkit examples](https://github.com/dciabrin/ngdevkit-examples): boot, sprites, palettes, audio, attract/game flow, credits and backup-RAM examples. Inspect examples under their supplied licenses.
- [Neo Geo general specifications](https://wiki.neogeodev.org/index.php/General_specifications): CPU, work RAM and sound overview.
- [Neo Geo 68k memory map](https://wiki.neogeodev.org/index.php/68k_memory_map): cartridge regions and BIOS-reserved work RAM.
- [Neo Geo sprites](https://wiki.neogeodev.org/index.php/Sprites): tile/strip format and scanline limit.
- [Neo Geo VRAM](https://wiki.neogeodev.org/index.php/VRAM): attribute/tile-map storage and access timing.
- [Neo Geo display timing](https://wiki.neogeodev.org/index.php/Display_timing): native display geometry and timing.
- [MAME command-line documentation](https://docs.mamedev.org/commandline/commandline-all.html): configuration inspection and runtime options.
- [MAME debugger](https://docs.mamedev.org/debugger/index.html): target debugging.
- [MAME source repository](https://github.com/mamedev/mame): authoritative loading definitions for the pinned emulator revision.

Design source: **Super-Dig-Dug-Curated-48.md**, selected from:
- digdug__astra.txt
- digdug__flint.txt
- digdug__hydrogen.txt
- digdug__longcat.txt
- digdug__mimo.txt
- digdug__muse.txt
- digdug__particle.txt

This handoff is self-contained for implementation. The raw pitches are optional context and do not override the selected mechanics or confirmed hardware.
