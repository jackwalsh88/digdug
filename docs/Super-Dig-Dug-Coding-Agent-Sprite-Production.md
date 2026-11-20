# Super Dig Dug — Sprite and Tile Production Guide for the Coding Agent

Version 1.0 • November 17, 2026  
Target: **Neo Geo MVS inside MAME**  
Companion: **Super-Dig-Dug-ChatGPT-Image-Generation-Guide.md**  
Gameplay authority: **Super-Dig-Dug-Neo-Geo-MVS-Handoff.md**

## Mission

Create the complete visual asset set for Super Dig Dug and a repeatable conversion pipeline. Use image-generation concepts as visual references, editable pixel-art masters as the production source, and validated ROM graphics as the runtime result.

This is a production specification. The files do not contain finished sprites or a working converter. Begin with the small B0/B1 set and a MAME art-viewer ROM, then expand through the catalog. Do not wait for every concept to be supplied before building placeholders and technical infrastructure.

The project is a new MVS game, not a patch to the 1982 Dig Dug ROM. No original ROM is needed to begin asset authoring. Preserve the existing gameplay and feature IDs.

## 1. Responsibilities and authoritative sources

| Stage | Owner | Result |
|---|---|---|
| Visual exploration | ChatGPT image generation and user art direction | Named concept images and pose references |
| Pixel construction | Coding agent using Aseprite/Lua or deterministic pixel data, with visual review | Native-grid editable sprites |
| Animation | Coding agent and art review | Consistent frames, tags, anchors and durations |
| Exact terrain generation | Coding agent | Collision-aligned occupancy and adjacency variants |
| Conversion/packing | Coding agent | C-ROM sprite data, S-ROM FIX data, palettes and runtime tables |
| Acceptance | Native-size review and MAME tests | Verified display, state readability and budgets |

Existing concepts:
- **Armored Mecha-Pooka pixel sprite.png** — reference for `enm_mecha_pooka`.
- **Pixel Air Cannon Pickup.png** — reference for `tool_air_cannon`.

If those images are absent, use the written art briefs and simple pixel placeholders; ask for the actual images only when visual matching is necessary. Do not claim to have inspected an unavailable image.

## Shared visual specification

These are production defaults for a **320×224, single-screen Neo Geo MVS** game. Confirm scale in the running arena before finishing the entire set. The gameplay handoff remains authoritative for mechanics; this guide expands the art workflow without adding weapons or enemy types.

- Bright early-1990s arcade pixel art: compact silhouettes, readable faces, playful industrial machinery and exaggerated inflation.
- Screen-plane view of the side-cut underground arena. Individual creatures can have a slight three-quarter face, but no isometric ground, camera tilt or perspective shrinking.
- One-pixel logical dark contours where useful; upper-left highlights; two or three deliberate shade bands per material.
- No soft gradients, smooth alpha edges, photographic surfaces, painterly noise, realistic firearm styling or baked CRT scanlines.
- Character references: round red body, brass goggles, cyan lenses and gunmetal armor for Mecha-Pooka; cream casing, red tank, brass gauge and broad steel nozzle for Air Cannon.
- Existing generated images are concepts. They were not verified as palette-limited, aligned sprites or production alpha cutouts.
- Ordinary actors use a **32×32 source canvas** initially; the visible body can be 16–24 pixels across. A 32×32 canvas does not imply a 32×32 collision box. Smaller shapes should stay small.
- Inflation may expand to 48×48. Bosses are composed from several tiles or parts. Native size is separate from the enlarged image-generation output.
- Objects that block movement, objects that warn of danger, and harmless decorations need different silhouettes. Never rely only on color to explain state.
- The player always retains ordinary pumping. Artwork must not imply that an enemy requires a specific consumable to defeat.
- Directional gameplay is up/down/left/right. Author right/up/down views where needed; a deliberate horizontal mirror may supply left. Do not rotate a standing creature 90 degrees to make it face up.
- Fonts, scores, timers, equipment labels and menu text are assembled from exact glyphs by the coding agent.

### Proposed shared metal/red/cyan palette

This is an editable art palette, not pre-encoded Neo Geo palette-register data. Preserve meaningful color roles across frames; derive separate green, purple and terrain palettes as needed.

| Index | Color | Role |
|---:|---|---|
| 0 | transparent | Fully transparent pixels; RGB payload is irrelevant |
| 1 | #161923 | Outline |
| 2 | #313543 | Deep metal shade |
| 3 | #5C6375 | Steel midtone |
| 4 | #A6B0C0 | Steel light |
| 5 | #F3F0D6 | Cream/highlight |
| 6 | #6F411E | Brass shadow |
| 7 | #BA7B27 | Brass |
| 8 | #F0C451 | Gold highlight |
| 9 | #7C1730 | Red shadow |
| 10 | #D82C42 | Red |
| 11 | #FF6470 | Red highlight |
| 12 | #176779 | Cyan shadow |
| 13 | #61CCD4 | Cyan |
| 14 | #B6F1E8 | Cyan highlight |
| 15 | #EE7A25 | Orange accent |

Use one 16-entry palette per ordinary character family as the initial authoring rule. The hardware uses palettes per tile; this rule does not mean the whole game has only 15 visible colors. Larger composed assets may use several explicitly budgeted palettes. In the final exporter, map RGB colors to representable hardware values and review the resulting colors.

## Shared asset IDs and naming

The catalog below is identical in both art guides. Each entry is an **asset family**, not one PNG. A family can include a master, direction variants, animation frames, icons, projectiles and overlays.

Use stable IDs such as `enm_mecha_pooka` and `tool_air_cannon`. Suggested child naming:

- Concept: `enm_mecha_pooka__master__v001.png`
- Pose reference: `enm_mecha_pooka__inflate_02__right__v001.png`
- Editable master: `enm_mecha_pooka.aseprite`
- Production sheet: `enm_mecha_pooka.png`
- Metadata: `enm_mecha_pooka.json`
- Child effect: `enm_rootmaw__root_corner`
- Review image: `enm_mecha_pooka__review_1x_8x.png`

The filenames are desired delivery names, not an assumption that an image-generation tool lets you set its output path. Preserve a mapping from actual outputs to asset IDs.

Feature numbers refer to the 48-addition design. “base” means an original/core asset not counted as a new feature. Feature 48 applies to animation across the catalog. Feature 47 is primarily audio; it does not require an invented collectible.

## Shared production batches

| Batch | Goal | Families to prioritize |
|---|---|---|
| B0 | Terrain/render proof | topsoil, rocks, dig dust, font |
| B1 | Coherent baseline | P1, Pooka, Fygar, Mecha-Pooka, standard pump, Turbo Hose, pump/fire effects, rewards, HUD |
| B2 | Signature slice | Air Cannon, Dig Bomb, air/blast/status/score effects, equipment menu, screen frames |
| B3 | Tactical variety | Borer, Clod, Goopy, Gecko, Mimic, Remote Charge, Decoy, Long Tom, hat/boots/scanner, two small bonuses |
| B4 | Advanced mechanics | Fusebug, Volty, Echo, Rootmaw, remaining tools/modules/bombs and their effects |
| B5 | World identity | six biome families, world cards, Bonus Balloon, Garden Panic |
| B6 | Bosses and presentation | four bosses, logo, ending and final animation polish |
| B7 | Co-op | P2, capture/rescue overlays and two-player presentation |

