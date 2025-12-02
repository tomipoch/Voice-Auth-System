import axios, { AxiosError, InternalAxiosRequestConfig, AxiosResponse } from 'axios';
import toast from 'react-hot-toast';
import { apiConfig, features } from '../config/environment.js';
import { authStorage } from './storage.js';

// Variables para manejar el refresh de tokens
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (error: any) => void;
}> = [];

const processQueue = (error: Error | null, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token!);
    }
  });
  failedQueue = [];
};

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
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // Log errors en modo desarrollo
    if (features.debugMode) {
      console.error('❌ API Response Error:', {
        status: error.response?.status,
        url: error.config?.url,
        message: error.message,
      });
    }

    // Manejar errores 401 (Unauthorized) con refresh token
    if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
      // Evitar refresh en endpoints de auth
      if (originalRequest.url?.includes('/auth/login') || 
          originalRequest.url?.includes('/auth/refresh') ||
          originalRequest.url?.includes('/auth/register')) {
        return Promise.reject(error);
      }

      if (isRefreshing) {
        // Si ya se está refrescando, agregar a la cola
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
            }
            return api(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        // Intentar refrescar el token
        const refreshToken = authStorage.getRefreshToken();
        
        if (!refreshToken) {
          throw new Error('No refresh token available');
        }

        const response = await axios.post(
          `${apiConfig.baseURL}/api/auth/refresh`,
          { refresh_token: refreshToken },
          {
            headers: { 'Content-Type': 'application/json' },
          }
        );

        const { access_token } = response.data;

        // Guardar nuevo token
        authStorage.setAccessToken(access_token);

        // Actualizar header del request original
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
        }

        // Procesar cola de requests pendientes
        processQueue(null, access_token);

        if (features.debugMode) {
          console.log('🔄 Token refreshed successfully');
        }

        // Reintentar request original
        return api(originalRequest);
      } catch (refreshError) {
        // Si falla el refresh, limpiar todo y redirigir
        processQueue(refreshError as Error, null);
        authStorage.clearAuth();

        if (!window.location.pathname.includes('/login')) {
          toast.error('Sesión expirada. Por favor, inicia sesión nuevamente.');
          window.location.href = '/login';
        }

        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    // Otros errores
    if (error.response?.status && error.response.status >= 500) {
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
