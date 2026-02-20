FROM n8nio/n8n:latest

# Copy workflow definitions
COPY workflows/ /home/node/workflows/

# n8n will auto-import workflows from this directory if configured
ENV N8N_USER_FOLDER=/home/node
