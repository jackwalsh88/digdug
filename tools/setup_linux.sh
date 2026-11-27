#!/usr/bin/env bash
# Install the Super Dig Dug build and test toolchain on Ubuntu 24.04 (run as root).
#   - ngdevkit: m68k-neogeo-elf-gcc, Z80 assembler, and nullbios (an open-source
#     Neo Geo BIOS replacement) from the ngdevkit PPA
#   - MAME for headless verification (tools/mame_smoke.py) and `make run`
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y --no-install-recommends software-properties-common gnupg
add-apt-repository -y ppa:dciabrin/ngdevkit
apt-get update
apt-get install -y --no-install-recommends ngdevkit ngdevkit-toolchain mame python3-pil

# MAME installs to /usr/games, which is not always on PATH.
if [ ! -e /usr/local/bin/mame ] && [ -x /usr/games/mame ]; then
  ln -s /usr/games/mame /usr/local/bin/mame
fi

m68k-neogeo-elf-gcc --version | head -1
mame -version
