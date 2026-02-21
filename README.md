# AI Video Cleaner Platform

A modular, AI-powered video processing platform that automatically detects and removes filler words, weak segments, dead air, and background noise from videos. Upload your raw recordings and get back polished, clean content.

## Project Report

### What It Does

1. **Upload** one or multiple videos via drag-and-drop
2. **Transcribe** audio using faster-whisper (word-level timestamps)
3. **Analyze** transcript with rule-based scoring + Ollama LLM review
4. **Score** every segment on clarity, engagement, filler density, retention risk
5. **Generate** an edit plan (which segments to cut, compress, or flag)
6. **Review** — approve or reject individual edits before rendering
7. **Render** cleaned video with noise reduction and audio normalization
8. **Download** the cleaned result or compare side-by-side with original

### Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   React UI   │────▶│    Nginx     │────▶│   FastAPI    │
│  (Desktop)   │     │  (Proxy:80)  │     │  (API:8000)  │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                  │
                     ┌──────────────┐     ┌───────▼──────┐
                     │   Ollama     │◀────│  Services    │
                     │ (LLM:11434) │     │              │
                     └──────────────┘     │ - Ingestion  │
                                          │ - Intel      │
                     ┌──────────────┐     │ - Editing    │
                     │  PostgreSQL  │◀────│              │
                     │  (DB:5432)   │     └───────┬──────┘
                     └──────────────┘             │
                     ┌──────────────┐             │
                     │     n8n      │◀────────────┘
                     │ (Orch:5678)  │  (webhook trigger)
                     └──────────────┘
```

### Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Backend | FastAPI + SQLAlchemy (async) | REST API, pipeline orchestration |
| Frontend | React 18 + Bootstrap 5 | Desktop-first UI |
| Database | PostgreSQL 16 | Jobs, transcripts, edit plans |
| Transcription | faster-whisper | Speech-to-text with timestamps |
| LLM Analysis | Ollama (Llama 3 / Mistral) | Segment review, edit suggestions |
| Video Editing | FFmpeg | Cutting, noise removal, normalization |
| Orchestration | n8n | Pipeline workflow automation |
| Proxy | Nginx | Reverse proxy, file uploads |
| Deployment | Docker Compose | Single-command deployment |

### Project Stats

- **59 source files** across backend and frontend
- **~4,500 lines** of application code
- **38 Python** modules (API, models, services, tests)
- **12 React** components and pages
- **6 Docker** services orchestrated via Compose
- **100% open-source** stack — no paid API dependencies

### Directory Structure

```
ai-video-cleaner/
├── docker-compose.yml              # Full stack deployment
├── .env.example                    # All configuration variables
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/
│   │   └── versions/
│   │       └── 001_initial_schema.py
│   ├── app/
│   │   ├── main.py                 # FastAPI app, lifespan, auto-pull
│   │   ├── config.py               # Pydantic settings
│   │   ├── database.py             # Async SQLAlchemy
│   │   ├── models/
│   │   │   ├── video_job.py        # Job status tracking
│   │   │   ├── transcript_chunk.py # Timestamped transcript segments
│   │   │   ├── edit_plan.py        # Edit actions with approval
│   │   │   └── pipeline_config.py  # Extensible pipeline definitions
│   │   ├── schemas/                # Pydantic request/response models
│   │   ├── api/
│   │   │   ├── videos.py           # Upload (single + batch)
│   │   │   ├── jobs.py             # List, status, transcript, edit approval
│   │   │   └── pipelines.py        # Ingest, analyze, edit, retry
│   │   ├── services/
│   │   │   ├── ingestion/
│   │   │   │   ├── audio_extractor.py   # FFmpeg audio extraction
│   │   │   │   └── transcriber.py       # faster-whisper transcription
│   │   │   ├── intelligence/
│   │   │   │   ├── filler_detector.py   # Rule-based filler detection
│   │   │   │   ├── segment_scorer.py    # Multi-dimension scoring
│   │   │   │   ├── ollama_client.py     # LLM client + auto-pull
│   │   │   │   └── edit_plan_generator.py # Merge local + LLM edits
│   │   │   └── editing/
│   │   │       ├── ffmpeg_wrapper.py    # Cut, normalize, denoise
│   │   │       ├── silence_compressor.py # Silence detection
│   │   │       └── renderer.py          # Final render pipeline
│   │   └── utils/
│   └── tests/
│       ├── test_filler_detector.py
│       └── test_segment_scorer.py
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   └── src/
│       ├── App.js
│       ├── api/client.js            # Axios API layer
│       ├── pages/
│       │   ├── Dashboard.js         # Upload, stats, job list
│       │   ├── JobDetail.js         # Full job view with approval
│       │   └── VideoPlayer.js       # Standalone player
│       ├── components/
│       │   ├── VideoUploader.js     # Multi-file drag-and-drop + preview
│       │   ├── JobTable.js          # Live-updating job list
│       │   ├── ProgressIndicator.js # Pipeline step visualization
│       │   ├── SegmentScoring.js    # Score bars per segment
│       │   ├── TimelineVisualization.js # Visual timeline
│       │   └── VideoComparison.js   # Before/after player
│       └── styles/custom.css
│
├── n8n/
│   ├── Dockerfile
│   └── workflows/
│       └── video_cleaner_pipeline.json
│
└── nginx/
    └── nginx.conf
