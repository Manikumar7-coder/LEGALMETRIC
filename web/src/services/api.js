import axios from 'axios';

const API_BASE_URL = (typeof import.meta !== 'undefined' && import.meta.env && (import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL)) || '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor injecting JWT authorization header
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('safemetric_token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor handling 401 unauthorized
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // If token expired, clear and redirect to login
      const isAuthRequest = error.config.url.includes('/auth/login') || error.config.url.includes('/auth/register');
      if (!isAuthRequest) {
        localStorage.removeItem('safemetric_token');
        localStorage.removeItem('safemetric_user');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

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
  logout: async () => {
    try {
      await api.post('/auth/logout');
    } finally {
      localStorage.removeItem('safemetric_token');
      localStorage.removeItem('safemetric_user');
    }
  },
};

export const dashboardAPI = {
  getStats: async () => {
    const res = await api.get('/dashboard/stats');
    return res.data;
  },
};

export const inspectionAPI = {
  upload: async (formData) => {
    const res = await api.post('/inspections/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  },
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
  delete: async (id) => {
    const res = await api.delete(`/inspections/${id}`);
    return res.data;
  },
  getImageUrl: (id) => `/api/inspections/${id}/image`,
};

export const reportAPI = {
  list: async () => {
    const res = await api.get('/reports');
    return res.data;
  },
  getById: async (inspectionId) => {
    const res = await api.get(`/reports/${inspectionId}`);
    return res.data;
  },
  getDownloadUrl: (inspectionId, format = 'pdf') => {
    let token = null;
    try {
      token = localStorage.getItem('safemetric_token');
    } catch (e) {}
    const tokenParam = token ? `&token=${encodeURIComponent(token)}` : '';
    return `/api/reports/${inspectionId}/download?format=${format}${tokenParam}`;
  },
};

export const userAPI = {
  list: async () => {
    const res = await api.get('/users');
    return res.data;
  },
  updateRole: async (userId, role) => {
    const res = await api.put(`/users/${userId}/role`, { role });
    return res.data;
  },
  delete: async (userId) => {
    const res = await api.delete(`/users/${userId}`);
    return res.data;
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

export const settingsAPI = {
  get: async () => {
    const res = await api.get('/settings');
    return res.data;
  },
};

export const rulesAPI = {
  list: async () => {
    const res = await api.get('/rules');
    return res.data;
  },
};

export default api;
