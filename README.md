# RAG Orchestrator Platform

On-prem, multi-database, LlamaIndex-powered RAG-as-a-Service platform.

## Architecture

```
Layer 1: Admin UI (Jinja2 Dashboard)
Layer 2: FastAPI Control + Data API
Layer 3: RAG Orchestration Engine (LlamaIndex)
Layer 4: Vector Database Abstraction Layer (Adapter Pattern)
Layer 5: PostgreSQL Metadata Store
Layer 6: Background Ingestion Workers
```

## Phase 1 (Current)

- Single vector DB: **Qdrant**
- Full CRUD for RAG instances
- Document ingestion with chunking + embedding (HuggingFace / sentence-transformers)
- Semantic query with metadata filtering
- Cross-instance query fan-out
- JWT + API key authentication
- Background ingestion worker
- Admin dashboard UI
- Docker Compose deployment (API + PostgreSQL + Qdrant)

## Quick Start

```bash
# Start all services
docker compose up -d

# Access
# API:       http://localhost:8000/api/v1/docs
# Dashboard: http://localhost:8000/
# Qdrant:    http://localhost:6333/dashboard

# Get auth token
curl -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}'

# Create a RAG instance
curl -X POST http://localhost:8000/api/v1/rag/instance \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "docs-rag",
    "namespace": "documentation",
    "vector_db_type": "qdrant"
  }'

# Ingest documents
curl -X POST http://localhost:8000/api/v1/rag/ingest \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_instance_id": "<instance-id>",
    "documents": [
      {"content": "Your document text here", "metadata": {"source": "manual"}}
    ]
  }'

# Query
curl -X POST http://localhost:8000/api/v1/rag/query \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "rag_instance_id": "<instance-id>",
    "query": "search query",
    "top_k": 5
  }'
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/token` | Get JWT token |
| POST | `/api/v1/auth/api-key` | Create API key (admin) |
| POST | `/api/v1/rag/instance` | Create RAG instance |
| GET | `/api/v1/rag/instance` | List RAG instances |
| GET | `/api/v1/rag/instance/{id}` | Get RAG instance |
| PATCH | `/api/v1/rag/instance/{id}` | Update RAG instance |
| DELETE | `/api/v1/rag/instance/{id}` | Delete RAG instance |
| POST | `/api/v1/rag/ingest` | Ingest documents |
| POST | `/api/v1/rag/reindex` | Trigger reindex |
| POST | `/api/v1/rag/delete-by-filter` | Delete by metadata |
| GET | `/api/v1/rag/ingestion-status` | Job status |
| POST | `/api/v1/rag/query` | Semantic query |
| POST | `/api/v1/rag/hybrid-query` | Hybrid query |
| POST | `/api/v1/rag/cross-instance-query` | Cross-instance query |
| GET | `/api/v1/rag/metrics` | Platform metrics |
| GET | `/api/v1/rag/vector-db-health` | Vector DB health |

## Project Structure

```
rag_platform/
  api/
    routes/          # FastAPI route handlers
    middleware/       # Auth middleware
    app.py           # Application factory
  core/
    config.py        # Settings (pydantic-settings)
    exceptions.py    # Platform exceptions
    logging.py       # Structured logging
  db/
    models/          # SQLAlchemy ORM models
    migrations/      # Alembic migrations
    session.py       # Async DB session
  vectordb/
    adapters/        # Vector DB adapters (Qdrant, ...)
    base.py          # Abstract adapter interface
    factory.py       # Adapter factory
  orchestrator/
    engine.py        # LlamaIndex RAG engine
  schemas/           # Pydantic request/response schemas
  services/          # Business logic layer
  workers/           # Background workers
  ui/
    templates/       # Jinja2 HTML templates
    static/          # CSS/JS assets
```

## Roadmap

- **Phase 2**: Multi-DB (Weaviate, Chroma, pgvector), adapter abstraction, namespace support
- **Phase 3**: Cross-instance federation, versioning, migration support
- **Phase 4**: Agent integration, hybrid search, benchmarking dashboard
- **Phase 5**: Index federation, intelligent routing
