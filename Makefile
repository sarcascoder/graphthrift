.PHONY: help install dev demo demo-aggressive test lint serve up down build clean web-install web-dev

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-16s\033[0m %s\n", $$1, $$2}'

install: ## Install the package with dev extras (uses .venv if present)
	pip install -e ".[dev]"

demo: ## Run the offline safe-vs-baseline demo
	graphthrift demo --scenario safe

demo-aggressive: ## Run the aggressive demo (gate should FAIL)
	graphthrift demo --scenario aggressive

test: ## Run the test suite
	pytest -q

lint: ## Lint with ruff
	ruff check .

serve: ## Start the API locally (:8000)
	graphthrift serve --reload

up: ## Start the full stack (API + dashboard + Postgres) via Docker
	docker compose up --build

down: ## Stop the stack
	docker compose down

build: ## Build Docker images
	docker compose build

web-install: ## Install dashboard deps
	cd apps/web && npm install

web-dev: ## Run the dashboard dev server (:5173)
	cd apps/web && npm run dev

clean: ## Remove local state and caches
	rm -rf graphthrift_data *.sqlite3 .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
