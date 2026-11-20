# MAME & Toolchain Setup (`MAME-SETUP.md`)

## Verification Status

**Current Status:** **NOT YET VERIFIED IN MAME** (`M0` pending).

Per Handoff §4 and §13:
- This cloud sandbox currently lacks `mame`, `ngdevkit` (`m68k-neogeo-elf-gcc`), `gcc`, and `make`, and outbound network egress to package mirrors/GitHub is disabled by sandbox policy.
- Consequently, **no untested `mame superdigdug` command is claimed here as working**. Once a local workstation runs the M0 bring-up steps below, pin exact versions, SHA-1/CRC32 hashes, and the tested command line in this document.

---

## 1. Required Host Toolchain (Linux / WSL2 Baseline)

1. **`ngdevkit` + `ngdevkit-examples`**
   - Provides `m68k-neogeo-elf-gcc`, binutils, Z80/SDCC audio toolchain, `libngdevkit`, linker scripts, and reference cartridge builders.
   - Record pinned git commit hashes for both `ngdevkit` and `ngdevkit-examples` in `DECISIONS.md` and `TEST-REPORT.md` upon installation.
2. **MAME** (0.250+ recommended; pin exact `mame -version` output)
   - Must include the `neogeo` (`Neo-Geo MV-1F` / `mv1fs` / `aes` or `ngdevkit`-matched MVS slot driver) driver and `neogeo.xml` software list definitions.
3. **Python 3.10+**
   - Used by `tools/sdd.py` and `tools/assets/` for deterministic PNG authoring, terrain mask generation, C-ROM/S-ROM bitplane encoding, round-trip verification, and host simulation tests.
4. **Optional: Aseprite CLI (`aseprite --batch`)**
   - When absent, the pipeline uses native indexed PNG sheets + JSON frame/socket manifests directly.

---

## 2. System BIOS Prerequisites

MAME requires a valid Neo Geo system ROM set (`neogeo.zip`) in its `rompath`:
- **Never commit `neogeo.zip` or commercial game ROMs into git** (`.gitignore` blocks `neogeo.zip` and `mame/roms/`).
- `ngdevkit` can build or pair with an open/development BIOS (`uni-bios` or `ngdevkit` nullbios) if supported by the pinned MAME machine definition; verify all required system files (`000-lo.lo`, `sfix.sfix`, `sm1.sm1`, and the selected `sp-s2.sp1` or `ngdevkit` BIOS) via:
  ```sh
  mame neogeo -verifyroms -rompath /path/to/bios_dir
  ```
- Record the chosen BIOS filename and CRC32/SHA-1 in local setup notes when certifying `M0`. Note that passing under a development BIOS does not prove compatibility with every retail MVS BIOS revision.

---

## 3. Cartridge Registration & Isolated Loading Policy (Handoff §4)

A `.zip` filename alone does **not** register a new arcade game in MAME. Use one of these two clean routes in order of preference:

### Route A — Software-List / Custom Hash XML or `ngdevkit` Cartridge Route (Preferred)
1. Inspect the pinned MAME build's Neo Geo cartridge slot and software list support:
   ```sh
   mame neogeo -listslots
   mame neogeo -listmedia
   ```
2. Build an unmodified `ngdevkit-examples` sample first to confirm the exact P-ROM (16-bit word-swapped/even-odd), S-ROM (`8×8` FIX), C-ROM (`C1`/`C2` odd/even bitplane halves), M-ROM (Z80), and V-ROM (ADPCM) layout expected by `ngdevkit`'s loader path.

### Route B — Isolated Donor Registration or Minimal MAME Registration Patch
- If `ngdevkit`'s default workflow substitutes a donor software-list shortname (e.g., `puzzledp`) during early bring-up:
  - Stage the generated ZIP **exclusively** inside `./mame/roms/` alongside a symlink or copy of `neogeo.zip`.
  - **Never overwrite a user's shared MAME ROM directory** and never distribute builds under a commercial game's identity.
- For clean standalone identity (`superdigdug`), keep a minimal MAME driver/hash patch under `mame/` separate from game source.

---

## 4. Isolated Runtime Directories & Planned Launch Flags

All project launcher scripts (`mame/run_mame.sh`, invoked by `make run` / `make debug`) must isolate emulator state from `~/.mame`:

```sh
mame neogeo \
  -rompath "./mame/roms;${NEOGEO_BIOS_DIR}" \
  -cfg_directory ./mame/cfg \
  -nvram_directory ./mame/nvram \
  -state_directory ./mame/sta \
  -snapshot_directory ./mame/snap \
  -diff_directory ./mame/diff \
  -window -nomaximize -nofilter -ues
```

*(Note: Replace `neogeo` + cart argument with the exact verified machine + slot/software-list invocation once proven in Gate M0, and keep `-nofilter` / no CRT shaders enabled for pixel and strip diagnosis.)*

---

## 5. Gate M0 Verification Checklist

Before marking `M0` complete in `TEST-REPORT.md`:
- [ ] Record exact `mame -version`, `m68k-neogeo-elf-gcc --version`, and `ngdevkit` commit SHA.
- [ ] Boot unmodified `ngdevkit` example cleanly.
- [ ] Boot `Super Dig Dug` M0 diagnostics ROM (cold boot + hard reset).
- [ ] Confirm FIX title text, 1 moving `16×16`/`32×32` sprite, palette swatch, VBlank counter, watchdog stability (5-minute run without reset), P1/P2 + Coin/Start inputs, and Z80 sound command round-trip.
