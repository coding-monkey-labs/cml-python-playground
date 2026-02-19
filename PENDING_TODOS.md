# Engineering Intelligence Platform — Pending TODOs

> Updated 2026-02-19

## Status Overview

| Layer | Status |
|-------|--------|
| Data models & schemas | Done |
| Repositories (CRUD) | Done |
| Services (Jira, PR, Feature, RAG, Analytics, Agent, Auth) | Done |
| GitHub service (REST API client) | Done |
| Feature parser (React/TS regex scanner) | Done |
| API routers (8 routers, all endpoints) | Done |
| Temporal workflows (6 definitions, 12 activities) | Done |
| Temporal worker | Done |
| Workflow dispatch (Temporal client) | Done |
| Alembic migrations (async env + initial schema) | Done |
| Neo4j graph repository | Done |
| ChromaDB vector store | Done |
| Unit tests (66 passing) | Done |
| Docker / docker-compose | Done |
| README & docs | Done |
| CI/CD pipeline | Deferred |
| Integration tests | Deferred |

---

## Deferred: CI/CD Pipeline (GitHub Actions)

Not needed yet. When ready, add:

- `.github/workflows/ci.yml` — lint (ruff), type check (mypy), unit tests, Docker build verification
- `.github/workflows/deploy.yml` — image push + deploy to staging/prod

---

## Deferred: Integration Tests

Not needed yet. When ready, add:

- `tests/integration/test_db.py` — CRUD cycles against real Postgres, Alembic up/down
- `tests/integration/test_api.py` — end-to-end auth flow, Jira/PR/feature CRUD via HTTP
- `tests/integration/test_services.py` — mocked external APIs (httpx/respx), RAG round-trips
- `tests/integration/test_workflows.py` — Temporal activities against test DB
- `tests/integration/conftest.py` — async test DB setup, factory fixtures
