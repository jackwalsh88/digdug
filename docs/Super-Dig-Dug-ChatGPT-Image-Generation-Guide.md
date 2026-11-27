# Super Dig Dug — ChatGPT Image-Generation Guide

Version 1.0 • November 17, 2026  
For: **ChatGPT with an available image-generation tool**  
Companion: **Super-Dig-Dug-Coding-Agent-Sprite-Production.md**  
Game: **Super Dig Dug**, a new Neo Geo MVS arcade game running inside MAME

## Start here: your job

Use this guide to generate a coherent collection of sprite-design references, pose references, equipment concepts, terrain material references, effects and interface artwork.

Use your actual image generator for requested visuals. Do not respond with prompts alone when the user asks you to generate an image. Do not replace requested artwork with an unrelated code mockup.

Generated images are **visual source material for the coding agent**. They are not automatically valid 16×16 tiles, indexed-color sprites, precisely aligned animation frames or ready-to-load Neo Geo ROM data. Describe them accurately.

The coding agent will reconstruct clean native pixels, stabilize palettes and anchors, assemble exact terrain masks and text, and convert the results into game graphics. Your priorities are design clarity, consistency, readable silhouettes and the right gameplay cues.

This is a new MVS implementation. Preserve the selected features and do not introduce new monster types, weapons, levels or mechanics while drawing them.

## 1. References and continuity

Two existing concepts establish a starting direction:
- **Armored Mecha-Pooka pixel sprite.png** — riveted gunmetal helmet, brass goggles, cyan lenses, red inflatable belly and orange feet.
- **Pixel Air Cannon Pickup.png** — red pressure tank, brass gauge, cream casing, steel flared nozzle and short hose loop.

These concepts are candidates, not a claim of final art approval. User feedback overrides them.

If the actual files are available, inspect them and use them as visual references. A filename or a previous-chat mention is not the image itself. If exact matching requires an unavailable image, ask the user to attach it; otherwise use the written design and explicitly label it a fresh interpretation.

Keep each asset's accepted master as its identity anchor. When producing another pose, edit or reference that image rather than relying only on the asset's name. Reuse the current accepted revision, not an older rejected design.

When tool capabilities permit:
- Request real transparency for isolated characters, tools, props and effects.
- Supply the smallest relevant set of actual reference images.
- Keep pose edits tied to the correct target image.
- Do not invent file paths, reference identifiers, seeds or model settings.
- Follow the available tool's actual input options. Do not promise native 32×32 output if the tool does not support that size.

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


## 2. Generation procedure for one asset family

1. **Read its catalog entry.** Note the feature, native canvas, silhouette, required states and related assets.
2. **Choose the deliverable.** Usually start with one neutral master. For terrain, start with a material reference. For a boss, start with a coherent design and then its component masters.
3. **Select references.** Use the style anchor and the asset's own accepted master when present. Distinguish identity references from palette/style references.
4. **Write a precise prompt.** Combine the appropriate template below with the catalog's subject brief. Mention actual intended game scale, but request an enlarged visual reference.
5. **Generate.** One distinct asset or pose per call is the default. Avoid giant collages of unrelated weapons and enemies.
6. **Inspect the result.** Check identity, silhouette, view, complete framing, unwanted props/text, edge clarity and consistency.
7. **Revise a specific problem.** Keep the successful parts fixed. If the goggles changed during an inflation edit, correct the goggles rather than redesigning the whole enemy.
8. **Record the result.** Asset ID, version, pose, actual output reference, target native size and notes for the coding agent.
9. **Continue the requested scope.** Do not ask for permission between every ordinary asset. Work in small coherent batches and keep a progress ledger. A request for all assets is not fulfilled by one master image or a list of prompts.

Do not silently mark an image “approved.” Distinguish generated, internally reviewed and user-approved. If the user has not chosen among alternatives, retain the best candidate with that status.

### Good master poses

