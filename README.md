# Engineering Intelligence Platform

A backend platform that connects **Jira issues**, **GitHub pull requests**, **feature graphs**, and **vector embeddings** to surface engineering insights: defect hotspots, reopen patterns, PR risk scores, duplicate detection, and AI-powered code review context.

## What It Does

| Capability | How |
|---|---|
| **Feature Graph** | Parses a React/TS codebase to build a feature hierarchy, stored in Neo4j |
| **Jira Integration** | Ingests epics/stories/defects from Jira REST API, maps them to features |
| **PR Intelligence** | Fetches PRs from GitHub, extracts Jira keys, infers mappings via embeddings |
| **Defect Analytics** | Computes hotspot features, reopen clusters, defect density, developer metrics |
| **RAG / Duplicate Detection** | Indexes issues + PRs in ChromaDB, enables similarity search and duplicate checks |
| **Agent Services** | Enriches code reviews with feature context, risk scores, and review guidance |
| **Async Workflows** | Orchestrates multi-step ingestion and analytics via Temporal |

## Architecture

```
                    ┌────────────────────────────┐
                    │    FastAPI  (8 routers)     │
                    │   33 endpoints, JWT auth    │
                    └──────┬─────────┬───────────┘
                           │         │
               ┌───────────┘         └───────────┐
               ▼                                  ▼
     ┌──────────────────┐              ┌──────────────────┐
     │  Service Layer   │              │  Temporal Worker  │
     │  7 services      │              │  6 workflows      │
     └───┬────┬────┬────┘              │  12 activities    │
         │    │    │                   └───┬────┬────┬────┘
         ▼    ▼    ▼                       │    │    │
     ┌──────┐ ┌──────┐ ┌──────────┐       │    │    │
     │Postgr│ │Neo4j │ │ ChromaDB │◄──────┘    │    │
     │ SQL  │ │Graph │ │ Vectors  │             │    │
     └──────┘ └──────┘ └──────────┘             │    │
                                           ┌────┘    └────┐
                                           ▼              ▼
                                      ┌────────┐    ┌────────┐
                                      │ Jira   │    │ GitHub │
                                      │  API   │    │  API   │
                                      └────────┘    └────────┘
```

## Tech Stack

| Component | Technology |
|---|---|
| API | FastAPI, Pydantic v2, uvicorn |
| Database | PostgreSQL 16, SQLAlchemy 2 (async), Alembic |
| Graph | Neo4j 5 |
| Vector DB | ChromaDB |
| Embeddings | OpenAI `text-embedding-3-small` |
| Workflows | Temporal |
| Auth | JWT (PyJWT) + bcrypt |
| HTTP clients | httpx (async) |

## Getting Started

### Prerequisites

- Docker and Docker Compose
- (Optional) Python 3.11+ for local development without Docker

### Quick Start with Docker

```bash
# 1. Clone and enter the repo
git clone <repo-url> && cd cml-python-playground

# 2. Create your environment file
cp .env.example .env
# Edit .env — at minimum set EI_SECRET_KEY to something random

# 3. Start everything
docker compose up -d

# 4. Run database migrations
docker compose run --rm migrate

# 5. Verify
curl http://localhost:8000/health
# {"status":"healthy","version":"0.1.0"}
```

Services will be available at:

| Service | URL |
|---|---|
| API | http://localhost:8000 |
| API docs (Swagger) | http://localhost:8000/docs |
| Neo4j Browser | http://localhost:7474 |
| Temporal UI | http://localhost:8080 |

### Local Development (without Docker)

```bash
# 1. Install dependencies
pip install -e ".[dev]"

# 2. Start infrastructure (Postgres, Neo4j, ChromaDB, Temporal) via Docker
docker compose up -d postgres neo4j chromadb temporal postgres-temporal

# 3. Run migrations
alembic upgrade head

# 4. Start the API server
uvicorn engineering_intelligence.main:app --reload

# 5. Start the Temporal worker (separate terminal)
python -m engineering_intelligence.workflows.worker
```

### Running Tests

```bash
pytest tests/unit/ -v
```

## API Reference

All endpoints are prefixed with `/api/v1`. Protected routes require a JWT `Authorization: Bearer <token>` header. Admin-only routes require `role=admin`.

### Auth (`/api/v1/auth`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/login` | Public | Authenticate, returns JWT |
| POST | `/auth/register` | Public | Create a new user account |
| GET | `/auth/me` | User | Get current user profile |

