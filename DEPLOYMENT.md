# Deployment Guide

Production deployment, scaling, and operations for the AI Video Cleaner Platform.

---

## Table of Contents

1. [Deployment Options](#deployment-options)
2. [Single Server (Docker Compose)](#single-server-docker-compose)
3. [Cloud Deployment](#cloud-deployment)
4. [GPU Setup](#gpu-setup)
5. [Security Hardening](#security-hardening)
6. [Backup & Recovery](#backup--recovery)
7. [Monitoring](#monitoring)
8. [Scaling](#scaling)
9. [Updating](#updating)

---

## Deployment Options

| Option | Best For | GPU Support | Complexity |
|--------|----------|-------------|------------|
| Docker Compose (single server) | Personal / small team | Yes | Low |
| Docker Compose + Remote Ollama | CPU server + GPU server | Split | Medium |
| Kubernetes | Team / production | Yes | High |

---

## Single Server (Docker Compose)

### Recommended Server Specs

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 4 cores | 8+ cores |
| RAM | 8 GB | 16-32 GB |
| Disk | 50 GB SSD | 200 GB+ SSD |
| GPU | None (CPU mode) | NVIDIA with 8+ GB VRAM |

### Step-by-Step

#### 1. Server Preparation

```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y
sudo apt install -y docker.io docker-compose-plugin git curl

# Start Docker
sudo systemctl enable docker
sudo systemctl start docker

# Add your user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

#### 2. GPU Setup (Optional but Recommended)

```bash
# Install NVIDIA drivers
sudo apt install -y nvidia-driver-535

# Install NVIDIA Container Toolkit
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt update
sudo apt install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# Verify
nvidia-smi
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi
```

#### 3. Clone and Configure

```bash
git clone <your-repo-url> /opt/video-cleaner
cd /opt/video-cleaner

cp .env.example .env
```

Edit `.env` for production:

```bash
# ── CHANGE THESE ──────────────────────────────────
POSTGRES_PASSWORD=<generate-strong-password>
DATABASE_URL=postgresql+asyncpg://videocleaner:<same-password>@postgres:5432/videocleaner

# ── GPU Settings ──────────────────────────────────
WHISPER_DEVICE=cuda
WHISPER_COMPUTE_TYPE=float16

# ── Larger whisper model for accuracy ─────────────
WHISPER_MODEL_SIZE=small

# ── Storage path (mount a large volume here) ──────
STORAGE_PATH=/data/videos
```

#### 4. Create Storage Directory

```bash
sudo mkdir -p /data/videos/{uploads,audio,processed}
sudo chown -R 1000:1000 /data/videos
```

#### 5. Deploy

```bash
docker compose up -d
```

#### 6. Verify

```bash
# Check all services
docker compose ps

# Check backend health
curl http://localhost:8000/health

# Check logs
docker compose logs --tail=50
```

#### 7. Import n8n Workflow

```bash
# Open n8n dashboard
echo "n8n: http://$(hostname -I | awk '{print $1}'):5678"
echo "Login: admin / changeme"
```

1. Go to n8n dashboard
2. Import workflow from Settings > Import
3. Use the file at `n8n/workflows/video_cleaner_pipeline.json`
4. **Activate** the workflow (toggle switch)

#### 8. Access the Application

```bash
echo "App: http://$(hostname -I | awk '{print $1}')"
echo "API: http://$(hostname -I | awk '{print $1}'):8000"
```

---

## Cloud Deployment

### AWS (EC2)

**Recommended instance types:**

| Instance | vCPUs | RAM | GPU | Use Case |
|----------|-------|-----|-----|----------|
| t3.xlarge | 4 | 16 GB | None | CPU-only, light use |
| g4dn.xlarge | 4 | 16 GB | T4 (16 GB) | GPU, best value |
| g5.xlarge | 4 | 16 GB | A10G (24 GB) | GPU, faster |

```bash
# Launch EC2 with Ubuntu 22.04 AMI
# Security group: open ports 80, 443, 22

# SSH in and follow "Single Server" steps above

# For GPU instances, use the NVIDIA AMI or install drivers manually
```

**Storage**: Attach an EBS volume (gp3, 200 GB) mounted at `/data/videos`.

### GCP (Compute Engine)

```bash
# e2-standard-4 (CPU) or n1-standard-4 + T4 GPU
# Use Container-Optimized OS or Ubuntu

gcloud compute instances create video-cleaner \
  --machine-type=n1-standard-4 \
  --accelerator=type=nvidia-tesla-t4,count=1 \
  --boot-disk-size=200GB \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud
```

### DigitalOcean

```bash
# GPU Droplets or regular Droplets
# Recommended: 8 GB RAM, 4 vCPUs, 160 GB SSD
# Follow "Single Server" steps
```

---

## GPU Setup

### CPU vs GPU Performance Comparison

| Task | CPU (base model) | GPU (base model) | GPU (small model) |
|------|-----------------|------------------|-------------------|
| 5-min video transcription | ~3 min | ~15 sec | ~25 sec |
| 30-min video transcription | ~20 min | ~1.5 min | ~2.5 min |
| LLM analysis | ~30 sec | ~5 sec | ~5 sec |

### No GPU? No Problem

The platform works fully on CPU. It's just slower for transcription.

```bash
# CPU settings (default)
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8
WHISPER_MODEL_SIZE=base
```

### Remove GPU Requirement from Docker Compose

If you don't have an NVIDIA GPU, the Ollama GPU reservation will cause errors. Create a `docker-compose.override.yml`:

```yaml
version: "3.9"
services:
  ollama:
    deploy:
      resources:
        reservations:
          devices: []
```

Or simply remove the `deploy` block from `docker-compose.yml`.

---

## Security Hardening

### 1. Change Default Passwords

```bash
# In .env
POSTGRES_PASSWORD=<strong-random-password>
```

n8n credentials (in docker-compose.yml or .env):
```yaml
N8N_BASIC_AUTH_PASSWORD=<strong-random-password>
```

### 2. HTTPS with Let's Encrypt

Replace the Nginx config for SSL:

```bash
# Install certbot on host
sudo apt install certbot

# Get certificate
sudo certbot certonly --standalone -d yourdomain.com

# Mount certs into nginx container (update docker-compose.yml)
```

Updated `nginx/nginx.conf`:
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    client_max_body_size 2G;

    location /api/ {
        proxy_pass http://backend:8000/;
        proxy_set_header Host $host;
        proxy_read_timeout 600s;
    }

    location / {
        proxy_pass http://frontend:80/;
        proxy_set_header Host $host;
    }
}
```

### 3. Restrict Port Exposure

In production, only expose port 80/443 via Nginx. Change docker-compose.yml:

```yaml
backend:
  ports: []   # Remove direct access, route through Nginx only

postgres:
  ports: []   # No external DB access

ollama:
  ports: []   # Internal only

n8n:
  ports:
    - "127.0.0.1:5678:5678"  # localhost only
```

### 4. Firewall

```bash
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

---

## Backup & Recovery

### Database Backup

```bash
# Manual backup
docker compose exec postgres pg_dump -U videocleaner videocleaner > backup_$(date +%Y%m%d).sql

# Restore
cat backup_20250101.sql | docker compose exec -T postgres psql -U videocleaner videocleaner
```

### Automated Daily Backup

Create `/opt/video-cleaner/backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR=/backups/postgres
mkdir -p $BACKUP_DIR
docker compose -f /opt/video-cleaner/docker-compose.yml exec -T postgres \
  pg_dump -U videocleaner videocleaner | gzip > $BACKUP_DIR/backup_$(date +%Y%m%d_%H%M).sql.gz

# Keep last 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete
```

```bash
chmod +x /opt/video-cleaner/backup.sh
# Add to crontab
echo "0 3 * * * /opt/video-cleaner/backup.sh" | crontab -
```

### Video Files Backup

```bash
# Sync processed videos to external storage
rsync -avz /data/videos/processed/ /backups/videos/
```

---

## Monitoring

### Health Checks

```bash
# Quick check script
#!/bin/bash
echo "Backend: $(curl -s http://localhost:8000/health | jq -r .status)"
echo "Postgres: $(docker compose exec postgres pg_isready -U videocleaner 2>&1 | tail -1)"
echo "Ollama: $(curl -s http://localhost:11434/api/tags | jq '.models | length') models loaded"
echo "Disk: $(df -h /data/videos | tail -1 | awk '{print $5}') used"
```

### Docker Container Monitoring

```bash
# Resource usage
docker stats --no-stream

# Restart counts
docker compose ps
```

### Log Rotation

Docker logs can grow large. Add to `/etc/docker/daemon.json`:

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "50m",
    "max-file": "3"
  }
}
```

Then restart Docker: `sudo systemctl restart docker`

---

## Scaling

### Vertical Scaling (Single Server)

Increase resources for the heaviest services:

```yaml
# docker-compose.override.yml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G

  ollama:
    deploy:
      resources:
        limits:
          memory: 12G
```

### Horizontal: Split Ollama to Dedicated GPU Server

Run Ollama on a separate GPU machine:

```bash
# On GPU server:
docker run -d --gpus all -p 11434:11434 ollama/ollama
docker exec <container> ollama pull llama3:8b

# In .env on main server:
OLLAMA_HOST=http://<gpu-server-ip>:11434
```

Remove the `ollama` service from docker-compose.yml on the main server.

### Processing Queue

The `MAX_CONCURRENT_JOBS` setting limits parallel processing:

```bash
# In .env
MAX_CONCURRENT_JOBS=3    # Adjust based on CPU/RAM available
```

---

## Updating

### Pull Latest Code and Rebuild

```bash
cd /opt/video-cleaner

# Backup first
./backup.sh

# Pull changes
git pull origin main

# Rebuild and restart
docker compose build
docker compose up -d

# Run migrations if schema changed
docker compose exec backend alembic upgrade head
```

### Zero-Downtime Update

```bash
# Build new images
docker compose build

# Restart one service at a time
docker compose up -d --no-deps backend
docker compose up -d --no-deps frontend
```

---

## Maintenance Checklist

| Task | Frequency | Command |
|------|-----------|---------|
| Check disk space | Weekly | `df -h /data/videos` |
| Database backup | Daily (automated) | `backup.sh` |
| Clean old processed files | Monthly | `find /data/videos/processed -mtime +60 -delete` |
| Clean old audio files | Monthly | `find /data/videos/audio -mtime +60 -delete` |
| Update Docker images | Monthly | `docker compose pull && docker compose up -d` |
| Check container health | Weekly | `docker compose ps` |
| Review failed jobs | Weekly | `curl localhost:8000/jobs?status=failed` |
| Rotate logs | Automated | Docker log rotation config |
