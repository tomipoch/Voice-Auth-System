// @ts-nocheck - Temporalmente deshabilitado hasta refinar mockApi.ts
import api from './api';
import { mockApiService } from './mockApi';
import type {
  LoginCredentials,
  RegisterData,
  AuthResponse,
  ApiResponse,
  User,
  DashboardStats,
  Activity,
  PaginatedResponse,
  Phrase,
  PhraseStats,
} from '../types/index.js';

// Determinar si usar mock API
const useRealAPI = true; // Forzar uso de API real para integración

interface EnrollmentStartResponse {
  enrollment_id: string;
  user_id: string;
  samples_required: number;
}

interface AudioSubmitResponse {
  success: boolean;
  sample_id: string;
  quality_score: number;
  samples_recorded: number;
  samples_required: number;
}

interface EnrollmentCompleteResponse {
  success: boolean;
  voice_template_id: string;
  message: string;
}

interface EnrollmentProgressResponse {
  status: 'in_progress' | 'completed' | 'failed';
  samples_recorded: number;
  samples_required: number;
}

interface VerificationStartResponse {
  verification_id: string;
  user_id: string;
  phrase: string;
}

interface VerificationAudioResponse {
  success: boolean;
  verified: boolean;
  confidence: number;
  message: string;
}

interface VerificationResultResponse {
  success: boolean;
  confidence: number;
  message: string;
}

interface PhraseResponse {
  phrase: string;
  id: string;
}

// Servicios de autenticación
export const authService = {
  // Login del usuario
  login: async (credentials: LoginCredentials): Promise<AuthResponse> => {
    if (!useRealAPI) {
      return await mockApiService.auth.login(credentials);
    }
    const response = await api.post<AuthResponse>('/auth/login', credentials);
    return response.data;
  },

  // Registro de usuario
  register: async (userData: RegisterData): Promise<AuthResponse> => {
    if (!useRealAPI) {
      return await mockApiService.auth.register(userData);
    }
    const response = await api.post<AuthResponse>('/auth/register', userData);
    return response.data;
  },

  // Logout
  logout: async (): Promise<ApiResponse<{ message: string }>> => {
    if (!useRealAPI) {
      // Mock logout - solo limpiar localStorage
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      return { success: true, data: { message: 'Logout exitoso' } };
    }
    const response = await api.post<ApiResponse<{ message: string }>>('/auth/logout');
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    return response.data;
  },

  // Obtener perfil del usuario
  getProfile: async (): Promise<User> => {
    if (!useRealAPI) {
      const user = JSON.parse(localStorage.getItem('user') || '{}');
      const mockResponse = await mockApiService.auth.getProfile(user.id);
      return mockResponse.data as User;
    }
    // El backend devuelve el UserProfile directamente, no envuelto en ApiResponse
    const response = await api.get<User>('/auth/profile');
    return response.data;
  },

  // Refresh access token
  refreshToken: async (): Promise<AuthResponse> => {
    const refreshToken = authStorage.getRefreshToken();

    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await api.post<AuthResponse>('/auth/refresh', {
      refresh_token: refreshToken,
    });

    // Guardar nuevo access token
    if (response.data.access_token) {
      authStorage.setAccessToken(response.data.access_token);
    }

    return response.data;
  },

  // Actualizar perfil del usuario
  updateProfile: async (userData: Partial<User>): Promise<ApiResponse<User>> => {
    if (!useRealAPI) {
      // Mock update
      const currentUser = JSON.parse(localStorage.getItem('user') || '{}');
      const updatedUser = { ...currentUser, ...userData };
      localStorage.setItem('user', JSON.stringify(updatedUser));
      return { success: true, data: updatedUser };
    }
    const response = await api.patch<User>('/auth/profile', userData);
    // Actualizar usuario en localStorage si la respuesta es exitosa
    if (response.data) {
      // La respuesta directa del backend es el objeto UserProfile, no envuelto en ApiResponse
      // Ajustamos según la implementación del backend
      return { success: true, data: response.data };
    }
    return { success: false, error: 'Error updating profile' };
  },

  // Cambiar contraseña del usuario
  changePassword: async (
    currentPassword: string,
    newPassword: string
  ): Promise<ApiResponse<void>> => {
    if (!useRealAPI) {
      // Mock password change
      return { success: true };
    }

    try {
      const response = await api.post('/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword,
      });

      if (response.data?.success) {
        return { success: true };
      }

      return { success: false, error: response.data?.message || 'Error changing password' };
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Error changing password';
      return { success: false, error: errorMessage };
    }
  },
};

