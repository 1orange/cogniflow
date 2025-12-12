.PHONY: help install test lint clean run generate-data generate-config

help:
	@echo "Modulus ML Pipeline - Available Commands"
	@echo "========================================="
	@echo "make install        - Install dependencies"
	@echo "make test           - Run all tests"
	@echo "make test-unit      - Run unit tests only"
	@echo "make test-integration - Run integration tests only"
	@echo "make test-e2e       - Run end-to-end tests only"
	@echo "make coverage       - Run tests with coverage report"
	@echo "make lint           - Run type checking with mypy"
	@echo "make clean          - Remove generated files"
	@echo "make generate-data  - Generate sample data"
	@echo "make generate-config - Generate default config"
	@echo "make run            - Run the pipeline with config.yaml"
	@echo "make quick-start    - Complete setup and run"

install:
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install -e .

test:
	pytest

test-unit:
	pytest tests/unit/

test-integration:
	pytest tests/integration/

test-e2e:
	pytest tests/e2e/

coverage:
	pytest --cov=modulus --cov-report=html --cov-report=term
	@echo "Coverage report generated in htmlcov/index.html"

lint:
	mypy modulus/

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf results/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

generate-data:
	python scripts/generate_sample_data.py

generate-config:
	python -m modulus.cli --generate-config

run:
	python -m modulus.cli --config config.yaml

quick-start:
	@bash scripts/quick_start.sh

