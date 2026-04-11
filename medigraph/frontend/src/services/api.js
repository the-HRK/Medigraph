import axios from 'axios';

const API_BASE = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const sendQuery = async (query) => {
  const response = await api.post('/query/', { query });
  return response.data;
};

export const sendChat = async (message, history = []) => {
  const response = await api.post('/chat/', { message, history });
  return response.data;
};

export const getGraphData = async (diseaseName) => {
  const response = await api.get(`/graph/disease/${encodeURIComponent(diseaseName)}`);
  return response.data;
};

export const getExploreGraph = async (limit = 50) => {
  const response = await api.get(`/graph/explore`, { params: { limit } });
  return response.data;
};

export const getGraphStats = async () => {
  const response = await api.get('/graph/stats');
  return response.data;
};

export const getHealth = async () => {
  const response = await api.get('/health');
  return response.data;
};

export const getStats = async () => {
  const response = await api.get('/stats');
  return response.data;
};

export default api;
