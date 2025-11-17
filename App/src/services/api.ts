import axios, { AxiosError, InternalAxiosRequestConfig, AxiosResponse } from 'axios';
import toast from 'react-hot-toast';
import { apiConfig, features } from '../config/environment.js';
import { authStorage } from './storage.js';

// Crear instancia de axios con configuración de entorno
const api = axios.create({
  baseURL: `${apiConfig.baseURL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: apiConfig.timeout,
});

// Interceptor para requests
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = authStorage.getAccessToken();
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Log requests en modo desarrollo
    if (features.debugMode) {
      console.log('🌐 API Request:', {
        method: config.method?.toUpperCase(),
        url: config.url,
        data: config.data,
      });
    }

    return config;
  },
  (error: AxiosError) => {
    if (features.debugMode) {
      console.error('❌ API Request Error:', error);
    }
    return Promise.reject(error);
  }
);

// Interceptor para responses
api.interceptors.response.use(
  (response: AxiosResponse) => {
    // Log successful responses en modo desarrollo
    if (features.debugMode) {
      console.log('✅ API Response:', {
        status: response.status,
        url: response.config.url,
        data: response.data,
      });
    }
    return response;
  },
  (error: AxiosError) => {
    // Log errors en modo desarrollo
    if (features.debugMode) {
      console.error('❌ API Response Error:', {
        status: error.response?.status,
        url: error.config?.url,
        message: error.message,
      });
    }

    if (error.response?.status === 401) {
      // Limpiar tokens usando authStorage
      authStorage.clearAuth();

      if (!window.location.pathname.includes('/login')) {
        toast.error('Sesión expirada. Por favor, inicia sesión nuevamente.');
        window.location.href = '/login';
      }
    } else if (error.response?.status && error.response.status >= 500) {
      if (!features.debugMode) {
        toast.error('Error del servidor. Intenta nuevamente.');
      }
    } else if (error.code === 'ECONNABORTED') {
      toast.error('Tiempo de espera agotado. Verifica tu conexión.');
    }

    return Promise.reject(error);
  }
);

export default api;