Characters: idle with clear limbs, facing right, no action effects obscuring the body.  
Equipment: side/profile or very slight three-quarter view, facing right, clear grip and emission point.  
Pickups: centered readable icon with no surrounding display card.  
Bosses: full uncropped silhouette, obvious weak points and simple component seams.  
Tiles: front-facing flat material design, no camera perspective or fake floor plane.

## 3. Prompt templates

Replace bracketed fields with real values from the catalog. Remove irrelevant fields rather than sending contradictory instructions.

### A. Character, equipment or pickup master

> Create exactly one isolated enlarged pixel-art design reference for Super Dig Dug, an early-1990s Neo Geo MVS arcade sequel. Asset: [ASSET ID / NAME]. Subject: [CATALOG BRIEF]. Intended production canvas: [NATIVE SIZE], with a simple silhouette legible at that tiny scale; this output is an enlarged reference. View: [RIGHT-FACING SCREEN-PLANE VIEW]. Pose: [NEUTRAL POSE]. Use deliberate square pixel clusters, crisp stepped contours, a limited palette with approximately 15 visible colors, hard two- or three-tone shading and upper-left highlights. Match [ACTUAL PROVIDED REFERENCE] in shape language and material treatment. Keep the entire asset visible with generous empty margins. Actual transparent background. No printed checkerboard, scenery, ground plane, cast shadow, text, labels, border, watermark, 3D render, soft glow, smooth gradient or painterly noise. One asset only.

For a held weapon, add: “It is a small player attachment; simplify to a clear nozzle/body/grip. Do not draw a large realistic gun.” For a pickup, add: “No hand or character holding it.”

### B. Pose/state edit with identity preservation

> Edit the supplied [ASSET ID] master into the [STATE / FRAME NAME] pose. Preserve the same character identity, palette roles, goggles/eyes, helmet, material details, facing direction, outline style and apparent scale. Change only [SPECIFIC POSE CHANGE]. Maintain the same conceptual ground/contact anchor. [INFLATION EXAMPLE: widen the exposed red belly, raise the existing helmet slightly, spread the feet; keep the same goggles.] Keep the whole object uncropped on a truly transparent background. No new props, background, text or style changes. Treat this as an animation key-pose reference; do not add multiple views.

The generator may still move pixels or proportions. Compare against the master and report any drift. Never claim that asking for a fixed anchor guarantees exact alignment.

### C. Boss and modular component

> Create a pixel-art design reference for [BOSS ID / NAME] in the same Super Dig Dug visual language. [BOSS BRIEF]. Design it to be assembled from [COMPONENTS], with obvious seams and [VULNERABLE PART]. Intended assembled footprint: [SIZE]. Show [WHOLE DESIGN OR ONE NAMED COMPONENT], facing [DIRECTION], in [STATE]. Use chunky arcade pixel clusters, restrained colors and exaggerated readable forms. Transparent background, full uncropped subject, no labels or UI.

First establish the whole boss design. Then reference it when generating the head, chassis, bellows, cheek sacs or worm segments. Do not independently redesign each component. The coding agent determines exact joints and tile boundaries.

### D. Terrain material and surface detail

> Create a flat, front-facing pixel-art material reference for Super Dig Dug: [BIOME ID / NAME]. Material: [BIOME BRIEF]. Intended construction uses 16×16 tiles; keep detail chunky, sparse and readable at that scale. Show one square opaque material swatch with compatible opposing edges, no border, no perspective, no objects, no lighting gradient across the whole swatch and no text. Use [BIOME PALETTE]. This is a texture reference for a tile generator, not a complete level screenshot.

Follow with isolated props or hazard states using template A. For an edge reference, specify the intended solid/empty boundary and use transparency in the empty region.

Do not promise a seamless tile just because the prompt requests matching edges. The coding agent checks the pixels. Do not ask the image model to create all 16 mathematically correct occupancy masks; those are constructed deterministically from the approved material.

### E. Effect keyframe

