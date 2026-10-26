VENV	= .venv

SRC		= src
MAIN	= $(SRC)/main.py

MYPY_FLAGS = \
	--warn-return-any           \
	--warn-unused-ignores       \
	--ignore-missing-imports    \
	--disallow-untyped-defs     \
	--check-untyped-defs


install:
	uv sync

run: install
	uv run $(MAIN)

lint: install
	uv run flake8 . --exclude $(VENV)
	uv run mypy . $(MYPY_FLAGS)

lint-strict: install
	uv run flake8 . --exclude $(VENV)
	uv run mypy . --strict

clean:
	uv clean

.PHONY: install run debug package lint lint-strict clean