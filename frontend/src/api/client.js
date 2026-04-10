import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' },
});

export async function getStatus() {
  const { data } = await api.get('/api/status');
  return data;
}

export async function getInterfaces() {
  const { data } = await api.get('/api/interfaces');
  return data.interfaces || [];
}

export async function startCapture(interfaceName) {
  const { data } = await api.post('/api/capture/start', {
    interface: interfaceName,
  });
  return data;
}

export async function stopCapture() {
  const { data } = await api.post('/api/capture/stop');
  return data;
}

export async function getAlerts(page = 1, limit = 50, filter = 'all') {
  const { data } = await api.get('/api/alerts', {
    params: { page, limit, filter },
  });
  return data;
}

export async function getStats() {
  const { data } = await api.get('/api/stats');
  return data;
}

export async function batchAnalyze(file) {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await api.post('/api/batch-analyze', formData);
  return data;
}

export default api;