Batch order is for art dependencies. M-numbers in the catalog refer to the game-code roadmap. Early versions of effects can precede the gameplay milestone that finishes them. Reuse existing families instead of duplicating them under a new name.

### State completeness rules

- **Enemy common states:** idle, locomotion where applicable, attack warning/attack/recovery if applicable, each gameplay inflation stage, deflation presentation, stun/hurt, defeat/pop and crushed presentation. Add phasing only to enemies whose AI actually supports it.
- Each enemy's common states may be shared, mirrored, reused or intentionally absent when its mechanics make a state impossible; record that decision. Stationary Rootmaw does not need a walk cycle.
- Inflation stages come from gameplay data. Four art stages are a reasonable prototype, but the approved engine count controls delivery; Mecha-Pooka needs its extra stage.
- **Tool pack:** pickup image, simplified HUD icon, held attachment or emission socket, activation/recoil if applicable, projectile/area effect, impact/end state.
- **Biome pack:** soil masks, hard boundary material, tunnel edges, surface/arena trim, decorative tiles, hazard warning/active/expiry states, and relevant falling/broken parts.
- All stated frame counts are starting budgets, not mandatory padding. Never add fake duplicate frames merely to meet a count.
- Warning and collision-critical frames take priority over extra decoration.


## 2. Pixel-authoring procedure

### A. Establish the master at native size

1. Choose the catalog canvas and an explicit gameplay footprint.
2. Draw the silhouette in one color. Check it at 1× against light soil, dark tunnels and a busy scene.
3. Add the face and role-defining feature: goggles, drill nose, shovel hands, nozzle or fuse.
4. Assign the family palette. Add two or three shade bands and only the highlights that survive native-size viewing.
5. Compare beside P1, ordinary Pooka, one rock and one terrain tile.
6. Preserve the editable master before creating animations.

Do not treat a 1024-pixel image with a pixel-art aesthetic as a 32-pixel source. Reduction can be a rough guide, but the final silhouette and pixel clusters need reconstruction. Automatic palette reduction alone cannot guarantee readable art.

Code can create the initial pixels through explicit indexed arrays, simple shape masks and Aseprite Lua. Keep source descriptions or scripts versioned. Use your available visual tools to inspect the actual result; compilable code does not prove good art.

Aseprite is the preferred editable source format. If unavailable, use indexed PNG frames plus a documented palette and JSON metadata; continue work and explain the format. Do not fabricate an .aseprite file by changing a PNG extension.

### B. Create animation from the same master

Duplicate and alter the approved sprite rather than generating unrelated characters for every frame.

- Walking: preserve body mass, face and helmet geometry; alternate feet and a small body bob.
- Inflation: widen the body, lift armor and spread the feet; preserve clear goggles and identifiable anatomy.
- Warning: change posture before the attack begins. Do not depend exclusively on flashing color.
- Death: distinguish popped, crushed and ordinary defeat only where gameplay uses those outcomes.
- Status: prefer reusable stars, hard-edged ice or explicit palette changes over many duplicate full-character sheets.
- Equipment: attach to a named player socket. A large pickup illustration must not become an equally large held weapon.
- Up/down views require appropriate anatomy and socket placement. Right/left mirroring needs review if a character has asymmetric armor or text.

Store animation tags, integer frame durations and loop/one-shot behavior. Convert authoring milliseconds to native game ticks offline with a documented rounding policy; do not assume exactly 60 Hz.

### C. Stable anchors and frame bounds

For each frame record a pivot in source-canvas coordinates. Use a foot/contact anchor for ground actors and a defined center or mount for floating actors, projectiles and attachments.

A 32×32 normal frame and a 48×48 inflated frame can have different numeric pivots but the same world-space anchor. Enlarging a canvas must not make the monster jump.

Start with fixed-grid frame exports without automatic trimming or rotation. Later deduplication or trimming must preserve offsets and anchors. Keep hitboxes and emission sockets as explicit metadata; derive neither from nontransparent bounds at runtime.

### D. Distinct forms with reuse

Palette swaps are appropriate for ordinary color variations and P2 accents, but every gameplay-significant variant needs a silhouette or animation cue. Mecha-Pooka needs visible armor. A crystal reflector needs a clear face angle. A dangerous spore pocket cannot look identical to a harmless mushroom.

Keep bosses modular. Reuse Pooka minions, rock debris, fire pieces and terrain materials. World Worm is a library of segments, not a giant animated PNG covering the screen.

## 3. Terrain and hazard production

Implement the terrain logic in the gameplay handoff. The default is 8×8 occupancy cells grouped into 16×16 visual tiles.

### Exact mask convention

For each visual tile, bits represent filled solid-earth quadrants:

| Bit | Position |
|---:|---|
| 0 | Top left |
| 1 | Top right |
| 2 | Bottom left |
| 3 | Bottom right |

Mask 0 is fully excavated; mask 15 is fully filled. The generator and runtime must use the same convention, ideally from a shared generated definition. Do not infer collision from painted pixels.

For each material:
1. Author a small repeatable soil texture and a restrained edge treatment.
2. Generate all 16 occupancy masks deterministically.
3. Fill only occupied quadrants. Exposed tunnel area is transparent when a separate back layer is used.
4. Render edge highlights inside solid quadrants, not as fake obstacles protruding into traversable space.
5. Use neighboring occupancy to suppress highlights at internal joins. Sixteen masks cover occupancy, not every possible decorative adjacency case.
6. Add a small set of solid texture variations. Decorative choices must never change collision.
7. Generate a test layout covering all neighboring mask combinations and inspect for seams.
8. Add refill, crack and hazard animation layers without changing the mask convention.

The engine can display these tiles through background sprite strips. The FIX layer is a foreground text layer; do not place the dirt there and cover the actors accidentally.

Terrain occupies sprite resources too. Use vertical strips of tile references rather than one strip per tile when the renderer supports it.

### Hazard states

For every interactive prop supply at least:
- safe/inactive;
- warning;
- active;
- spent, broken or recovering.

Provide the actual mechanic's parts: support break and icicle for Frozen Depths; reflector orientations for Crystal Caverns; pillar fragments for Sunken Temple; valve and directional jets for Lost Machinery; root/spore states for Fungal Hollows; bounded lava edge/flow pieces for Molten Core.

Decorative water does not imply a flood mechanic. Do not add gravity devices, teleports or other unselected systems through art.

## 4. Hardware-aware color and tile packing

Neo Geo sprite tiles are 16×16 at 4 bits per pixel, with index 0 transparent. Larger objects use multiple strips. FIX glyphs are 8×8 and have their own layout. Sprite data and FIX data require different converters.