> Create one isolated enlarged pixel-art keyframe for [FX ID], at the [ONSET / PEAK / DISSIPATION] stage. Effect: [BRIEF]. Intended native footprint: [SIZE]. Direction: [DIRECTION]. Shape must communicate [GAMEPLAY MEANING] without hiding the target. Use sparse deliberate opaque pixel clusters, hard edges and a small palette; transparent gaps between particles. Transparent background, no dark rectangle, no soft bloom, no scenery, text or character.

Make onset, peak and end from the same design. For a modular pressure wave, generate the visual vocabulary; the coding agent builds exact straight/corner/junction connectivity.

### F. Interface icon or panel piece

> Create one enlarged arcade pixel-art [ICON / PANEL CORNER / CURSOR] for [UI ID]. It represents [FUNCTION] in Super Dig Dug. Intended final footprint [8×8 OR 16×16 OR MODULAR SIZE]. Use a bold simple silhouette, dark outline, cream highlights and restrained brass/cyan/red accents consistent with the game. Transparent background. No words, numbers, display card or extra icons.

For exact fonts, scores, prices, ammo counts and timers, provide a style reference only. The coding agent draws/exports deterministic bitmap glyphs and typesets real values.

### G. Logo

> Create a crisp early-1990s arcade pixel-art title-logo concept with the exact words “SUPER DIG DUG”. “SUPER” is the smaller red accent above the main chunky cream-and-gold “DIG DUG” lettering. A subtle mining-tool motif is allowed if it does not reduce legibility. Intended final composition is approximately 256×64 pixels, shown enlarged. Transparent background. No additional words, signatures, publisher logos, license seals, fake copyright notices or surrounding game screen.

Check spelling visually. If lettering is wrong, correct it or hand the shape reference to the coding agent for exact typography. Do not silently accept a nearly correct title.

### H. World vignette or ending scene

> Create a compact pixel-art [WORLD CARD / ENDING TABLEAU] for Super Dig Dug. Scene: [CATALOG BRIEF]. Intended composition: [128×64 OR 320×224], shown enlarged. Use the established character proportions, limited arcade palettes, simple depth separation and readable silhouettes. Reserve [AREA] for runtime text but draw no text. [OPAQUE BACKGROUND OR SPECIFIC TRANSPARENT OVERLAY]. No modern UI, cinematic blur, realistic lighting or invented gameplay mechanics.

A scenic card is presentation artwork. It cannot substitute for terrain tiles, collision-aligned props or a playable level.

## 4. Worked first prompts

### Mecha-Pooka master

Use the existing Mecha-Pooka image as the identity reference when available:

> Create one compact Mecha-Pooka pixel-sprite master reference for Super Dig Dug. Round red inflatable body, two large brass-rimmed cyan goggles, dark gunmetal riveted half-shell helmet with one small blunt spike, two orange feet and a visible exposed belly. Neutral right-facing three-quarter pose. Simplify the design for a 32×32 production canvas; enlarge it with crisp square pixel clusters for review. Preserve the character from the supplied reference but remove detail that would disappear at native scale. Dark outline, upper-left hard highlights, roughly 15 visible colors. Entire figure visible on a transparent background. No text, background, glow, shadow, weapon or additional poses.

Then produce:
- walk contact A and B;
- inflation stages, based on the engine's chosen count;
- extra armored inflation pose;
- helmet lift/crack;
- hurt/stun and defeat references.

Do not produce 48×48 as a larger “camera zoom” of the same normal pose. It represents actual body expansion in-game.

### Air Cannon pickup and held form

> Create one isolated Air Cannon pickup concept for Super Dig Dug. Use the supplied Air Cannon design: crimson pressure tank, brass gauge with cyan face, cream housing, short black hose and wide steel nozzle pointing right. Simplify it to read as a 16×16 pickup, shown enlarged. Keep the tank, gauge and nozzle as three clear masses, with no tiny decorative clutter. Hard pixel shading, dark contour, transparent background; no hand, text, projectile or scenery.

Generate the held form separately, referencing the same design:
- compact attachment with a defined grip/nozzle;
- recoil key pose;
- cyan pressure-ring bolt;
- impact/dissipation effect.

The large concept gun is not the final in-hand scale.

