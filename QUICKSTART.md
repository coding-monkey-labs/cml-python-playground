# Quick Start Guide

Get the AI Video Cleaner running on your machine in under 10 minutes.

## Prerequisites

- **Docker** v20+ and **Docker Compose** v2+
- **8 GB RAM** minimum (16 GB recommended for LLM)
- **~10 GB disk** for models and Docker images
- (Optional) **NVIDIA GPU** with drivers for faster transcription

Check your setup:

```bash
docker --version          # Docker 20+
docker compose version    # Compose v2+
nvidia-smi                # Optional: GPU check
```

## Step 1: Clone and Configure

```bash
git clone <your-repo-url> ai-video-cleaner
cd ai-video-cleaner

# Create your environment file
cp .env.example .env
```

Edit `.env` if you want to change defaults. The only things you might want to tweak:

```bash
# For GPU-accelerated transcription (much faster):
WHISPER_DEVICE=cuda
WHISPER_COMPUTE_TYPE=float16

# For a different LLM model:
OLLAMA_MODEL=mistral:7b
OLLAMA_REVIEWER_MODEL=mistral:7b
```

## Step 2: Launch Everything

```bash
docker compose up -d
```

This starts 6 services:
- **PostgreSQL** (port 5432) — database
- **Backend** (port 8000) — FastAPI
- **Frontend** (port 3000) — React UI
- **n8n** (port 5678) — pipeline orchestration
- **Ollama** (port 11434) — local LLM
- **Nginx** (port 80) — reverse proxy

First startup takes 5-10 minutes (building images, downloading models).

Watch the progress:

```bash
docker compose logs -f backend
```

You'll see:
```
Starting AI Video Cleaner Platform...
Database tables created.
Ollama model 'llama3:8b': ready
```

## Step 3: Open the UI

Go to **http://localhost:3000** in your browser.

You'll see the Dashboard with:
- Upload area (drag and drop)
- Job stats
- Empty jobs table

## Step 4: Process Your First Video

1. **Drag a video** into the upload zone (or click to browse)
2. **Preview** the video inline before uploading
3. Click **Upload & Process**
4. Watch the job progress through the pipeline steps:
   - Extracting Audio
   - Transcribing
   - Analyzing
   - Generating Edit Plan

5. When analysis is complete, click into the job to **review the edit plan**
6. **Approve or reject** individual edits (or use Approve All / Reject All)
7. Click **Render Approved Edits**
8. **Download** the cleaned video or use the side-by-side comparison

## Step 5: Batch Processing

For multiple videos at once:

1. **Drag multiple files** into the upload zone
2. Remove any you don't want with the X button
3. Click **Upload & Process N Videos**
4. Each video gets its own job, processed independently

## Common Operations

### Check service health

```bash
# All services running?
docker compose ps

# Backend health
curl http://localhost:8000/health

# Ollama ready?
curl http://localhost:11434/api/tags
```

### View logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f ollama
```

### Retry a failed job

Two options:
1. **UI**: Click into the failed job, hit **Retry** (auto-detects where to resume)
2. **API**: `curl -X POST http://localhost:8000/pipelines/{JOB_ID}/retry`

### Stop everything

```bash
docker compose down          # Stop services (keep data)
docker compose down -v       # Stop and delete all data
```

### Restart a single service

```bash
docker compose restart backend
docker compose restart ollama
```

## Tuning for Your Content

### Whisper model size

Bigger models = better accuracy but slower:

| Model | Size | Speed | Accuracy |
|-------|------|-------|----------|
| `tiny` | 39 MB | Fastest | Basic |
| `base` | 74 MB | Fast | Good (default) |
| `small` | 244 MB | Medium | Better |
| `medium` | 769 MB | Slow | Great |
| `large-v3` | 1.5 GB | Slowest | Best |

Change in `.env`:
```bash
WHISPER_MODEL_SIZE=small
```

### Noise reduction

Control how aggressively background noise is removed:

```bash
NOISE_REDUCTION_ENABLED=true
NOISE_REDUCTION_STRENGTH=0.21    # 0.0 = off, 1.0 = maximum
```

For noisy recordings, try `0.4`. For clean recordings, `0.15` or disable.

### Filler detection sensitivity

Lower threshold = more aggressive removal:

```bash
FILLER_SCORE_THRESHOLD=0.4       # Default: moderate
SILENCE_THRESHOLD_SECONDS=1.5    # Pauses longer than this get flagged
```

### LLM model

Any Ollama-compatible model works. Smaller = faster, larger = smarter:

```bash
OLLAMA_MODEL=llama3:8b           # Default: good balance
OLLAMA_MODEL=mistral:7b          # Alternative: fast
OLLAMA_MODEL=llama3:70b          # If you have the GPU for it
```

## Ports Reference

| Port | Service | URL |
|------|---------|-----|
| 80 | Nginx (full app) | http://localhost |
| 3000 | React UI (direct) | http://localhost:3000 |
| 8000 | FastAPI (direct) | http://localhost:8000 |
| 5678 | n8n Dashboard | http://localhost:5678 |
| 11434 | Ollama API | http://localhost:11434 |
| 5432 | PostgreSQL | localhost:5432 |

## Troubleshooting

### "Ollama not reachable" on startup

Normal — Ollama takes a few seconds to start. The backend retries automatically. Check:
```bash
docker compose logs ollama
```

### Transcription is very slow

You're running on CPU. For GPU acceleration:
```bash
# In .env:
WHISPER_DEVICE=cuda
WHISPER_COMPUTE_TYPE=float16
```
Requires NVIDIA GPU with Docker GPU support.

### "No space left on device"

Video processing creates temporary files. Clean up:
```bash
docker compose exec backend rm -rf /data/videos/audio/* /data/videos/processed/*
```

### n8n webhook not triggering

The n8n workflow needs to be imported on first run:
1. Go to http://localhost:5678
2. Login (admin / changeme)
3. Import workflow from `/home/node/workflows/video_cleaner_pipeline.json`
4. Activate the workflow

### GPU not detected by Ollama

Ensure NVIDIA Container Toolkit is installed:
```bash
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

## Next Steps

- See [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment
- See [README.md](README.md) for full API reference and architecture