Rules:
- Final indexed art has deliberate palette indices. Preserve the same role ordering across a family's animation.
- Production alpha is binary: transparent or opaque. Flag intermediate alpha for cleanup.
- Do not let an image quantizer allocate opaque colors to index 0.
- Each tile must use a valid 16-entry palette. Record palette selection per tile if a composed asset requires more than one.
- Convert RGB to Neo Geo palette words through a documented tested routine. Review quantization; do not assume ordinary packed RGB555 bit order matches the hardware.
- Reserve FIX-compatible palette slots for HUD text and respect the FIX layer's palette restrictions.
- Default to no dithering on characters. Patterned shading can be used sparingly in terrain after native-size review.
- A 32×32 character normally uses two 16-pixel-wide strips. A 48×48 pose needs three; count its worst inflation state.
- Aim below the handoff's 80-strip-per-line working budget; 96 is the hardware limit. Include terrain, bosses, overlays and effects.
- Export maxima and a worst-case scene report. A total tile count does not substitute for a scanline-strip calculation.

The palette/image format checks below are required before marking an asset production-ready.

## 5. File structure and metadata

Suggested folders:

| Path | Purpose |
|---|---|
| `assets/concepts/` | Unmodified image-generation references and reference metadata |
| `assets/source/characters/` | Editable character masters |
| `assets/source/equipment/` | Tools, bombs, modules and pickups |
| `assets/source/terrain/` | Material masters and exact mask generator inputs |
| `assets/source/effects/` | Modular particles, trails and warnings |
| `assets/source/ui/` | Font, symbols, panels and corrected logo |
| `assets/palettes/` | Named palettes and hardware-mapped equivalents |
| `assets/export/` | Native indexed PNG sheets plus metadata |
| `assets/generated/` | Packed ROM tiles and runtime tables |
| `assets/review/` | 1×/integer-scale previews and animation loops |
| `tools/assets/` | Validators, generators and packers |

Manifest example; numbers are illustrative, not fixed game balance:

```json
{
  "asset_id": "enm_mecha_pooka",
  "feature_ids": [1, 48],
  "status": "pixel_master",
  "source": "assets/source/characters/enm_mecha_pooka.aseprite",
  "palette_id": "metal_red_cyan_v1",
  "tile_format": "neogeo_sprite_16x16_4bpp",
  "frames": [
    {
      "id": "walk_right_00",
      "canvas": [32, 32],
      "pivot": [16, 28],
      "hitbox": [-8, -16, 16, 16],
      "duration_ticks": 6,
      "sockets": {"hit": [0, -12]}
    }
  ],
  "animations": {
    "walk_right": {"frames": ["walk_right_00"], "loop": true}
  }
}
```

Use a documented hitbox convention: here x/y are offsets from the pivot and the last two values are width/height; socket coordinates are also pivot-relative. A real walk animation needs its remaining frames before it is complete.

Track status as:
`missing → concept → pixel_master → animated → exported → rom_tested → approved`.
Keep approval by the user distinct from technical validation; never infer it from generation success.

## 6. Build pipeline

1. Export the editable masters to native-resolution indexed sheets.
2. Export animation tags and frame metadata.
3. Validate indices, dimensions, pivots and references.
4. Generate terrain-mask variants and exact UI glyph compositions.
5. Deduplicate tiles while preserving palette identity and any explicit flip metadata.
6. Encode sprite graphics into the chosen C-ROM layout and FIX art into S-ROM layout using the proven SDK conventions.
7. Emit palettes and compact animation/metasprite tables.
8. Decode representative packed tiles back to indexed pixels and compare them to the input.
9. Build the diagnostics/game ROM and inspect in MAME.

Aseprite supports batch PNG+JSON export. Example interface to adapt to the pinned executable:

```sh
aseprite --batch assets/source/characters/enm_mecha_pooka.aseprite \
  --sheet-type rows --format json-array \
  --sheet assets/export/enm_mecha_pooka.png \
  --data assets/export/enm_mecha_pooka.json
```

This exports a sheet; it does not by itself enforce palettes, include every custom socket field, or produce Neo Geo ROMs. Merge project-specific metadata deliberately. Pin exporter versions and keep the conversion deterministic.

Implement commands such as `make assets`, `make asset-check`, `make asset-preview` and `make art-viewer`. These are requested project commands, not existing ngdevkit commands.

A coded bitplane encoder needs known-answer tests for each quadrant, palette bit and C-ROM half. Do not let an encoder and decoder with the same bug “verify” each other; compare a known SDK-generated tile and the emulator display.

## 7. Validation and review

### Automated rejection conditions

- Missing state referenced by the engine.
- More palette entries than allowed for a tile or index 0 used as an opaque color.
- Non-binary alpha, unintended smoothing, unsupported dimensions or misaligned exports.
- Changed palette ordering between frames without explicit remapping.
- Unresolved pivots, off-canvas sockets or obviously invalid collision bounds.
- Missing/inconsistent animation durations.
- Duplicate asset IDs or overlapping packed ranges.
- Sprite-strip or palette budget overflow in a representative scene.
- Generated terrain occupying the wrong quadrants.
- Incorrect C/S packing or untracked dependency/version changes.

### Visual acceptance

Inspect at 1× and at a nearest-neighbor enlarged scale:
- Is the silhouette understandable?
- Are movement, inflation, vulnerability and attack timing readable?
- Do attachments stay connected?
- Do inflated monsters remain distinguishable from ordinary enemies?
- Are warnings visible against all seven terrain families?
- Do tile edges join without seams?
- Are HUD digits legible without zoom?
- Does an animation preserve position rather than jitter?
- Does the game still look coherent with two players, several enemies and effects?

Build an MAME asset viewer with background selection, animation selection, frame advance, pivot/hitbox/socket overlays and strip/palette reports. Keep a plain presentation mode without CRT filters for diagnosis.

## 8. Delivery and first assignment

For each finished family deliver:
- editable master or documented indexed-frame fallback;
- palette;
- native indexed sheet;
- metadata and animation tags;
- 1×/enlarged contact sheet and animation preview;
- conversion output and manifest;
- MAME-tested status with any remaining visual issues.

Start with B0 and B1: one soil family, one rock, P1, Pooka, Fygar, Mecha-Pooka, standard pump/Turbo Hose, core effects and a tiny HUD. Prove them together before producing all biome and boss art.

When an AI concept fails, preserve it as reference and improve the native sprite. When a tile/hazard fails, fix the authoritative mask or state mapping. Do not compensate for a collision bug by repainting a misleading warning.

## 9. Complete shared asset catalog

Native dimensions are proposed production canvases. Animation counts are provisional budgets. The briefs also define the subject descriptions used by ChatGPT; both guides intentionally share these IDs.


### Characters

#### chr_player_1

- **Feature IDs:** base; animation also contributes to 48.
- **Target native canvas:** 32×32; 48×48 death if needed.
- **Art batch / game milestone:** B1 / M2.
- **Visual brief:** Taizo-inspired compact digger: cream helmet with cyan visor, white suit, red gloves/boots and small orange accents; stubby readable proportions.
- **Required states/components:** idle 2; walk 4; dig 4; pump 3; hurt 2; death 4; victory 2; up/down/right views; left may mirror. Add special-use socket poses and capture/rescue later.

#### chr_player_2

