# Makefile for common development tasks

.PHONY: test test-all test-matrix install help

help:
	@echo "Available commands:"
	@echo "  make test        - Run tests with current Python version"
	@echo "  make test-all    - Run tests with all available Python versions (matching CI)"
	@echo "  make install     - Install dependencies"
	@echo "  make help        - Show this help message"

test:
	@pytest tests/ -v

test-all:
	@./test-matrix.sh

install:
	@pip install -r requirements.txt
