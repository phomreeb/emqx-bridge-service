.PHONY: help install run test typecheck lint format clean

help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies using uv"
	@echo "  make run        - Run the application"
	@echo "  make test       - Run unit tests with pytest and coverage"
	@echo "  make typecheck  - Run static type checking with mypy"
	@echo "  make lint       - Run linter (ruff check)"
	@echo "  make format     - Run formatter (ruff format)"
	@echo "  make clean      - Remove cached files"

install:
	uv sync

run:
	PYTHONPATH=src uv run python main.py

test:
	uv run pytest

typecheck:
	uv run mypy src tests main.py

lint:
	uv run ruff check src main.py tests

format:
	uv run ruff check --fix src main.py tests
	uv run ruff format src main.py tests

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -f coverage.xml .coverage
