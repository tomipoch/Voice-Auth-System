import api from './api';
import { mockApiService } from './mockApi';

// Determinar si usar mock API
const isDevelopment = import.meta.env.VITE_DEV_MODE === 'true';
const useRealAPI = !isDevelopment; // En desarrollo usar mock por defecto

// Servicios de autenticación
export const authService = {
  // Login del usuario
  login: async (credentials) => {
    if (!useRealAPI) {
      return await mockApiService.auth.login(credentials);
    }
    const response = await api.post('/auth/login', credentials);
    return response.data;
  },

  // Registro de usuario
  register: async (userData) => {
    if (!useRealAPI) {
      return await mockApiService.auth.register(userData);
    }
    const response = await api.post('/auth/register', userData);
    return response.data;
  },

  // Logout
  logout: async () => {
    if (!useRealAPI) {
      // Mock logout - solo limpiar localStorage
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      return { message: 'Logout exitoso' };
    }
    const response = await api.post('/auth/logout');
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    return response.data;
  },

  // Obtener perfil del usuario
  getProfile: async () => {
    if (!useRealAPI) {
      const user = JSON.parse(localStorage.getItem('user') || '{}');
      return await mockApiService.auth.getProfile(user.id);
    }
    const response = await api.get('/auth/profile');
    return response.data;
  },
};

// Servicios de enrollment (registro de voz)
export const enrollmentService = {
  // Iniciar proceso de enrollment
  startEnrollment: async (userId) => {
    if (!useRealAPI) {
      return await mockApiService.enrollment.startEnrollment(userId);
    }
    const response = await api.post('/enrollment/start', { user_id: userId });
    return response.data;
  },

  // Enviar audio para enrollment
  submitAudio: async (enrollmentId, audioBlob, phraseText) => {
    if (!useRealAPI) {
      return await mockApiService.enrollment.submitAudio(enrollmentId, audioBlob, phraseText);
    }

    const formData = new FormData();
    formData.append('audio', audioBlob, 'enrollment.wav');
    formData.append('enrollment_id', enrollmentId);
    formData.append('phrase_text', phraseText);

    const response = await api.post('/enrollment/audio', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Finalizar enrollment
  completeEnrollment: async (enrollmentId) => {
    if (!useRealAPI) {
      return await mockApiService.enrollment.completeEnrollment(enrollmentId);
    }
    const response = await api.post(`/enrollment/complete/${enrollmentId}`);
    return response.data;
  },

  // Obtener progreso del enrollment
  getEnrollmentProgress: async (enrollmentId) => {
    if (!useRealAPI) {
      // Mock progress - devolver estado de la sesión mock
      return { status: 'in_progress', samples_recorded: 2, samples_required: 5 };
    }
    const response = await api.get(`/enrollment/progress/${enrollmentId}`);
    return response.data;
  },
};

// Servicios de verificación de voz
export const verificationService = {
  // Iniciar verificación
  startVerification: async (userId) => {
    if (!useRealAPI) {
      return await mockApiService.verification.startVerification(userId);
    }
    const response = await api.post('/verification/start', { user_id: userId });
    return response.data;
  },

  // Enviar audio para verificación
  verifyAudio: async (verificationId, audioBlob, phraseText) => {
    if (!useRealAPI) {
      return await mockApiService.verification.verifyAudio(verificationId, audioBlob, phraseText);
    }

    const formData = new FormData();
    formData.append('audio', audioBlob, 'verification.wav');
    formData.append('verification_id', verificationId);
    formData.append('phrase_text', phraseText);

    const response = await api.post('/verification/audio', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Obtener resultado de verificación
  getVerificationResult: async (verificationId) => {
    if (!useRealAPI) {
      // Mock result - resultado ya incluido en verifyAudio
      return { success: true, confidence: 0.89, message: 'Verificación exitosa' };
    }
    const response = await api.get(`/verification/result/${verificationId}`);
    return response.data;
  },
};

// Servicios de administración
export const adminService = {
  // Obtener lista de usuarios
  getUsers: async (page = 1, limit = 10) => {
    if (!useRealAPI) {
      return await mockApiService.admin.getUsers(page, limit);
    }
    const response = await api.get(`/admin/users?page=${page}&limit=${limit}`);
    return response.data;
  },

  // Obtener estadísticas del sistema
  getStats: async () => {
    if (!useRealAPI) {
      return await mockApiService.admin.getStats();
    }
    const response = await api.get('/admin/stats');
    return response.data;
  },

  // Eliminar usuario
  deleteUser: async (userId) => {
    if (!useRealAPI) {
      return await mockApiService.admin.deleteUser(userId);
    }
    const response = await api.delete(`/admin/users/${userId}`);
    return response.data;
  },

  // Actualizar usuario
  updateUser: async (userId, userData) => {
    if (!useRealAPI) {
      return await mockApiService.admin.updateUser(userId, userData);
    }
    const response = await api.patch(`/admin/users/${userId}`, userData);
    return response.data;
  },

  // Obtener actividad reciente
  getRecentActivity: async (limit = 10) => {
    if (!useRealAPI) {
      return await mockApiService.admin.getRecentActivity(limit);
    }
    const response = await api.get(`/admin/activity?limit=${limit}`);
    return response.data;
  },
};

// Servicios de challenges (frases de verificación)
export const challengeService = {
  // Obtener frase aleatoria para enrollment
  getEnrollmentPhrase: async () => {
    if (!useRealAPI) {
      return await mockApiService.challenges.getEnrollmentPhrase();
    }
    const response = await api.get('/challenges/enrollment');
    return response.data;
  },

  // Obtener frase aleatoria para verificación
  getVerificationPhrase: async () => {
    if (!useRealAPI) {
      return await mockApiService.challenges.getVerificationPhrase();
    }
    const response = await api.get('/challenges/verification');
    return response.data;
  },
};