- **Feature IDs:** 45; animation also contributes to 48.
- **Target native canvas:** same as chr_player_1.
- **Art batch / game milestone:** B7 / M8.
- **Visual brief:** A matching junior digger with cobalt-blue gear and a distinct helmet stripe; readable beside P1 without relying only on color.
- **Required states/components:** Reuse the locomotion rig with recolor and a silhouette accent; capture 2; struggling 2; rescued 2; join/ready pose. Do not generate a new art style.

#### enm_pooka

- **Feature IDs:** base; animation also contributes to 48.
- **Target native canvas:** 32×32 normal; 48×48 inflated.
- **Art batch / game milestone:** B1 / M2.
- **Visual brief:** Round red goggle-eyed burrower with orange feet and brass-rimmed pale cyan goggles; simpler and less armored than Mecha-Pooka.
- **Required states/components:** Enemy common states; walk 2; inflation stages driven by game data; deflation reuses stage art; phase-eye cue; pop and crushed states.

#### enm_fygar

- **Feature IDs:** base; animation also contributes to 48.
- **Target native canvas:** 32×32 normal; 48×48 inflated.
- **Art batch / game milestone:** B1 / M2.
- **Visual brief:** Squat green cartoon underground dragon, orange snout/belly, small wings, clear horizontal fire-breath silhouette.
- **Required states/components:** Enemy common states; walk 2–4; inhale warning 2; breathe 2; recovery 2; flame belongs to fx_enemy_attacks.

#### enm_mecha_pooka

- **Feature IDs:** 01; animation also contributes to 48.
- **Target native canvas:** 32×32 normal; 48×48 inflated.
- **Art batch / game milestone:** B1 / M2.
- **Visual brief:** Follow the existing Mecha-Pooka concept: round red belly, riveted gunmetal helmet, brass goggles, cyan lenses and orange feet; one small blunt spike.
- **Required states/components:** Common states plus extra inflation pose, helmet-lift, armor crack and rear vulnerability. First gameplay version uses the extra inflation stage; directional armor is later.

#### enm_borer_beetle

- **Feature IDs:** 02; animation also contributes to 48.
- **Target native canvas:** 32×32.
- **Art batch / game milestone:** B3 / M4.
- **Visual brief:** Ochre beetle with a compact steel drill nose, dark segmented shell and stout digging legs; front silhouette unmistakable.
- **Required states/components:** walk 4; brace 2; bore 4; recover 2; common vulnerability/death states; nose rotation and dirt chips separate.

#### enm_clod

- **Feature IDs:** 03; animation also contributes to 48.
- **Target native canvas:** 32×32.
- **Art batch / game milestone:** B3 / M4.
- **Visual brief:** Squat terracotta creature with shovel-shaped forearms and pale stone eyebrows; broad hands make its tunnel-refill role visible.
- **Required states/components:** walk 4; scoop 2; pack soil 3; recover; common inflation/death. Newly packed earth is in terrain sheets.

#### enm_goopy

- **Feature IDs:** 04; animation also contributes to 48.
- **Target native canvas:** 32×32 parent; 16×16 children; 48×48 inflation.
- **Art batch / game milestone:** B3 / M4.
- **Visual brief:** Blue jelly blob with a pale cyan belly highlight, expressive eyes and two lumpy feet; two smaller offspring retain its face language.
- **Required states/components:** wobble 4; inflation stages; split 4; mini-walk 2; slow slime trail pieces; common death. Fully completed pumping kills cleanly.

#### enm_fusebug

- **Feature IDs:** 05; animation also contributes to 48.
- **Target native canvas:** 32×32; 48×48 inflation.
- **Art batch / game milestone:** B4 / M5.
- **Visual brief:** Charcoal beetle with an amber glass abdomen and visible fuse coil; warning readable as a changing silhouette and pulsing core.
- **Required states/components:** walk 4; armed warning 3; pushed/sliding 2; final flash 2; common death; explosion uses fx_blast. No invisible countdown.

#### enm_volty

- **Feature IDs:** 06; animation also contributes to 48.
- **Target native canvas:** 32×32.
- **Art batch / game milestone:** B4 / M5.
- **Visual brief:** Yellow sea-urchin creature with short chunky prongs, dark face and blue electrical accents.
- **Required states/components:** idle/walk 2; charge 3; protected spark 2; discharge 2; exhausted/vulnerable 2; common inflation/death. Spark projectile separate.

#### enm_gecko

- **Feature IDs:** 07; animation also contributes to 48.
- **Target native canvas:** 32×32.
- **Art batch / game milestone:** B3 / M4.
- **Visual brief:** Violet cave gecko with large sticky toes, curved tail and light belly; silhouette reads upside down while clinging.
- **Required states/components:** ceiling crawl 4; tail-twitch warning 2; drop 2; land 2; ground recovery 2; common inflation/death. Draw clinging posture deliberately.

#### enm_echo

- **Feature IDs:** 08; animation also contributes to 48.
- **Target native canvas:** 32×32.
- **Art batch / game milestone:** B4 / M5.
- **Visual brief:** Pale teal spectral creature with large listening ear-fins and bright eyes; hollow patterned body in tracking form and clear solid outline when vulnerable.
- **Required states/components:** listening 2; phased drift 4; materialize 3; attack 2; solid recovery 2; inflation/death. Use hard pixel patterns, not partial alpha.

#### enm_mimic_pooka

- **Feature IDs:** 09; animation also contributes to 48.
- **Target native canvas:** 32×32; disguise matches pickup scale.
- **Art batch / game milestone:** B3 / M4.
- **Visual brief:** A vegetable-shaped disguise derived from an existing turnip pickup, with subtly blinking goggle eyes and a red creature revealed beneath.
- **Required states/components:** disguise idle 1; tell/blink 2; reveal 3; walk 2; inflation/death. Reuse the actual vegetable shape so the disguise is credible.

#### enm_rootmaw

- **Feature IDs:** 10; animation also contributes to 48.
- **Target native canvas:** 32×32 bulb; modular 16×16 roots.
- **Art batch / game milestone:** B4 / M5.
- **Visual brief:** Stationary magenta root bulb with a pale toothy opening, green crown leaves and warm gold root tips.
- **Required states/components:** idle 2; root growth 3; spit warning 2; spit 2; vulnerable bulb; inflation/death; root straight/corner/end/junction pieces and retract states.

### Bosses

#### boss_king_pooka

- **Feature IDs:** 31; animation also contributes to 48.
- **Target native canvas:** 64×64 normal; 80×80 maximum inflation.
- **Art batch / game milestone:** B6 / M6.
- **Visual brief:** Large crowned Pooka whose goggles and swollen red body stay readable; crown can be a small separate overlay.
- **Required states/components:** idle 2; inhale 3; charge warning 2; charge 3; summon 2; distinct inflation/damage stages; stunned 2; defeat 5. Reuse enm_pooka minions.

#### boss_king_fygar

- **Feature IDs:** 32; animation also contributes to 48.
- **Target native canvas:** 96×64 composed; separate 32×32 cheek sacs.
- **Art batch / game milestone:** B6 / M7.
- **Visual brief:** Broad green dragon with orange air sacs, massive goggles-like brows and a clear horizontal snout; compact within one arena.
- **Required states/components:** idle 2; inhale/fire warning 3; breathe 3; exposed sacs; inflated sacs; stunned 2; armor/damage variants; defeat 5. Fire parts modular.

