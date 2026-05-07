.PHONY: help install dev-install infra infra-down migrate run worker test lint format clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

# ── Setup ──────────────────────────────────────────────────────────────────────

install: ## Install production dependencies
	pip install -e .

dev-install: ## Install with dev dependencies (pytest, ruff, mypy)
	pip install -e ".[dev]"

# ── Infrastructure ─────────────────────────────────────────────────────────────

infra: ## Start infrastructure (Postgres, Neo4j, ChromaDB, Temporal) in Docker
	docker compose -f docker-compose.dev.yml up -d

infra-down: ## Stop infrastructure containers
	docker compose -f docker-compose.dev.yml down

infra-reset: ## Stop infrastructure and delete all data volumes
	docker compose -f docker-compose.dev.yml down -v

infra-logs: ## Tail infrastructure logs
	docker compose -f docker-compose.dev.yml logs -f

infra-status: ## Show infrastructure container status
	docker compose -f docker-compose.dev.yml ps

# ── Database ───────────────────────────────────────────────────────────────────

migrate: ## Run Alembic migrations (upgrade to head)
	alembic upgrade head

migrate-down: ## Rollback one migration
	alembic downgrade -1

migrate-history: ## Show migration history
	alembic history --verbose

# ── Application ────────────────────────────────────────────────────────────────

run: ## Start the FastAPI server with hot-reload
	uvicorn engineering_intelligence.main:app --reload --host 0.0.0.0 --port 8000

worker: ## Start the Temporal worker
	python -m engineering_intelligence.workflows.worker

# ── Testing & Quality ──────────────────────────────────────────────────────────

test: ## Run all unit tests
	python -m pytest tests/unit/ -v

test-cov: ## Run tests with coverage report
	python -m pytest tests/unit/ -v --cov=engineering_intelligence --cov-report=term-missing

lint: ## Run ruff linter
	python -m ruff check engineering_intelligence/ tests/

format: ## Auto-format code with ruff
	python -m ruff format engineering_intelligence/ tests/

typecheck: ## Run mypy type checker
	python -m mypy engineering_intelligence/

# ── Full Stack (Docker) ───────────────────────────────────────────────────────

up: ## Start everything in Docker (app + infra)
	docker compose up -d

down: ## Stop all Docker containers
	docker compose down

docker-migrate: ## Run migrations inside Docker
	docker compose run --rm migrate

docker-logs: ## Tail all Docker logs
	docker compose logs -f

# ── Cleanup ────────────────────────────────────────────────────────────────────

clean: ## Remove build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf dist/ build/ htmlcov/ .coverage
