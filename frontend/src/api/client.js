import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 600000, // 10 min for large uploads
});

// ── Videos ───────────────────────────────────────

export async function uploadVideo(file, pipelineType = 'cleaner', onProgress) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('pipeline_type', pipelineType);

  const response = await api.post('/videos/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (event) => {
      if (onProgress && event.total) {
        onProgress(Math.round((event.loaded * 100) / event.total));
      }
    },
  });

  return response.data;
}

export async function getVideoJob(jobId) {
  const response = await api.get(`/videos/${jobId}`);
  return response.data;
}

// ── Jobs ─────────────────────────────────────────

export async function listJobs(skip = 0, limit = 20, status = null) {
  const params = { skip, limit };
  if (status) params.status = status;
  const response = await api.get('/jobs', { params });
  return response.data;
}

// ── Transcript ───────────────────────────────────

export async function getTranscript(jobId) {
  const response = await api.get(`/jobs/${jobId}/transcript`);
  return response.data;
}

// ── Edit Plan ────────────────────────────────────

export async function getEditPlan(jobId) {
  const response = await api.get(`/jobs/${jobId}/edit-plan`);
  return response.data;
}

// ── Pipeline Triggers (manual) ───────────────────

export async function triggerIngestion(jobId) {
  const response = await api.post(`/pipelines/${jobId}/ingest`);
  return response.data;
}

export async function triggerAnalysis(jobId) {
  const response = await api.post(`/pipelines/${jobId}/analyze`);
  return response.data;
}

export async function triggerEditing(jobId) {
  const response = await api.post(`/pipelines/${jobId}/edit`);
  return response.data;
}

// ── Media URLs ───────────────────────────────────

export function getMediaUrl(path) {
  if (!path) return null;
  // Convert absolute server path to media URL
  const relativePath = path.replace(/^\/data\/videos\//, '');
  return `${API_BASE}/media/${relativePath}`;
}

export default api;