#### boss_iron_mole

- **Feature IDs:** 33; animation also contributes to 48.
- **Target native canvas:** 96×64 composed from modules.
- **Art batch / game milestone:** B6 / M7.
- **Visual brief:** Rusted cream-and-gunmetal digging machine, brass drill cone, red hazard lamps, tank treads and visible accordion cooling bellows.
- **Required states/components:** chassis idle; tread 4; drill 4; route-warning marker; armor intact/cracked/open; bellows inflate; stunned; defeat components.

#### boss_world_worm

- **Feature IDs:** 34; animation also contributes to 48.
- **Target native canvas:** 32×32 head/body/tail modules; optional 48×48 inflated module.
- **Art batch / game milestone:** B6 / M7.
- **Visual brief:** Segmented deep-earth worm with ochre stone plates and coral flexible joints; visible inflateable soft segments.
- **Required states/components:** Head 4 facing variants; body straight/corner modules; tail; burrow warning; exposed/inflated/cracked segment states; collapse/defeat. Never one enormous whole-worm raster.

### Equipment

#### tool_standard_pump

- **Feature IDs:** base; animation also contributes to 48.
- **Target native canvas:** 16×16 attachment/pickup; 8×8 HUD glyph.
- **Art batch / game milestone:** B1 / M2.
- **Visual brief:** Cream-and-brass hand pump with red grip, thin dark hose and compact harpoon nozzle.
- **Required states/components:** pickup 1; held right/up/down; pump compression 2; nozzle socket. Hose and harpoon use fx_pump.

#### tool_air_cannon

- **Feature IDs:** 11; animation also contributes to 48.
- **Target native canvas:** 16×16 pickup; up to 32×16 attachment; 8×8 HUD.
- **Art batch / game milestone:** B2 / M3.
- **Visual brief:** Follow existing Air Cannon concept: red pressure tank, brass pressure gauge with cyan glass, cream body, wide gunmetal nozzle and short hose loop.
- **Required states/components:** pickup idle; held right/up/down; recoil 2; icon. Pressure bolt/trail/impact in fx_air.

#### tool_drill_missile

- **Feature IDs:** 12; animation also contributes to 48.
- **Target native canvas:** 16×16 pickup/shot; 32×16 held maximum.
- **Art batch / game milestone:** B4 / M5.
- **Visual brief:** Short orange-and-steel launcher with an unmistakable spiral drill tip; industrial mining tool.
- **Required states/components:** pickup; held views; launch 2; drill projectile spin 4; short exhaust; hard-rock impact. No full-screen beam.

#### tool_freeze_sprayer

- **Feature IDs:** 13; animation also contributes to 48.
- **Target native canvas:** 16×16 pickup; 32×16 held maximum.
- **Art batch / game milestone:** B4 / M5.
- **Visual brief:** Cyan insulated tank, cream handle and broad frost nozzle; snowflake-like silhouette mark.
- **Required states/components:** pickup; held views; spray onset/loop/end; frost puffs; individual ice block intact/cracked/thawing. Shares fx_status ice language.

#### tool_ricochet_disc

- **Feature IDs:** 14; animation also contributes to 48.
- **Target native canvas:** 16×16 pickup/shot; 32×16 held maximum.
- **Art batch / game milestone:** B4 / M5.
- **Visual brief:** Brass-rimmed teal spinning disc and compact circular launcher; disc remains readable edge-on.
- **Required states/components:** pickup; held views; launch 2; spin 4; bounce star 2; spent/disappear 2.

#### tool_sonic_lance

- **Feature IDs:** 15; animation also contributes to 48.
- **Target native canvas:** 16×16 pickup; 32×16 held maximum.
- **Art batch / game milestone:** B4 / M5.
- **Visual brief:** Purple-and-brass tuning-fork emitter with a cyan resonator; distinct fork silhouette.
- **Required states/components:** pickup; held views; pulse windup/release; repeatable sonic wave segments; materialization hit cue.

#### tool_foam_launcher

- **Feature IDs:** 16; animation also contributes to 48.
- **Target native canvas:** 16×16 pickup; 32×16 held maximum; 16×16 plug tiles.
- **Art batch / game milestone:** B4 / M5.
- **Visual brief:** Cream cartridge with mint foam emblem and a stubby square nozzle; bulbous foam plug.
- **Required states/components:** pickup; held views; lob/spray 2; plug grow/intact/cracking/break; occupied-tile placement denied cue from UI.

#### trap_dig_bomb

- **Feature IDs:** 17; animation also contributes to 48.
- **Target native canvas:** 16×16 object; 8×8 HUD.
- **Art batch / game milestone:** B2 / M3.
- **Visual brief:** Round red mining bomb with chunky brass cap and clearly visible burning fuse.
- **Required states/components:** pickup; planted idle; fuse slow/fast; final flash. Explosion and debris use fx_blast/fx_dig.

#### trap_remote_charge

- **Feature IDs:** 18; animation also contributes to 48.
- **Target native canvas:** 16×16 charge and detonator; 8×8 HUD.
- **Art batch / game milestone:** B3 / M4.
- **Visual brief:** Rectangular orange charge with a brass receiver and separate small plunger remote; no timed fuse silhouette.
- **Required states/components:** pickup; planted; armed indicator; detonate cue; icon distinguishes ready versus active charge.

#### trap_pressure_bomb

- **Feature IDs:** 19; animation also contributes to 48.
- **Target native canvas:** 16×16 object; modular 16×16 wave.
- **Art batch / game milestone:** B4 / M5.
- **Visual brief:** Blue compressed-air sphere with brass valve and a dial face; visibly pneumatic.
- **Required states/components:** pickup; armed expanding bands 3; release; tunnel wave straight/corner/T/cross/end pieces. Wave design must match actual propagation.

#### trap_decoy_turnip

- **Feature IDs:** 20; animation also contributes to 48.
- **Target native canvas:** 16×16 object; optional 32×32 concept canvas.
- **Art batch / game milestone:** B3 / M4.
- **Visual brief:** Squeaky ivory turnip with purple shoulder, green leaves and a tiny wind-up key.
- **Required states/components:** pickup; planted bounce 3; squeak ring 3; exhausted 1. No explosive fuse or blast.

#### trap_cryo_bomb

- **Feature IDs:** 21; animation also contributes to 48.
- **Target native canvas:** 16×16 object; 8×8 HUD.
- **Art batch / game milestone:** B4 / M5.
- **Visual brief:** Pale blue faceted grenade with brass top and a white ice crystal motif.
- **Required states/components:** pickup; armed pulse 3; cold burst onset/loop/end. Group-freeze effect uses status art, not movable frozen blocks.

#### module_turbo_hose

- **Feature IDs:** 22; animation also contributes to 48.
- **Target native canvas:** 16×16 pickup/attachment; 8×8 HUD.
- **Art batch / game milestone:** B1 / M2.
- **Visual brief:** Short red reinforced nozzle with a small twin-stripe speed mark.
- **Required states/components:** pickup; attachment views; rapid pump pulse; equipment card icon. Short range is represented by game geometry.

#### module_long_tom

