# Getting Started — Engineering Intelligence Platform

Step-by-step guide to get the platform running locally with Docker Compose or bare Python.

---

## 1. Prerequisites

| Requirement | Minimum Version | Check |
|---|---|---|
| Docker | 24+ | `docker --version` |
| Docker Compose | v2+ | `docker compose version` |
| Python *(local dev only)* | 3.11+ | `python --version` |
| Git | any | `git --version` |

---

## 2. Clone & Configure

```bash
git clone <repo-url>
cd cml-python-playground
cp .env.example .env
```

Open `.env` and configure these sections:

### 2.1 Required Configuration (must set before first run)

| Variable | What to set | Why |
|---|---|---|
| `EI_SECRET_KEY` | A random 32+ character string | JWT token signing. **Do not use the default in production.** Generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"` |

### 2.2 Optional — External Service Tokens

These are only needed if you want to ingest data from external sources. The platform runs fine without them — you can create data manually via the API.

| Variable | How to get it | What it unlocks |
|---|---|---|
| `EI_JIRA_API_TOKEN` | Jira → Profile → Personal Access Tokens → Create | Jira ingestion workflows (fetch epics/stories/defects) |
| `EI_JIRA_BASE_URL` | Your Jira instance URL, e.g. `https://yourcompany.atlassian.net` | Required alongside the token |
| `EI_JIRA_USER_EMAIL` | Your Jira account email | Required for Jira API auth |
| `EI_GITHUB_TOKEN` | GitHub → Settings → Developer Settings → Personal Access Tokens → Fine-grained | PR ingestion workflows (fetch PRs, files, metadata) |
| `EI_GITHUB_ORG` | Your GitHub org name | Default org for PR fetching |
| `EI_GITHUB_REPO` | Your GitHub repo name | Default repo for PR fetching |
| `EI_OPENAI_API_KEY` | OpenAI → API keys → Create new | Vector embeddings for RAG similarity search and duplicate detection. Without this, embeddings return zero vectors (search still works but returns no results). |

### 2.3 Infrastructure Defaults (usually leave as-is)

These match the docker-compose.yml defaults. Only change if you're running infrastructure externally.

| Variable | Default | Notes |
|---|---|---|
| `EI_DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/eng_intel` | Docker overrides this to use the `postgres` service hostname |
| `EI_NEO4J_URI` | `bolt://localhost:7687` | Docker overrides to `bolt://neo4j:7687` |
| `EI_NEO4J_USER` | `neo4j` | |
| `EI_NEO4J_PASSWORD` | `neo4jpassword` | Must match `NEO4J_AUTH` in docker-compose |
| `EI_CHROMA_HOST` | `localhost` | Docker overrides to `chromadb` |
| `EI_CHROMA_PORT` | `8000` | ChromaDB internal port |
| `EI_TEMPORAL_HOST` | `localhost:7233` | Docker overrides to `temporal:7233` |
| `EI_TEMPORAL_NAMESPACE` | `default` | |
| `EI_TEMPORAL_TASK_QUEUE` | `eng-intel-queue` | |

---

## 3. Start with Docker Compose (Recommended)

### 3.1 Start all services

```bash
docker compose up -d
```

This starts **8 containers**:

| Container | Description | Port |
|---|---|---|
| `app` | FastAPI API server | `localhost:8000` |
| `worker` | Temporal workflow worker | (no port, connects to Temporal) |
| `postgres` | Application database | `localhost:5432` |
| `neo4j` | Knowledge graph | `localhost:7474` (browser), `localhost:7687` (bolt) |
| `chromadb` | Vector embeddings | `localhost:8001` |
| `temporal` | Workflow orchestration server | `localhost:7233` |
| `postgres-temporal` | Temporal's own database | (internal only) |
| `temporal-ui` | Temporal dashboard | `localhost:8080` |

### 3.2 Run database migrations

```bash
docker compose run --rm migrate
```

This creates all 8 tables: `users`, `features`, `jira_issues`, `pull_requests`, `feature_jira_mapping`, `jira_pr_mapping`, `defect_metrics`, `workflow_runs`.

### 3.3 Verify

```bash
# Health check
curl http://localhost:8000/health
# → {"status":"healthy","version":"0.1.0"}

# Swagger docs
open http://localhost:8000/docs
```

### 3.4 Stop everything

```bash
docker compose down          # Stop containers, keep data
docker compose down -v       # Stop containers AND delete all data volumes
```

---

## 4. Local Development (Python + Docker for infra)

Use this if you want hot-reload and debugger support.

### 4.1 Start infrastructure only

```bash
docker compose up -d postgres neo4j chromadb temporal postgres-temporal temporal-ui
```

### 4.2 Install Python dependencies