// Servicios de enrollment (registro de voz)
export const enrollmentService = {
  // Iniciar proceso de enrollment
  startEnrollment: async (userId: string): Promise<EnrollmentStartResponse> => {
    if (!useRealAPI) {
      return await mockApiService.enrollment.startEnrollment(userId);
    }
    const response = await api.post<EnrollmentStartResponse>('/enrollment/start', {
      user_id: userId,
    });
    return response.data;
  },

  // Enviar audio para enrollment
  submitAudio: async (
    enrollmentId: string,
    audioBlob: Blob,
    phraseText: string
  ): Promise<AudioSubmitResponse> => {
    if (!useRealAPI) {
      return await mockApiService.enrollment.submitAudio(enrollmentId, audioBlob, phraseText);
    }

    const formData = new FormData();
    formData.append('audio', audioBlob, 'enrollment.wav');
    formData.append('enrollment_id', enrollmentId);
    formData.append('phrase_text', phraseText);

    const response = await api.post<AudioSubmitResponse>('/enrollment/add-sample', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Finalizar enrollment
  completeEnrollment: async (enrollmentId: string): Promise<EnrollmentCompleteResponse> => {
    if (!useRealAPI) {
      return await mockApiService.enrollment.completeEnrollment(enrollmentId);
    }
    const response = await api.post<EnrollmentCompleteResponse>(
      `/enrollment/complete/${enrollmentId}`
    );
    return response.data;
  },

  // Obtener progreso del enrollment
  getEnrollmentProgress: async (enrollmentId: string): Promise<EnrollmentProgressResponse> => {
    if (!useRealAPI) {
      // Mock progress - devolver estado de la sesión mock
      return { status: 'in_progress', samples_recorded: 2, samples_required: 5 };
    }
    const response = await api.get<EnrollmentProgressResponse>(
      `/enrollment/status/${enrollmentId}`
    );
    return response.data;
  },
};

// Servicios de verificación de voz
export const verificationService = {
  // Iniciar verificación
  startVerification: async (userId: string): Promise<VerificationStartResponse> => {
    if (!useRealAPI) {
      return await mockApiService.verification.startVerification(userId);
    }
    const response = await api.post<VerificationStartResponse>('/verification/start', {
      user_id: userId,
    });
    return response.data;
  },

  // Enviar audio para verificación
  verifyAudio: async (
    verificationId: string,
    audioBlob: Blob,
    phraseText: string
  ): Promise<VerificationAudioResponse> => {
    if (!useRealAPI) {
      return await mockApiService.verification.verifyAudio(verificationId, audioBlob, phraseText);
    }

    const formData = new FormData();
    formData.append('audio', audioBlob, 'verification.wav');
    formData.append('verification_id', verificationId);
    formData.append('phrase_text', phraseText);

    const response = await api.post<VerificationAudioResponse>('/verification/verify', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Obtener resultado de verificación
  getVerificationResult: async (verificationId: string): Promise<VerificationResultResponse> => {
    if (!useRealAPI) {
      // Mock result - resultado ya incluido en verifyAudio
      return { success: true, confidence: 0.89, message: 'Verificación exitosa' };
    }
    const response = await api.get<VerificationResultResponse>(
      `/verification/result/${verificationId}`
    );
    return response.data;
  },

  // Obtener historial de verificaciones
  getVerificationHistory: async (userId: string, limit = 10): Promise<any> => {
    if (!useRealAPI) {
      return {
        success: true,
        history: [
          {
            id: 1,
            date: '2024-11-30 14:30',
            result: 'success',
            score: 98,
            method: 'Frase Aleatoria',
          },
          { id: 2, date: '2024-11-29 09:15', result: 'success', score: 95, method: 'Frase Fija' },
        ],
      };
    }
    const response = await api.get(`/verification/user/${userId}/history?limit=${limit}`);
    return response.data;
  },
};

// Servicios de administración
export const adminService = {
  // Obtener lista de usuarios
  getUsers: async (page = 1, limit = 10): Promise<PaginatedResponse<User>> => {
    if (!useRealAPI) {
      return await mockApiService.admin.getUsers(page, limit);
    }
    const response = await api.get<PaginatedResponse<User>>(
      `/admin/users?page=${page}&limit=${limit}`
    );
    return response.data;
  },

  // Obtener estadísticas del sistema
  getStats: async (): Promise<DashboardStats> => {
    if (!useRealAPI) {
      return await mockApiService.admin.getStats();
    }
    const response = await api.get<DashboardStats>('/admin/stats');
    return response.data;
  },

  // Eliminar usuario
  deleteUser: async (userId: string): Promise<ApiResponse<{ message: string }>> => {
    if (!useRealAPI) {
      return await mockApiService.admin.deleteUser(userId);
    }
    const response = await api.delete<ApiResponse<{ message: string }>>(`/admin/users/${userId}`);
    return response.data;
  },

  // Actualizar usuario
  updateUser: async (userId: string, userData: Partial<User>): Promise<ApiResponse<User>> => {
    if (!useRealAPI) {
      return await mockApiService.admin.updateUser(userId, userData);
    }
    const response = await api.patch<ApiResponse<User>>(`/admin/users/${userId}`, userData);
    return response.data;
  },

  // Obtener actividad reciente
  getRecentActivity: async (limit = 10): Promise<Activity[]> => {
    if (!useRealAPI) {
      return await mockApiService.admin.getRecentActivity(limit);
    }
    const response = await api.get<Activity[]>(`/admin/activity?limit=${limit}`);
    return response.data;
  },
};

// Servicios de challenges (frases de verificación)
export const challengeService = {
  // Obtener frase aleatoria para enrollment
  getEnrollmentPhrase: async (): Promise<PhraseResponse> => {
    if (!useRealAPI) {
      return await mockApiService.challenges.getEnrollmentPhrase();
    }
    // Usar el endpoint correcto de phrases
    const response = await api.get<Phrase[]>('/phrases/random?count=1&difficulty=medium');
    const phrase = response.data[0];
    return {
      id: phrase.id,
      phrase: phrase.text,
    };
  },

  // Obtener frase aleatoria para verificación
  getVerificationPhrase: async (): Promise<PhraseResponse> => {
    if (!useRealAPI) {
      return await mockApiService.challenges.getVerificationPhrase();
    }
    // Usar el endpoint correcto de phrases
    const response = await api.get<Phrase[]>('/phrases/random?count=1');
    const phrase = response.data[0];
    return {
      id: phrase.id,
      phrase: phrase.text,
    };
  },
};

// Servicios de gestión de frases (Admin)
export const phraseService = {
  // Listar frases
  listPhrases: async (
    difficulty?: string,
    language: string = 'es',
    limit: number = 100
  ): Promise<Phrase[]> => {
    if (!useRealAPI) {
      // TODO: Implement mock for listPhrases if needed
      return [];
    }
    const params = new URLSearchParams();
    if (difficulty) params.append('difficulty', difficulty);
    params.append('language', language);
    params.append('limit', limit.toString());
    const response = await api.get<Phrase[]>(`/phrases/list?${params.toString()}`);
    return response.data;
  },

  // Obtener estadísticas
  getStats: async (language: string = 'es'): Promise<PhraseStats> => {
    if (!useRealAPI) {
      // TODO: Implement mock for getStats if needed
      return { total: 0, easy: 0, medium: 0, hard: 0, language };
    }
    const response = await api.get<PhraseStats>(`/phrases/stats?language=${language}`);
    return response.data;
  },

  // Actualizar estado (activar/desactivar)
  updateStatus: async (
    id: string,
    isActive: boolean
  ): Promise<ApiResponse<{ message: string }>> => {
    if (!useRealAPI) {
      return { success: true, data: { message: 'Estado actualizado (mock)' } };
    }
    const response = await api.patch<ApiResponse<{ message: string }>>(
      `/phrases/${id}/status?is_active=${isActive}`
    );
    return response.data;
  },

  // Eliminar frase
  deletePhrase: async (id: string): Promise<ApiResponse<{ message: string }>> => {
    if (!useRealAPI) {
      return { success: true, data: { message: 'Frase eliminada (mock)' } };
    }
    const response = await api.delete<ApiResponse<{ message: string }>>(`/phrases/${id}`);
    return response.data;
  },
};
