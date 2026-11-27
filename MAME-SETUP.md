# MAME and Toolchain Setup (`MAME-SETUP.md`)

## Verification status

**Verified on 2026-11-27** in an Ubuntu 24.04 (x86_64) container:

| Component | Version |
|---|---|
| MAME | 0.264 (Ubuntu package `mame`) |
| 68000 compiler | `m68k-neogeo-elf-gcc` 15.3.0 (`ngdevkit-toolchain` 0.1+202611221216) |
| ngdevkit | 0.5+202611251130 (PPA `ppa:dciabrin/ngdevkit`) |
| BIOS | ngdevkit **nullbios 0.5** (`/usr/share/ngdevkit/neogeo.zip`), an open-source BIOS replacement |
| Machine / loading route | `neogeo` driver, cartridge loaded through a project software list (`-hashpath mame/hash`) |

The game ROM boots, plays, and produces sound under this configuration. It has
**not** been run under a commercial MVS BIOS (`sp-s2.sp1` and others); nullbios
implements the same USER / PLAYER_START / SYSTEM_IO contract, but passing under
it does not prove compatibility with every retail BIOS revision.

## 1. Install the toolchain (Ubuntu 24.04)

```sh
sudo tools/setup_linux.sh
```

This adds the ngdevkit PPA and installs `ngdevkit`, `ngdevkit-toolchain`, `mame`
and Pillow. macOS: ngdevkit publishes a Homebrew tap (`dciabrin/ngdevkit`); it
has not been verified for this project.

## 2. Build

```sh
make assets PACK=/path/to/Super-Dig-Dug-Art   # or the asset-pack zip; omit PACK for stand-in art
make rom                                      # mame/roms/superdigdug.zip + mame/hash/neogeo.xml
make art-viewer                               # optional: mame/roms/sddview.zip
```

`make rom` assembles the Z80 driver (`src/audio/z80_driver.s`), compiles the
68000 program, packs P/S/M/V/C chips and writes a software-list entry with
their hashes. A directory named `Super-Dig-Dug-Art/` in the repository root is
picked up automatically by `make assets`.

## 3. BIOS

MAME needs a `neogeo.zip` in its ROM path. Two options:

- **Open BIOS (used for all verification here):** `make bios` copies ngdevkit's
  nullbios to `mame/roms/neogeo.zip`. MAME reports wrong checksums for
  `sp-s2.sp1`, `sm1.sm1` and `sfix.sfix`; that is expected and it still runs.
- **Your own MVS BIOS set:** `NEOGEO_BIOS_DIR=/dir/containing/neogeo.zip make run`.

`neogeo.zip` and `mame/roms/` are git-ignored. No BIOS is committed or bundled.

## 4. Run

Interactive:

```sh
make run            # mame/run_mame.sh superdigdug
```

which executes

```sh
mame neogeo superdigdug \
  -hashpath mame/hash -rompath "mame/roms;$NEOGEO_BIOS_DIR" \
  -cfg_directory mame/cfg -nvram_directory mame/nvram -state_directory mame/sta \
  -snapshot_directory mame/snap -diff_directory mame/diff \
  -window -nomaximize -nofilter
```

All emulator state stays under `mame/`; `~/.mame` is not touched.

Default MAME keys: `5` coin, `1` / `2` start, arrows move, `Left Ctrl` pump (A),
`3` ("Next Game", the MVS P1 SELECT input) opens and closes the art viewer on
the title and attract screens.

Headless (no display needed), with scripted inputs, PNG snapshots and memory
peeks written to `build/smoke/<scenario>/`:

```sh
make smoke SCENARIO=boot     # title + attract
make smoke SCENARIO=play     # coin, start, dig, pump
make smoke SCENARIO=viewer   # art viewer
make smoke SCENARIO=soak     # five emulated minutes of play
make smoke SCENARIO=play WAV=1   # also record build/smoke/play/audio.wav
```

## 5. ROM layout proven in MAME

| Chip | File | Size | Notes |
|---|---|---|---|
| P1 | `0482-p1.p1` | 512 KiB | big-endian program, stored word-swapped (`load16_word_swap`) |
| S1 | `0482-s1.s1` | 128 KiB | FIX tiles |
| M1 | `0482-m1.m1` | 128 KiB | Z80 driver + cue table at `$0400` |
| V1 | `0482-v1.v1` | 1 MiB | ADPCM-A samples (`ymsnd:adpcma`) |
| C1/C2 | `0482-c1.c1`, `0482-c2.c2` | 1 MiB each | sprite bitplanes 0-1 / 2-3 (`load16_byte`) |

NGH number `0x0482` is a development ID.

## 6. Gate M0 checklist

- [x] Exact `mame -version`, compiler version and ngdevkit version recorded (above).
- [ ] Boot an unmodified ngdevkit example. Not done; the project cart itself was used to prove the route.
- [x] Cold boot to title; BIOS coin restart (USER request 3) returns to title.
- [x] FIX text, sprites, palettes, VBlank counter (art viewer).
- [x] Five emulated minutes without a crash or watchdog reset (`soak`).
- [x] Coin and P1 start through the BIOS (credits in backup RAM, PLAYER_START).
- [ ] P2 inputs and 2P start: code path present, not exercised in MAME yet.
- [x] Z80 sound command round trip: MAME's audio output matches the source WAV.
- [ ] Hard reset (F3) and service/test switch behaviour.