```bash
python -m venv .venv
source .venv/bin/activate    # Linux/Mac
pip install -e ".[dev]"
```

### 4.3 Run migrations

```bash
alembic upgrade head
```

### 4.4 Start the API server

```bash
uvicorn engineering_intelligence.main:app --reload --host 0.0.0.0 --port 8000
```

### 4.5 Start the Temporal worker (separate terminal)

```bash
source .venv/bin/activate
python -m engineering_intelligence.workflows.worker
```

### 4.6 Run tests

```bash
pytest tests/unit/ -v
```

---

## 5. First Steps After Setup

### 5.1 Register a user

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "securepassword123",
    "full_name": "Admin User",
    "role": "admin"
  }'
```

### 5.2 Log in to get a JWT token

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "securepassword123"
  }'
# → {"access_token": "eyJhbG...", "token_type": "bearer"}
```

Save the token:

```bash
export TOKEN="eyJhbG..."
```

### 5.3 Create a feature

```bash
curl -X POST http://localhost:8000/api/v1/features/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Authentication", "description": "User auth flows"}'
```

### 5.4 Create a Jira issue

```bash
curl -X POST http://localhost:8000/api/v1/jira/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jira_key": "AUTH-101",
    "issue_type": "defect",
    "summary": "Login fails with SSO enabled",
    "status": "open",
    "severity": "high",
    "epic_key": "AUTH-1"
  }'
```

### 5.5 Create a PR (auto-extracts Jira keys)

```bash
curl -X POST http://localhost:8000/api/v1/pr/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pr_number": 42,
    "repo": "myorg/myrepo",
    "title": "Fix AUTH-101: SSO login redirect",
    "description": "Fixes the SSO redirect loop",
    "status": "open",
    "author_login": "developer1",
    "files_changed": 3,
    "additions": 50,
    "deletions": 10
  }'
```

The platform automatically extracts `AUTH-101` from the title and creates a PR-Jira mapping.

### 5.6 Trigger a workflow (admin only)

```bash
# Ingest Jira issues for an epic
curl -X POST http://localhost:8000/api/v1/workflow/trigger \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_type": "jira_ingestion",
    "params": {"epic_keys": ["AUTH-1", "DASH-1"]}
  }'

# Ingest PRs from GitHub
curl -X POST http://localhost:8000/api/v1/workflow/trigger \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_type": "pr_ingestion",
    "params": {"repo": "myorg/myrepo"}
  }'

# Build feature graph from codebase
curl -X POST http://localhost:8000/api/v1/workflow/trigger \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_type": "feature_graph_build",
    "params": {"codebase_path": "/path/to/react/app"}
  }'

# Compute defect hotspots
curl -X POST http://localhost:8000/api/v1/workflow/trigger \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"workflow_type": "hotspot_computation"}'

# Rebuild RAG vector index
curl -X POST http://localhost:8000/api/v1/workflow/trigger \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"workflow_type": "rag_rebuild"}'
```

### 5.7 Query analytics

```bash
# Defect hotspots
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/analytics/hotspots

# Feature health
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/analytics/feature-health/Authentication

# PR impact
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/pr/myorg%2Fmyrepo/42/impact

# Duplicate detection
curl -X POST http://localhost:8000/api/v1/rag/duplicate-check \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"summary": "Login broken with SSO", "threshold": 0.7}'
```

---

## 6. Service URLs & Dashboards

| Service | URL | Credentials |
|---|---|---|
| API Swagger Docs | http://localhost:8000/docs | JWT token |
| API ReDoc | http://localhost:8000/redoc | JWT token |
| Neo4j Browser | http://localhost:7474 | `neo4j` / `neo4jpassword` |
| Temporal UI | http://localhost:8080 | None |
| PostgreSQL | `localhost:5432` | `postgres` / `postgres` / `eng_intel` |
| ChromaDB | `localhost:8001` | None |

---

## 7. Troubleshooting

### Container won't start

```bash
docker compose logs app        # Check API logs
docker compose logs worker     # Check Temporal worker logs
docker compose logs postgres   # Check database logs
```

### Migration fails

```bash
# Check Postgres is ready
docker compose exec postgres pg_isready -U postgres

# Re-run migration
docker compose run --rm migrate
```

### Neo4j connection refused

Neo4j takes 30-60 seconds to start. The app handles this gracefully — graph features will be unavailable until Neo4j is ready, but all other endpoints work.

```bash
# Check Neo4j status
docker compose logs neo4j
```

### Temporal workflow not running

```bash
# Check worker is connected
docker compose logs worker

# Check Temporal server
docker compose logs temporal

# View workflows in UI
open http://localhost:8080
```

### Reset everything

```bash
docker compose down -v    # Deletes all data volumes
docker compose up -d      # Fresh start
docker compose run --rm migrate
```
