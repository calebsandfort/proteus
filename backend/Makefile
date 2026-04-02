.PHONY: test test-verbose test-cov install dev

# Run tests with pytest
test:
	uv run pytest

# Run tests with verbose output
test-verbose:
	uv run pytest -v

# Run tests with coverage report
test-cov:
	uv run pytest --cov=src --cov-report=term-missing --cov-report=html

# Install all dependencies including dev
install:
	uv sync --group dev

# Run development server
dev:
	uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# Run a specific test file
test-file:
	uv run pytest tests/$(FILE) -v

# Run tests matching a pattern
test-match:
	uv run pytest -v -k "$(PATTERN)"
