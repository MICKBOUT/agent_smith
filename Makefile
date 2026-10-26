install:
	uv sync

run: install
	uv run src/main.py