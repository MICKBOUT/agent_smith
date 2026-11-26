VENV			= .venv
DEV_DIR			= .dev
MOULINETTE_DIR	= moulinette
FLAKE8_EXCLUDE	= --exclude $(VENV),$(DEV_DIR),$(MOULINETTE_DIR)
MYPY_EXCLUDE	= --exclude '(^|/)(\.venv|\.dev|moulinette)(/|$$)'

SRC		= src
MAIN	= $(SRC)/__main__.py
CACHE	= (cache)

install:
	uv sync

get-task-mbpp:
	cd moulinette && env -u VIRTUAL_ENV uv run moulinette_eval dump mbpp --output ../cache/mbpp_task.json

get-task-swebench:
	cd moulinette && env -u VIRTUAL_ENV uv run moulinette_eval dump swebench --output ../cache/swebench_task.json

run-mbpp:
	uv run python -m $(SRC) agent_mbpp

run-swebench:
	uv run python -m $(SRC) agent_swebench \
		--output output.json \
		--task_file datasets/swebench/task.json

run-model_lst:
	uv run python -m src.api.openai_api

lint:
	uv run flake8 . $(FLAKE8_EXCLUDE)
	uv run mypy . $(MYPY_EXCLUDE)

lint-strict: install
	uv run flake8 . $(FLAKE8_EXCLUDE)
	uv run mypy . --strict $(MYPY_EXCLUDE)

clean:
	uv clean
	rm -rf $(VENV) $(CACHE)
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +

.PHONY: install run debug package lint lint-strict clean