- **Feature IDs:** 23; animation also contributes to 48.
- **Target native canvas:** 16×16 pickup; 32×16 held maximum; 8×8 HUD.
- **Art batch / game milestone:** B3 / M4.
- **Visual brief:** Long brass telescoping nozzle with cream collar and small range chevrons.
- **Required states/components:** pickup; attachment views; extend/retract 2; icon. Do not increase the player's collision box.

#### module_tri_pump

- **Feature IDs:** 24; animation also contributes to 48.
- **Target native canvas:** 16×16 pickup; 32×16 held maximum; 8×8 HUD.
- **Art batch / game milestone:** B4 / M5.
- **Visual brief:** Three short brass nozzle prongs in a fan with a red common manifold.
- **Required states/components:** pickup; attachment views; pump pulse; three branch tether components. Each branch is clipped by terrain.

### Pickups

#### pick_hard_hat

- **Feature IDs:** 35; animation also contributes to 48.
- **Target native canvas:** 16×16 pickup; player-sized overlay; 8×8 HUD.
- **Art batch / game milestone:** B3 / M4.
- **Visual brief:** Gold protective over-helmet with a bold pale ridge; fits over the established player helmet.
- **Required states/components:** pickup; equipped overlay per view; crack/break 3; protection sparkle; icon.

#### pick_tunnel_boots

- **Feature IDs:** 36; animation also contributes to 48.
- **Target native canvas:** 16×16 pickup; 8×8 HUD.
- **Art batch / game milestone:** B3 / M4.
- **Visual brief:** Pair of cobalt boots with gold soles and a simple speed stripe.
- **Required states/components:** pickup bob 2; worn accents if readable; short footprint trail; timer icon.

#### pick_soil_scanner

- **Feature IDs:** 37; animation also contributes to 48.
- **Target native canvas:** 16×16 pickup; 8×8 HUD.
- **Art batch / game milestone:** B3 / M4.
- **Visual brief:** Brass handheld detector with a green screen and small cyan antenna.
- **Required states/components:** pickup; scanning pulse 3; item-outline markers; hazard-outline markers; icon. Never conceal normal hazard warnings.

#### pick_bonus_balloon

- **Feature IDs:** 38; animation also contributes to 48.
- **Target native canvas:** 32×32 balloon plus 16×16 icon inset.
- **Art batch / game milestone:** B5 / M6.
- **Visual brief:** Bright red supply balloon with cream seams and a brass equipment capsule.
- **Required states/components:** float 4; first-hit activate; cycle frame; lock flash; reward release/pop. Composite real equipment icons into its window in code.

#### pick_rewards

- **Feature IDs:** base; animation also contributes to 48.
- **Target native canvas:** 16×16 each.
- **Art batch / game milestone:** B1 / M2.
- **Visual brief:** Clear arcade vegetables and fruit: carrot, turnip, radish, strawberry, cherry pair, pineapple; supply capsule and extra-life helmet.
- **Required states/components:** One clean master each; shared pickup glint/collect effect; fruit colors must not be confused with hazard warnings. Decoy remains distinguishable by wind-up key.

### Terrain

#### tile_topsoil

- **Feature IDs:** base; animation also contributes to 48.
- **Target native canvas:** 16×16 tiles.
- **Art batch / game milestone:** B0 / M1.
- **Visual brief:** Classic warm brown earth strata with sparse pebbles, dark tunnels, green grass surface and cream roots.
- **Required states/components:** All 16 occupancy masks per material style; 3 solid texture variants; edges/corners/junctions; fresh refill; surface cap; hard bedrock; boundary tiles.

#### tile_crystal_caverns

- **Feature IDs:** 25; animation also contributes to 48.
- **Target native canvas:** 16×16 tiles; modular larger crystals.
- **Art batch / game milestone:** B5 / M6.
- **Visual brief:** Deep navy stone with cyan and violet minerals; bright faceted reflectors stand apart from ordinary glitter.
- **Required states/components:** Base mask family; hard mineral vein; reflector slash/backslash/front orientations; glint 3; break/crack if permitted; safe surface/arena trim.

#### tile_frozen_depths

- **Feature IDs:** 26; animation also contributes to 48.
- **Target native canvas:** 16×16 tiles; 16×32 icicles.
- **Art batch / game milestone:** B5 / M6.
- **Visual brief:** Cobalt ice, pale cyan fossil inclusions and white cracked support ledges.
- **Required states/components:** Base mask family; intact/warning/broken support; icicle attached/falling/shatter; frozen-body ground cue. No sliding-floor arrows.

#### tile_fungal_hollows

- **Feature IDs:** 27; animation also contributes to 48.
- **Target native canvas:** 16×16 tiles; modular mushrooms.
- **Art batch / game milestone:** B5 / M6.
- **Visual brief:** Dark plum soil with teal roots and magenta mushroom caps; threats readable without darkening the whole playfield.
- **Required states/components:** Base masks; spore pocket sealed/warning/open; spore cloud pieces; root regrowth stages; harmless mushroom decoration clearly distinct from Rootmaw.

#### tile_sunken_temple

- **Feature IDs:** 28; animation also contributes to 48.
- **Target native canvas:** 16×16 tiles; modular pillars.
- **Art batch / game milestone:** B5 / M6.
- **Visual brief:** Ochre stonework, weathered turquoise trim, moss and shallow decorative blue water motifs.
- **Required states/components:** Base masks; indestructible blocks; pillars intact/cracked/failing/broken; ceiling pieces falling/impact; cosmetic water. No functioning flood simulation implied.

#### tile_lost_machinery

- **Feature IDs:** 29; animation also contributes to 48.
- **Target native canvas:** 16×16 tiles; modular valves and jets.
- **Art batch / game milestone:** B5 / M6.
- **Visual brief:** Rusted cream steel, dark pipes, brass valves and red/amber warning lamps.
- **Required states/components:** Base diggable fill masks; fixed hard metal; valve closed/open; jet warning/on/off in four directions; separate machinery trim. No unselected teleport system.

#### tile_molten_core

- **Feature IDs:** 30; animation also contributes to 48.
- **Target native canvas:** 16×16 tiles; modular reservoirs.
- **Art batch / game milestone:** B5 / M6.
- **Visual brief:** Charcoal earth, orange molten seams and enormous pale fossil fragments; hot reservoirs clearly marked.
- **Required states/components:** Base masks; sealed reservoir/warning/breach; lava filled/edge/end/corner and 3-frame flow; hardened boundary; heat accents. Finite pools, no global rising tide.

#### prop_rocks

- **Feature IDs:** base; animation also contributes to 48.
- **Target native canvas:** 16×16 or 32×32.
- **Art batch / game milestone:** B0 / M1.
- **Visual brief:** Chunky gray boulder with two hard highlights and a clear flat support footprint.
- **Required states/components:** supported; wobble 3; falling 2; impact 3; broken fragments; optional material variants derived from one silhouette.

### Effects

#### fx_pump

