VENV			= .venv
DEV_DIR			= .dev
EXCLUDE_LINT	= --exclude $(VENV),$(DEV_DIR)

SRC		= src
MAIN	= $(SRC)/__main__.py

install:
	uv sync

run: install
	uv run python -m $(SRC)

run-openai:
	uv run python -m src.api.openai_api

lint: install
	uv run flake8 . $(EXCLUDE_LINT)
	uv run mypy . $(EXCLUDE_LINT)

lint-strict: install
	uv run flake8 . $(EXCLUDE_LINT)
	uv run mypy . --strict $(EXCLUDE_LINT)

clean:
	uv clean

.PHONY: install run debug package lint lint-strict clean
