import api from './api';

// Servicios de autenticación
export const authService = {
  // Login del usuario
  login: async (credentials) => {
    const response = await api.post('/auth/login', credentials);
    return response.data;
  },

  // Registro de usuario
  register: async (userData) => {
    const response = await api.post('/auth/register', userData);
    return response.data;
  },

  // Logout
  logout: async () => {
    const response = await api.post('/auth/logout');
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    return response.data;
  },

  // Obtener perfil del usuario
  getProfile: async () => {
    const response = await api.get('/auth/profile');
    return response.data;
  },
};

// Servicios de enrollment (registro de voz)
export const enrollmentService = {
  // Iniciar proceso de enrollment
  startEnrollment: async (userId) => {
    const response = await api.post('/enrollment/start', { user_id: userId });
    return response.data;
  },

  // Enviar audio para enrollment
  submitAudio: async (enrollmentId, audioBlob, phraseText) => {
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
    const response = await api.post(`/enrollment/complete/${enrollmentId}`);
    return response.data;
  },

  // Obtener progreso del enrollment
  getEnrollmentProgress: async (enrollmentId) => {
    const response = await api.get(`/enrollment/progress/${enrollmentId}`);
    return response.data;
  },
};

// Servicios de verificación de voz
export const verificationService = {
  // Iniciar verificación
  startVerification: async (userId) => {
    const response = await api.post('/verification/start', { user_id: userId });
    return response.data;
  },

  // Enviar audio para verificación
  verifyAudio: async (verificationId, audioBlob, phraseText) => {
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
    const response = await api.get(`/verification/result/${verificationId}`);
    return response.data;
  },
};

// Servicios de administración
export const adminService = {
  // Obtener lista de usuarios
  getUsers: async (page = 1, limit = 10) => {
    const response = await api.get(`/admin/users?page=${page}&limit=${limit}`);
    return response.data;
  },

  // Obtener estadísticas del sistema
  getStats: async () => {
    const response = await api.get('/admin/stats');
    return response.data;
  },

  // Eliminar usuario
  deleteUser: async (userId) => {
    const response = await api.delete(`/admin/users/${userId}`);
    return response.data;
  },

  // Actualizar usuario
  updateUser: async (userId, userData) => {
    const response = await api.patch(`/admin/users/${userId}`, userData);
    return response.data;
  },
};

// Servicios de challenges (frases de verificación)
export const challengeService = {
  // Obtener frase aleatoria para enrollment
  getEnrollmentPhrase: async () => {
    const response = await api.get('/challenges/enrollment');
    return response.data;
  },

  // Obtener frase aleatoria para verificación
  getVerificationPhrase: async () => {
    const response = await api.get('/challenges/verification');
    return response.data;
  },
};