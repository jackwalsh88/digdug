# Verification & Test Report (`TEST-REPORT.md`)

## 1. Environment Audit (Recorded at Repository Bootstrap)

Probed via `python3 tools/sdd.py status` inside the Ubuntu 24.04 (`x86_64`) workspace container:

| Tool / Dependency | Status | Observed Version / Notes |
|---|---|---|
| `python3` | **Present** | Python `3.12.x` (`numpy`, `pandas`, `pyyaml` pre-installed) |
| `git` | **Present** | `git version 2.43.0` |
| `node` / `npm` | **Present** | Node `v22.x` / npm `10.x` |
| `make` | **Missing** | Not installed; `python3 tools/sdd.py <cmd>` provides identical CLI dispatch |
| `gcc` / `g++` | **Missing** | No host C compiler installed in this container |
| `m68k-neogeo-elf-gcc` (`ngdevkit`) | **Missing** | Target 68000 cross-compiler not installed in this container |
| `z80-neogeo-ihx-sdcc` / `sdcc` | **Missing** | Target Z80 sound compiler not installed in this container |
| `mame` | **Missing** | Target Neo Geo MVS emulator not installed in this container |
| `aseprite` | **Missing** | Using documented indexed PNG + JSON metadata fallback (DECISIONS `D-06`) |
| Network Egress | **Restricted** | Package mirrors (`apt`, `PyPI`) and GitHub are blocked (`HTTP 403`) in this sandbox |

---

## 2. Current Build & Runtime Verification Status

- **ROM Build (`M0`):** Not yet built (`0` ROM artifacts).
- **MAME Execution (`M0`):** Not yet executed in MAME (`0` emulated frames). No performance, RAM high-water, or scanline strip hardware measurements are claimed.
- **Asset Pipeline (`B0`):** Baseline palette `metal_red_cyan_v1.json` added; pixel masters, packers, and validators pending next task.
- **Host Automated Tests:** Test harness scaffolded (`tests/`); unit tests pending next task.

---

## 3. Planned Verification Matrix

1. **Host Asset & Bitplane Tests (Runnable in this sandbox via `python3 tools/sdd.py asset-check`):**
   - Known-answer Neo Geo 16-bit palette word quantization & round-trip checks.
   - Known-answer `16×16` C-ROM (`C1`/`C2` planar halves, all 4 quadrants & 4 bitplanes) and `8×8` S-ROM (`S1`) encode/decode verification against hardware bit-order specifications.
   - Binary transparency (`index 0`), ≤16 colors/tile, palette role consistency, pivot/hitbox/socket bounds, 16-mask terrain quadrant accuracy, and worst-case `< 80` scanline strip budget checks.
2. **Host Gameplay Simulation Tests (Runnable in this sandbox via `python3 tools/sdd.py test`):**
   - `36×22` logical cell digging, corner turn buffering, rock partial-support/undercut/chain drops, `(slot, generation)` tether handles, bounded BFS Pressure Bomb loop safety, single-commit same-frame death/score precedence, and deterministic input-replay checksums.
3. **Target Build & MAME Integration Checks (Requires local workstation per `MAME-SETUP.md`):**
   - Clean `ngdevkit` 68000/Z80 compile, linker RAM/ROM map audit (`≤ 40 KiB` static game data, `~8 KiB` stack canary), cold boot/reset, P1/P2/Coin/Start inputs, Z80 sound handshake, `art-viewer` inspection, and 5-minute (`M0`) / 30-minute (`M7+`) MAME soak runs.
