# Super Dig Dug — Unified Project Makefile
# Delegates portable orchestration to tools/sdd.py so developers with GNU Make
# can run `make <target>` while minimal containers without `make` can run
# `python3 tools/sdd.py <target>` with identical behavior.

PYTHON ?= python3
SDD    := $(PYTHON) tools/sdd.py

ROM    ?= digdug.zip
PACK   ?=
SCENARIO ?= play

.PHONY: help status disasm smoke bios assets asset-check asset-preview art-viewer rom test run debug budgets package clean

help:
	@$(SDD) --help

status:
	@$(SDD) status

disasm:
	@$(SDD) disasm --rom "$(ROM)"

assets:
	@$(SDD) assets $(if $(PACK),--pack "$(PACK)",)

asset-check:
	@$(SDD) asset-check

asset-preview:
	@$(SDD) asset-preview

art-viewer:
	@$(SDD) art-viewer

rom:
	@$(SDD) rom

test:
	@$(SDD) test

run:
	@$(SDD) run

debug:
	@$(SDD) debug

budgets:
	@$(SDD) budgets

package:
	@$(SDD) package

# Headless MAME scenario (boot, play, viewer): snapshots + memory peeks in build/smoke/
smoke:
	@$(PYTHON) tools/mame_smoke.py $(SCENARIO) $(if $(WAV),--wav,)

# Stage ngdevkit's open-source nullbios as mame/roms/neogeo.zip (no commercial BIOS needed)
bios:
	@mkdir -p mame/roms && cp /usr/share/ngdevkit/neogeo.zip mame/roms/neogeo.zip && echo "[bios] nullbios staged in mame/roms/neogeo.zip"

clean:
	@$(SDD) clean
