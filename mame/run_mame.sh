#!/usr/bin/env bash
# Isolated MAME Neo Geo MVS launcher for Super Dig Dug
# Never touches ~/.mame; keeps NVRAM, CFG, states, and snapshots inside ./mame/
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CART_NAME="${1:-superdigdug}"
EXTRA_FLAGS="${2:-}"
BIOS_DIR="${NEOGEO_BIOS_DIR:-${ROOT_DIR}/mame/roms}"

mkdir -p \
  "${ROOT_DIR}/mame/roms" \
  "${ROOT_DIR}/mame/cfg" \
  "${ROOT_DIR}/mame/nvram" \
  "${ROOT_DIR}/mame/sta" \
  "${ROOT_DIR}/mame/snap" \
  "${ROOT_DIR}/mame/diff"

MAME_BIN="$(command -v mame || echo /usr/games/mame)"

exec "${MAME_BIN}" neogeo "${CART_NAME}" \
  -hashpath "${ROOT_DIR}/mame/hash" \
  -rompath "${ROOT_DIR}/mame/roms;${BIOS_DIR}" \
  -cfg_directory "${ROOT_DIR}/mame/cfg" \
  -nvram_directory "${ROOT_DIR}/mame/nvram" \
  -state_directory "${ROOT_DIR}/mame/sta" \
  -snapshot_directory "${ROOT_DIR}/mame/snap" \
  -diff_directory "${ROOT_DIR}/mame/diff" \
  -window -nomaximize -nofilter ${EXTRA_FLAGS}
