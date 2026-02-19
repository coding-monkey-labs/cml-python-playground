# Engineering Intelligence Platform — Pending TODOs

> Auto-generated 2026-02-19 — tracks remaining work after the core implementation is complete.

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
| **CI/CD pipeline** | **Pending** |
| **Integration tests** | **Pending** |

---

## ~~1. Docker & Docker Compose~~ (Done)

All completed — `Dockerfile`, `docker-compose.yml`, `.dockerignore`, `.env.example`.

---

## 2. CI/CD Pipeline (GitHub Actions)

### 2.1 `.github/workflows/ci.yml`
- [ ] **Lint** — ruff check + ruff format --check
- [ ] **Type check** — mypy (optional, but schemas are Pydantic)
- [ ] **Unit tests** — `pytest tests/unit/ -v`
- [ ] **Integration tests** — `pytest tests/integration/ -v` (with service containers)
- [ ] **Build** — verify Docker image builds successfully
- [ ] Matrix: Python 3.11 / 3.12
- [ ] Cache pip dependencies

### 2.2 `.github/workflows/deploy.yml` (optional)
- [ ] Build and push Docker image to registry
- [ ] Deploy to staging/production environment

---

## 3. Integration Tests

### 3.1 Database integration (`tests/integration/test_db.py`)
- [ ] Test full CRUD cycle for each repository against a real (test) Postgres
- [ ] Test Alembic migrations apply cleanly (upgrade + downgrade)
- [ ] Test concurrent writes / upsert idempotency

### 3.2 API integration (`tests/integration/test_api.py`)
- [ ] Test auth flow end-to-end (register → login → access protected routes)
- [ ] Test Jira issue create → search → subtree
- [ ] Test PR create with Jira key extraction → verify mappings created
- [ ] Test feature tree build → metrics → defect density
- [ ] Test analytics endpoints with seeded data
- [ ] Test RAG similarity search + duplicate detection with real embeddings (or mocked)
- [ ] Test workflow trigger → status polling

### 3.3 Service integration (`tests/integration/test_services.py`)
- [ ] Test JiraService.fetch_from_jira_api with mocked httpx (respx)
- [ ] Test GitHubService.fetch_prs with mocked httpx
- [ ] Test PRService.upsert_pr creates Jira mappings when issues exist
- [ ] Test RAGService.index_document → similarity_search round-trip
- [ ] Test FeatureParser against a sample React project fixture

### 3.4 Workflow integration (`tests/integration/test_workflows.py`)
- [ ] Test Temporal activities in isolation with test DB
- [ ] Test full workflow execution with Temporal test server (if available)

### 3.5 Test fixtures
- [ ] `conftest.py` with async test DB setup (test Postgres via testcontainers or SQLite)
- [ ] Factory fixtures for User, JiraIssue, PullRequest, Feature
- [ ] Sample React project fixture directory for parser tests

---

## Priority Order

1. **Docker + docker-compose** — enables local development and deployment
2. **Integration tests** — validates the wiring between layers actually works
3. **CI/CD** — automates quality gates on every push
