VENV			= .venv
DEV_DIR			= .dev
EXCLUDE_LINT	= --exclude $(VENV),$(DEV_DIR)

SRC		= src
MAIN	= $(SRC)/__main__.py

install:
	uv sync

get-task-mbpp:
	cd .dev/moulinette && uv run moulinette_eval dump mbpp --output ../../datasets/mbpp/task.json

get-task-swebench:
	cd .dev/moulinette && uv run moulinette_eval dump swebench --output ../../datasets/swebench/task.json

run-mbpp: install
	uv run python -m $(SRC) agent_mbpp

run-swebench: install
	uv run python -m $(SRC) agent_swebench

run-model_lst:
	uv run python -m src.api.openai_api

lint: install
	uv run flake8 . $(EXCLUDE_LINT)
	uv run mypy . $(EXCLUDE_LINT)

lint-strict: install
	uv run flake8 . $(EXCLUDE_LINT)
	uv run mypy . --strict $(EXCLUDE_LINT)	

clean:
	uv clean
	rm -rf $(VENV)
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +

.PHONY: install run debug package lint lint-strict clean