### Topsoil

> Create one opaque square pixel-art topsoil material swatch for Super Dig Dug: warm brown packed earth, sparse ochre pebbles and a few darker clusters. Detail must read in 16×16 tiles, with no large central object. Flat front-facing cross-section material, compatible opposite edges, no vignette, gradient, border, text, roots crossing arbitrarily beyond the frame or camera perspective.

The coding agent will derive the exact dug-out quadrants, shared edges and refill states from this reference.

## 5. Animation and sprite-sheet policy

Prefer an accepted master followed by referenced key-pose edits. For most families, the coding agent can build in-between frames more consistently than generating each full frame independently.

If the user specifically wants a sprite-sheet mockup:
- Restrict it to one asset family and one small animation.
- Specify pose order, equal visual scale, common facing and generous separation.
- Use at most a few frames per sheet so individual poses remain inspectable.
- Keep labels outside the art or omit them.
- Call it a reference sheet; do not claim exact cells, spacing, native resolution or palette compliance until measured and repaired.

The coding agent handles final frame extraction, native-grid reconstruction, fixed pivots and animation tags. A pleasant contact sheet is not evidence that it will animate without jitter.

## 6. Coverage, batching and progress

The catalog contains **65 asset families**, not 65 final images. A character with several poses, two statuses and a projectile requires multiple deliverables. UI text and exact terrain-mask variants are deterministic outputs from the coding agent, not dozens of separate AI generations.

When asked to generate:
- “one enemy”: select the named or next sensible enemy, make its master and deliver it.
- “the first batch”: cover the listed family masters and the essential requested states for that batch.
- “all game assets”: work through B0–B7, tracking family masters, required pose references and components; continue the authorized scope as tools allow. If a tool/runtime limit stops progress, give the precise completed and pending list without claiming completion.
- “continue”: resume from the ledger instead of regenerating completed assets.

Suggested ledger:

| Asset ID | Output/pose | Version | Status | Identity reference | Actual file/image reference | Remaining work |
|---|---|---|---|---|---|---|

For outputs use the environment's supported display and saving behavior. Keep delivered images associated with their asset IDs. Do not fabricate download links or rename an output only in prose. Avoid rebuilding files solely to display an image already delivered by the tool.

At the end of a batch, provide a compact summary of what was generated and what still requires native-pixel work. Never label all animation complete because the master exists.

## 7. Image acceptance checklist

Inspect each output:
1. Correct asset and required state?
2. Recognizable silhouette at the intended tiny scale?
3. Matches the current identity and style references?
4. Correct facing direction and complete framing?
5. No unrequested weapon, character or mechanic?
6. Clear role/weak point/warning?
7. No checkerboard printed into the art, background rectangle or unwanted shadow?
8. No excessive gradients, painterly noise or micro-detail?
9. No text except where explicitly requested, and exact spelling for the logo?
10. Does the coding agent have enough information to create clean source pixels?

If actual alpha or exact colors cannot be inspected, say they are unverified. Do not claim technical validation by visual impression alone.

## 8. Complete shared asset catalog

Each **Visual brief** can be inserted into the appropriate prompt template. The **Required states/components** field determines additional pose references or reusable parts. Native sizes are targets for the coding agent; the generator output may be much larger.


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


## 9. Coverage of the selected 48 additions

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


## 10. Completion and handoff

For each asset family, pass the coding agent:
- asset ID and feature IDs;
- chosen master and actual image/file reference;
- pose or component name for every additional image;
- intended native canvas and orientation;
- palette/style reference;
- deliberate deviations and unresolved visual problems;
- which states are still absent;
- user approval status, if explicitly given.

Completion means the requested visual references have been delivered and accurately inventoried. Production-ready art, exact fonts, seamless terrain, collision masks, palette packing and MAME testing belong to the coding-agent pipeline.

The user's existing gameplay handoff takes precedence over raw proposals. Do not introduce discarded enemies such as the penguin/octopus combinations, unlimited screen-clearing weapons, full flooding or new progression systems.

