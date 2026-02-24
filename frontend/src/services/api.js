import axios from 'axios'

const API_BASE = '/workflow'

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
})

export async function listWorkflows() {
  const response = await api.get('/list')
  return response.data
}

export async function startWorkflow(workflowId, initialContext = {}) {
  const response = await api.post('/start', {
    workflow_id: workflowId,
    initial_context: initialContext,
  })
  return response.data
}

export async function submitInput(sessionId, action, payload = {}) {
  const response = await api.post('/input', {
    session_id: sessionId,
    action,
    payload,
  })
  return response.data
}

export async function getState(sessionId) {
  const response = await api.get(`/state/${sessionId}`)
  return response.data
}
