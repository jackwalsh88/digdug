# Super Dig Dug — Unified Project Makefile
# Delegates portable orchestration to tools/sdd.py so developers with GNU Make
# can run `make <target>` while minimal containers without `make` can run
# `python3 tools/sdd.py <target>` with identical behavior.

PYTHON ?= python3
SDD    := $(PYTHON) tools/sdd.py

ROM    ?= digdug.zip

.PHONY: help status disasm assets asset-check asset-preview art-viewer rom test run debug budgets package clean

help:
	@$(SDD) --help

status:
	@$(SDD) status

disasm:
	@$(SDD) disasm --rom "$(ROM)"

assets:
	@$(SDD) assets

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

clean:
	@$(SDD) clean