```

### API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `POST /videos/upload` | POST | Upload single video |
| `POST /videos/upload-batch` | POST | Upload multiple videos |
| `GET /videos/{id}` | GET | Job details |
| `GET /jobs` | GET | List jobs (paginated, filterable) |
| `GET /jobs/{id}/transcript` | GET | Transcript chunks with scores |
| `GET /jobs/{id}/edit-plan` | GET | Edit plan items |
| `PATCH /jobs/{id}/edit-plan/approve` | PATCH | Approve/reject specific edits |
| `PATCH /jobs/{id}/edit-plan/approve-all` | PATCH | Bulk approve/reject |
| `PATCH /jobs/{id}/status` | PATCH | Update job status |
| `POST /pipelines/{id}/ingest` | POST | Run audio extraction + transcription |
| `POST /pipelines/{id}/analyze` | POST | Run scoring + edit plan generation |
| `POST /pipelines/{id}/edit` | POST | Render with approved edits |
| `POST /pipelines/{id}/retry` | POST | Retry from auto-detected or specified step |
| `GET /download/{path}` | GET | Download processed video |
| `GET /health` | GET | Health check |

### Database Schema

```
video_jobs
├── id (UUID, PK)
├── filename, input_path, output_path, audio_path
├── status (pending → extracting_audio → transcribing → analyzing →
│           generating_edit_plan → editing → completed/failed)
├── pipeline_type, error_message, duration_seconds
└── created_at, updated_at

transcript_chunks
├── id (UUID, PK), job_id (FK)
├── start_time, end_time, text, confidence, word_count
├── is_filler
└── clarity_score, engagement_score, filler_score, retention_risk_score

edit_plans
├── id (UUID, PK), job_id (FK)
├── start_time, end_time, action (remove/compress/flag)
├── reason, confidence, source (local/ollama/merged)
├── approved (bool)
└── created_at

pipeline_configs
├── id (UUID, PK), name, description
├── pipeline_type, steps (JSON), is_active
└── created_at
```

### Processing Pipeline

```
Upload → Extract Audio (FFmpeg) → Transcribe (faster-whisper)
    → Score Segments (rule-based + Ollama LLM)
    → Generate Edit Plan → User Reviews & Approves
    → Render (cut + denoise + normalize) → Download
```

### Configuration

All settings are controlled via environment variables (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_MODEL` | `llama3:8b` | Primary LLM model |
| `OLLAMA_REVIEWER_MODEL` | `llama3:8b` | Model for edit plan review |
| `OLLAMA_AUTO_PULL` | `true` | Auto-download models on startup |
| `WHISPER_MODEL_SIZE` | `base` | Whisper model (tiny/base/small/medium/large) |
| `WHISPER_DEVICE` | `cpu` | `cpu` or `cuda` for GPU |
| `WHISPER_COMPUTE_TYPE` | `int8` | `int8` (CPU) or `float16` (GPU) |
| `NOISE_REDUCTION_ENABLED` | `true` | Apply audio noise removal |
| `NOISE_REDUCTION_STRENGTH` | `0.21` | Denoise intensity (0.0-1.0) |
| `MAX_CONCURRENT_JOBS` | `3` | Parallel job limit |
| `FILLER_SCORE_THRESHOLD` | `0.4` | Filler detection sensitivity |
| `SILENCE_THRESHOLD_SECONDS` | `1.5` | Min pause to flag for compression |

See [QUICKSTART.md](QUICKSTART.md) for getting started and [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment.

## License

See [LICENSE](LICENSE) for details.