### Features (`/api/v1/features`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/features/tree` | User | Hierarchical feature tree |
| GET | `/features/{name}/metrics` | User | Defect count, health score, reopen rate |
| GET | `/features/{name}/defect-density` | User | Defect density calculation |
| POST | `/features/` | User | Create a new feature node |

### Jira (`/api/v1/jira`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/jira/search` | User | Search issues by query, type, status, epic |
| GET | `/jira/{jira_key}` | User | Get single issue details |
| GET | `/jira/{root_key}/subtree` | User | Issue hierarchy (graph or relational) |
| POST | `/jira/` | User | Create/upsert a Jira issue |

### Pull Requests (`/api/v1/pr`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/pr/search` | User | Search PRs by query, repo |
| GET | `/pr/{repo}/{pr_number}` | User | Get PR details |
| GET | `/pr/{repo}/{pr_number}/impact` | User | Risk score, related defects, affected features |
| POST | `/pr/` | User | Create/upsert a PR, auto-extracts Jira mappings |

### Analytics (`/api/v1/analytics`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/analytics/hotspots` | User | Top features by defect weight |
| GET | `/analytics/reopen-patterns` | User | Defects with reopen relationships |
| GET | `/analytics/developer/{email}` | User | Issues worked on, by type |
| GET | `/analytics/feature-health/{name}` | User | Risk score for a feature |

### RAG (`/api/v1/rag`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/rag/similarity` | User | Semantic similarity search across indexed docs |
| POST | `/rag/duplicate-check` | User | Find likely duplicate defects |
| GET | `/rag/stats` | User | Vector index document count |

### Agent (`/api/v1/agent`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/agent/context` | User | Enrich a code review with feature + issue context |
| POST | `/agent/risk` | User | Assess PR risk (defect likelihood, impact scope) |
| POST | `/agent/duplicate-check` | User | Check if a new defect is a duplicate |
| POST | `/agent/review-context` | User | Full review guidance (context + risk + duplicates) |

### Workflows (`/api/v1/workflow`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/workflow/trigger` | Admin | Start a Temporal workflow |
| GET | `/workflow/types` | Admin | List available workflow types |
| GET | `/workflow/status/{id}` | Admin | Check workflow run status |
| GET | `/workflow/recent` | Admin | Recent workflow runs |

**Available workflow types:** `jira_ingestion`, `jira_incremental`, `pr_ingestion`, `feature_graph_build`, `hotspot_computation`, `rag_rebuild`

## Configuration

All settings use the `EI_` environment variable prefix. See `.env.example` for the full list.

| Variable | Default | Description |
|---|---|---|
| `EI_SECRET_KEY` | `change-me-in-production` | JWT signing key |
| `EI_DATABASE_URL` | `postgresql+asyncpg://...` | Async Postgres connection string |
| `EI_NEO4J_URI` | `bolt://localhost:7687` | Neo4j Bolt URI |
| `EI_CHROMA_HOST` | `localhost` | ChromaDB hostname |
| `EI_JIRA_API_TOKEN` | *(empty)* | Jira Personal Access Token |
| `EI_GITHUB_TOKEN` | *(empty)* | GitHub PAT for PR fetching |
| `EI_OPENAI_API_KEY` | *(empty)* | OpenAI key for embeddings |
| `EI_TEMPORAL_HOST` | `localhost:7233` | Temporal server address |

## Project Structure

```
engineering_intelligence/
  auth/               # JWT tokens, password hashing, RBAC dependencies
  config/             # Pydantic Settings (env-driven)
  db/                 # SQLAlchemy models, session factory, base
  graph/              # Neo4j client + repository (knowledge graph)
  repositories/       # Data access layer (user, jira, pr, feature, workflow)
  routers/            # FastAPI routers (8 modules, 33 endpoints)
  schemas/            # Pydantic v2 request/response models
  services/           # Business logic (jira, pr, feature, rag, analytics, agent, github, parser)
  vector/             # ChromaDB client wrapper
  workflows/          # Temporal definitions, activities, worker, dispatch
  main.py             # FastAPI app factory + lifespan
alembic/              # Database migrations (async)
tests/unit/           # 66 unit tests
docker-compose.yml    # Full stack: app, worker, postgres, neo4j, chromadb, temporal
Dockerfile            # Multi-stage production build
```
