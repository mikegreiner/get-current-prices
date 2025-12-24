# Makefile for common development tasks

.PHONY: test test-all test-matrix install help

help:
	@echo "Available commands:"
	@echo "  make test        - Run tests with current Python version (recommended)"
	@echo "  make test-all    - Run tests with all available Python versions (optional)"
	@echo "  make install     - Install dependencies"
	@echo "  make help        - Show this help message"
	@echo ""
	@echo "Note: Testing on your primary Python version is usually sufficient."
	@echo "      GitHub Actions will test on all versions (3.8-3.12)."

test:
	@pytest tests/ -v

test-all:
	@./test-matrix.sh

install:
	@pip install -r requirements.txt
