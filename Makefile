VENV			= .venv
EXCLUDE_VENV	= --exclude $(VENV)

SRC		= src
MAIN	= $(SRC)/main.py

install:
	uv sync

run: install
	uv run $(MAIN)

run-openrouter:
	uv run $(SRC)/openrouter_api.py

run-openai:
	uv run $(SRC)/openai_api.py

lint: install
	uv run flake8 . $(EXCLUDE_VENV)
	uv run mypy . $(EXCLUDE_VENV)

lint-strict: install
	uv run flake8 . $(EXCLUDE_VENV)
	uv run mypy . --strict $(EXCLUDE_VENV)

clean:
	uv clean

.PHONY: install run debug package lint lint-strict clean
