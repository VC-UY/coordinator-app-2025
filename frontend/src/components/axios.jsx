import axios from 'axios';

const baseUrl = import.meta.env.PROD ? '/api/' : 'http://127.0.0.1:8001/api/';

const AxiosInstance = axios.create({
  baseURL: baseUrl,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    accept: 'application/json',
  },
});

AxiosInstance.interceptors.request.use((config) => {
  const token = localStorage.getItem('coordinator_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

AxiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && !error.config?.url?.includes('auth/login')) {
      localStorage.removeItem('coordinator_token');
      localStorage.removeItem('coordinator_email');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  },
);

export default AxiosInstance;
