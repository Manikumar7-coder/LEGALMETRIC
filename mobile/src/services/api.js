import axios from 'axios';
import { Platform } from 'react-native';

// In Android emulator, 10.0.2.2 maps to host machine localhost.
// In iOS simulator or web preview, localhost:8000 is used.
export const DEFAULT_API_BASE_URL = Platform.OS === 'android' 
  ? 'http://10.0.2.2:8000/api'
  : 'http://127.0.0.1:8000/api';

let authToken = null;
let currentBaseUrl = DEFAULT_API_BASE_URL;

const api = axios.create({
  baseURL: currentBaseUrl,
  timeout: 30000,
});

export const setAuthToken = (token) => {
  authToken = token;
};

export const setCustomBaseUrl = (url) => {
  currentBaseUrl = url;
  api.defaults.baseURL = url;
};

api.interceptors.request.use((config) => {
  if (authToken) {
    config.headers.Authorization = `Bearer ${authToken}`;
  }
  return config;
});

export const authAPI = {
  login: async (email, password) => {
    const res = await api.post('/auth/login', { email, password });
    return res.data;
  },
  register: async (name, email, password, role, organization) => {
    const res = await api.post('/auth/register', { name, email, password, role, organization });
    return res.data;
  },
  getMe: async () => {
    const res = await api.get('/auth/me');
    return res.data;
  },
};

export const dashboardAPI = {
  getStats: async () => {
    const res = await api.get('/dashboard/stats');
    return res.data;
  },
};

export const inspectionAPI = {
  analyze: async (formData) => {
    const res = await api.post('/inspections/analyze', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  },
  list: async (params = {}) => {
    const res = await api.get('/inspections', { params });
    return res.data;
  },
  getById: async (id) => {
    const res = await api.get(`/inspections/${id}`);
    return res.data;
  },
};

export const reportAPI = {
  list: async () => {
    const res = await api.get('/reports');
    return res.data;
  },
  getDownloadUrl: (id, format = 'pdf') => {
    const tokenParam = authToken ? `&token=${encodeURIComponent(authToken)}` : '';
    return `${currentBaseUrl}/reports/${id}/download?format=${format}${tokenParam}`;
  },
};

export const profileAPI = {
  get: async () => {
    const res = await api.get('/profile');
    return res.data;
  },
  update: async (data) => {
    const res = await api.put('/profile', data);
    return res.data;
  },
};

export default api;