- **Feature IDs:** base,22,23,24; animation also contributes to 48.
- **Target native canvas:** 8×8 visual parts in 16×16 sprite cells.
- **Art batch / game milestone:** B1 / M2.
- **Visual brief:** Thin dark hose with pale highlight, brass harpoon head and small air pulse.
- **Required states/components:** Right/up/down tether segments, endpoint, attachment flash, pressure pulse and disconnect. Length built from components; no raster for every possible length.

#### fx_air

- **Feature IDs:** 11; animation also contributes to 48.
- **Target native canvas:** 16×16 bolt; modular trail.
- **Art batch / game milestone:** B2 / M3.
- **Visual brief:** Cyan-white compressed-air ring with a clear leading edge and a short pale trail.
- **Required states/components:** launch 2; travel 3; impact 3; end/dissipate 2. No opaque smoke hiding targets.

#### fx_dig

- **Feature IDs:** base,02,03,12,17; animation also contributes to 48.
- **Target native canvas:** 16×16 dust/chips.
- **Art batch / game milestone:** B0 / M1.
- **Visual brief:** Small warm earth chips and compact dust puffs using the current biome palette.
- **Required states/components:** dig puff 3; chips 3; refill settling 3; rock dust 3. No permanent background shadow baked into actor sprites.

#### fx_blast

- **Feature IDs:** 05,17,18,19,21; animation also contributes to 48.
- **Target native canvas:** 16×16 pieces; composed burst up to 48×48.
- **Art batch / game milestone:** B2 / M3.
- **Visual brief:** Compact mining blast with white-yellow center, orange rim and chunky debris; cold/pressure versions use different shapes as well as palettes.
- **Required states/components:** warning glint; ignition 2; expansion 3; dissipation 2; debris. Pressure routes and cryo clouds use their own component geometry.

#### fx_status

- **Feature IDs:** base,13,15,21,35; animation also contributes to 48.
- **Target native canvas:** 16×16 parts; 32×32/48×48 overlays.
- **Art batch / game milestone:** B2 / M3.
- **Visual brief:** Stun stars, hard-edged frost facets, materialization speckles, hit accents and shield fragments.
- **Required states/components:** stun orbit 3; freeze onset 3; ice intact/crack/thaw; ghost/solid transition; hit 2; shield break 3. Palette/index effects may replace overlays where safe.

#### fx_enemy_attacks

- **Feature IDs:** base,06,10,32; animation also contributes to 48.
- **Target native canvas:** 16×16 modular pieces.
- **Art batch / game milestone:** B1 / M2.
- **Visual brief:** Fygar flame with orange core, Volty spark with forked yellow arms, Rootmaw spore as a pale magenta seed.
- **Required states/components:** Each attack: tell/onset/travel or active/recovery/end; directional masks as needed; boss fire shares art language with a larger assembly.

#### fx_score

- **Feature IDs:** 39,40,41; animation also contributes to 48.
- **Target native canvas:** 8×8 glyphs; 16×16 badges.
- **Art batch / game milestone:** B2 / M3.
- **Visual brief:** Gold score numerals, small link emblem for chains, three-step inflate/arrow/rock technique emblem, clean-clear shield/check badge.
- **Required states/components:** Text composed from glyphs; pop/move/fade timing in code; collect spark. Counts and multiplier values are runtime data, not generated text.

#### fx_coop

- **Feature IDs:** 45; animation also contributes to 48.
- **Target native canvas:** 16×16 markers; actor-relative overlays.
- **Art batch / game milestone:** B7 / M8.
- **Visual brief:** P1 orange and P2 blue identification markers with distinct shapes, rescue pulse, capture warning brackets.
- **Required states/components:** capture onset/loop; struggle marker; rescue flash; timeout marker; join sparkle. Uses exact runtime timers and glyphs.

### Bonus props

#### bonus_garden

- **Feature IDs:** 42; animation also contributes to 48.
- **Target native canvas:** 16×16 pickups; 32×32/48×48 prize crops.
- **Art batch / game milestone:** B5 / M6.
- **Visual brief:** Oversized carrot, turnip and pumpkin crops with expressive leafy tops; whimsical farm-rescue props.
- **Required states/components:** Crop intact/carried/recovered/escape; carry attachment variants on existing enemies; garden fence/surface trim. No new enemy species required.

#### bonus_rockfall

- **Feature IDs:** 43; animation also contributes to 48.
- **Target native canvas:** 16×16 tiles and glyphs.
- **Art batch / game milestone:** B3 / M4.
- **Visual brief:** Simple rock-count tokens and marked puzzle chamber trim using existing boulders and soil.
- **Required states/components:** Limited-rock icon; target markers; success/failure banner frame. Reuse prop_rocks, enm_pooka and HUD font.

#### bonus_pressure_test

- **Feature IDs:** 44; animation also contributes to 48.
- **Target native canvas:** 32×32 balloon monsters; 48×48 inflated.
- **Art batch / game milestone:** B3 / M4.
- **Visual brief:** Comical balloon creatures with the Pooka visual vocabulary and distinctive practice-target markings.
- **Required states/components:** waiting 2; inflation stages; wobble 2; deflate; pop 3; timer frame. No dependency on Pressure Bomb.

### Interface

#### ui_font

- **Feature IDs:** base,39,40,41,42,43,44,45,46; animation also contributes to 48.
- **Target native canvas:** 8×8 FIX glyphs.
- **Art batch / game milestone:** B0 / M1.
- **Visual brief:** Compact early-1990s arcade bitmap lettering: squared sans, open counters, clear O/0 and I/1 distinction.
- **Required states/components:** Printable basic Latin as needed; digits; punctuation; arrows; multiplication sign if used; P1/P2; exact text typeset by code. Image generation supplies style only.

#### ui_hud

- **Feature IDs:** base,35,36,37,39,40,41; animation also contributes to 48.
- **Target native canvas:** 8×8 glyphs; 16×16 source icons.
- **Art batch / game milestone:** B1 / M2.
- **Visual brief:** Small high-contrast score/lives/ammo/module/timer indicators with cream text and restrained brass separators.
- **Required states/components:** Empty/full ammo; life; module/special slots; timer; no-ammo cue; chain and technique labels; clean-clear flag; boss state indicator.

#### ui_equipment_menu

- **Feature IDs:** 11,12,13,14,15,16,17,18,19,20,21,22,23,24; animation also contributes to 48.
- **Target native canvas:** 8×8/16×16 pieces; composed at 320×224.
- **Art batch / game milestone:** B2 / M3.
- **Visual brief:** Simple arcade equipment rack with selected-item frame, arrows and silhouettes of the actual tools.
- **Required states/components:** Selected/unselected/disabled/empty states; small confirm/cancel glyphs; reuse real equipment icons; deterministic names and stats.

#### ui_logo

- **Feature IDs:** base; animation also contributes to 48.
- **Target native canvas:** provisional 256×64 composed tiles.
- **Art batch / game milestone:** B6 / M7.
- **Visual brief:** Chunky SUPER DIG DUG wordmark, cream/gold depth, red SUPER accent and subtle mining-tool motif; clean readable arcade logo.
- **Required states/components:** Concept wordmark; corrected final lettering; small monochrome version if needed. Exact title is SUPER DIG DUG; no SNK/Namco logos or fake license seals.

#### ui_screen_frames

