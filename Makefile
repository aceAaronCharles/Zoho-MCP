# Zoho MCP server - developer and operator tasks.
# Usage:  make help
SHELL := /bin/bash
VENV  ?= .venv
PY    := $(VENV)/bin/python
PIP   := $(VENV)/bin/pip

.DEFAULT_GOAL := help
.PHONY: help setup test lint fmt check run run-http docker-build docker-up \
        docker-down docker-logs prod-up prod-down prod-logs clean

help: ## Show this help
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) \
		| awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

setup: ## Create the virtualenv and install dev dependencies
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"

test: ## Run the test suite
	$(PY) -m pytest -q

lint: ## Static analysis (pyflakes)
	$(PY) -m pyflakes src tests

fmt: ## Format code and sort imports
	$(PY) -m black --line-length 120 src tests
	$(PY) -m isort --profile black --line-length 120 src tests

check: lint test ## Lint then test

run: ## Run the server over stdio (local, single user)
	$(PY) -m src.server

run-http: ## Run the HTTP transport on loopback
	MCP_TRANSPORT=http MCP_HOST=127.0.0.1 MCP_PORT=8000 $(PY) -m src.server

docker-build: ## Build the container image
	docker build -t zoho-mcp:local .

docker-up: ## Start the single-host stack
	docker compose up -d --build

docker-down: ## Stop the single-host stack
	docker compose down

docker-logs: ## Follow the single-host stack logs
	docker compose logs -f zoho-mcp

prod-up: ## Start the production stack (Caddy, automatic TLS)
	docker compose -f docker-compose.prod.yml up -d --build

prod-down: ## Stop the production stack
	docker compose -f docker-compose.prod.yml down

prod-logs: ## Follow the production stack logs
	docker compose -f docker-compose.prod.yml logs -f

clean: ## Remove caches and build artifacts
	rm -rf .pytest_cache .mypy_cache .ruff_cache build dist *.egg-info
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
