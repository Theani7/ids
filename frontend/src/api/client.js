import axios from 'axios';

const api = axios.create({
  baseURL: '',
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' },
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('[API] Request error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    console.log(`[API] Response ${response.status}:`, response.config.url);
    return response;
  },
  (error) => {
    if (error.response) {
      console.error(`[API] Error ${error.response.status}:`, error.response.data);
    } else if (error.request) {
      console.error('[API] No response received:', error.message);
    } else {
      console.error('[API] Request error:', error.message);
    }
    return Promise.reject(error);
  }
);

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

// Traffic & Protocol Stats
export async function getTrafficStats(hours = 24) {
  const { data } = await api.get('/api/traffic', { params: { hours } });
  return data;
}

export async function getProtocolStats(hours = 24) {
  const { data } = await api.get('/api/protocols', { params: { hours } });
  return data;
}

// Trends & Geography
export async function getTrends(days = 7) {
  const { data } = await api.get('/api/trends', { params: { days } });
  return data;
}

export async function getGeography(days = 7) {
  const { data } = await api.get('/api/geography', { params: { days } });
  return data;
}

// DNS & HTTP Monitoring
export async function getDNSQueries(page = 1, limit = 50, filter = 'all') {
  const { data } = await api.get('/api/dns', { params: { page, limit, filter } });
  return data;
}

export async function getHTTPRequests(page = 1, limit = 50, filter = 'all') {
  const { data } = await api.get('/api/http', { params: { page, limit, filter } });
  return data;
}

// VPN/Tunnel Detection
export async function getVPNTunnels(hours = 24) {
  const { data } = await api.get('/api/vpn-tunnels', { params: { hours } });
  return data;
}

// PCAP Upload
export async function uploadPCAP(file) {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await api.post('/api/pcap/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

// Export Reports
export function exportCSV(days = 7) {
  window.open(`/api/export/csv?days=${days}`, '_blank');
}

export function exportJSON(days = 7) {
  window.open(`/api/export/json?days=${days}`, '_blank');
}

// Debug: Check database counts
export async function getDebugCounts() {
  const { data } = await api.get('/api/debug/counts');
  return data;
}

export default api;