- **Feature IDs:** base,46; animation also contributes to 48.
- **Target native canvas:** 8×8/16×16 modular pieces; 320×224 assembly.
- **Art batch / game milestone:** B2 / M3.
- **Visual brief:** Minimal dark arcade panels with brass corners, tiny tool motifs and enough negative space for crisp text.
- **Required states/components:** Title/attract overlay, ready, game over, continue if implemented, stage clear, high-score initials, credits and Boss Rush menu. No invented menu modes.

#### ui_world_cards

- **Feature IDs:** 25,26,27,28,29,30; animation also contributes to 48.
- **Target native canvas:** provisional 128×64 vignette per biome.
- **Art batch / game milestone:** B5 / M6.
- **Visual brief:** Small scenic pixel vignettes showing each biome's recognizable material and primary hazard without UI text baked in.
- **Required states/components:** One card per six biome IDs plus topsoil if needed; tiny map icons; runtime titles. Pure presentation, not gameplay terrain substitutes.

#### ui_ending

- **Feature IDs:** base; animation also contributes to 48.
- **Target native canvas:** 320×224 composed scene; reusable sprites/tiles.
- **Art batch / game milestone:** B6 / M7.
- **Visual brief:** The digger returns to a restored vegetable garden with defeated monsters as harmless comic cameos; warm celebratory arcade tone.
- **Required states/components:** Simple victory tableau, player victory reuse, crops, sparkles, space for ending text. Co-op variant reuses P2; no large cutscene scope.

#### ui_audio_cue

- **Feature IDs:** 47; animation also contributes to 48.
- **Target native canvas:** none required; optional 8×8 debug glyph.
- **Art batch / game milestone:** B6 / M7.
- **Visual brief:** Reactive music is an audio system and does not require a new character, weapon or collectible.
- **Required states/components:** Optional debug music-state icon only; do not count a decorative note as completing reactive music.


## 10. Coverage of the 48 selected additions

| Feature | Primary asset families / treatment |
|---|---|
| 01. Mecha-Pooka | `enm_mecha_pooka` |
| 02. Borer Beetle | `enm_borer_beetle`, `fx_dig` |
| 03. Clod | `enm_clod`, `fx_dig` |
| 04. Goopy | `enm_goopy` |
| 05. Fusebug | `enm_fusebug`, `fx_blast` |
| 06. Volty | `enm_volty`, `fx_enemy_attacks` |
| 07. Gecko | `enm_gecko` |
| 08. Echo | `enm_echo` |
| 09. Mimic Pooka | `enm_mimic_pooka` |
| 10. Rootmaw | `enm_rootmaw`, `fx_enemy_attacks` |
| 11. Air Cannon | `tool_air_cannon`, `fx_air`, `ui_equipment_menu` |
| 12. Drill Missile | `tool_drill_missile`, `fx_dig`, `ui_equipment_menu` |
| 13. Freeze Sprayer | `tool_freeze_sprayer`, `fx_status`, `ui_equipment_menu` |
| 14. Ricochet Disc | `tool_ricochet_disc`, `ui_equipment_menu` |
| 15. Sonic Lance | `tool_sonic_lance`, `fx_status`, `ui_equipment_menu` |
| 16. Foam Launcher | `tool_foam_launcher`, `ui_equipment_menu` |
| 17. Dig Bomb | `trap_dig_bomb`, `fx_dig`, `fx_blast`, `ui_equipment_menu` |
| 18. Remote Charge | `trap_remote_charge`, `fx_blast`, `ui_equipment_menu` |
| 19. Pressure Bomb | `trap_pressure_bomb`, `fx_blast`, `ui_equipment_menu` |
| 20. Decoy Turnip | `trap_decoy_turnip`, `ui_equipment_menu` |
| 21. Cryo Bomb | `trap_cryo_bomb`, `fx_blast`, `fx_status`, `ui_equipment_menu` |
| 22. Turbo Hose | `module_turbo_hose`, `fx_pump`, `ui_equipment_menu` |
| 23. Long Tom Hose | `module_long_tom`, `fx_pump`, `ui_equipment_menu` |
| 24. Tri-Pump | `module_tri_pump`, `fx_pump`, `ui_equipment_menu` |
| 25. Crystal Caverns | `tile_crystal_caverns`, `ui_world_cards` |
| 26. Frozen Depths | `tile_frozen_depths`, `ui_world_cards` |
| 27. Fungal Hollows | `tile_fungal_hollows`, `ui_world_cards` |
| 28. Sunken Temple | `tile_sunken_temple`, `ui_world_cards` |
| 29. Lost Machinery | `tile_lost_machinery`, `ui_world_cards` |
| 30. Molten Core | `tile_molten_core`, `ui_world_cards` |
| 31. King Pooka | `boss_king_pooka` |
| 32. King Fygar | `boss_king_fygar`, `fx_enemy_attacks` |
| 33. Iron Mole | `boss_iron_mole` |
| 34. World Worm | `boss_world_worm` |
| 35. Hard Hat | `pick_hard_hat`, `fx_status`, `ui_hud` |
| 36. Tunnel Boots | `pick_tunnel_boots`, `ui_hud` |
| 37. Soil Scanner | `pick_soil_scanner`, `ui_hud` |
| 38. Bonus Balloon | `pick_bonus_balloon` |
| 39. Pop Chain | `fx_score`, `ui_font`, `ui_hud` |
| 40. Technique Bonus | `fx_score`, `ui_font`, `ui_hud` |
| 41. Clean Clear | `fx_score`, `ui_font`, `ui_hud` |
| 42. Garden Panic | `bonus_garden`, `ui_font` |
| 43. Rockfall Rally | `bonus_rockfall`, `ui_font` |
| 44. Pressure Test | `bonus_pressure_test`, `ui_font` |
| 45. Co-op Rescue | `chr_player_2`, `fx_coop`, `ui_font` |
| 46. Boss Rush | `ui_font`, `ui_screen_frames` |
| 47. Reactive Music | Audio implementation; optional `ui_audio_cue` for debugging only. No required generated image. |
| 48. Expanded Combat Animation | Applies to all animated character, boss, equipment, prop and effect families; no additional standalone character. |


## 11. Technical references

- [Aseprite CLI](https://www.aseprite.org/docs/cli/) — batch exports, tags, metadata and scripting entry points.
- [Aseprite scripting API](https://www.aseprite.org/api/) — inspect the installed version before authoring scripts.
- [ngdevkit](https://github.com/dciabrin/ngdevkit) and [examples](https://github.com/dciabrin/ngdevkit-examples) — use the pinned graphics pipeline and verified MAME loader.
- [Neo Geo sprite graphics format](https://wiki.neogeodev.org/index.php/Sprite_graphics_format) — planar tile encoding.
- [Neo Geo sprites](https://wiki.neogeodev.org/index.php/Sprites) — strip organization and rendering limits.
- [Neo Geo FIX layer](https://wiki.neogeodev.org/index.php/Fix_layer) — HUD tile and palette rules.
- [Neo Geo VRAM](https://wiki.neogeodev.org/index.php/VRAM) — tile references and hardware access.

This guide adds visual production detail to the gameplay handoff. It does not certify that the art or ROM pipeline has already been implemented.
