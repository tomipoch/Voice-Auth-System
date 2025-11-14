// Mock data service para simular el backend durante desarrollo

// Simular delay de red
const simulateNetworkDelay = () => 
  new Promise(resolve => setTimeout(resolve, Math.random() * 1000 + 500));

// Mock users
const mockUsers = [
  {
    id: 'dev-user-1',
    name: 'Usuario Desarrollo',
    email: 'dev@test.com',
    role: 'user',
    voice_template: null,
    created_at: '2024-11-01T10:00:00Z',
    last_login: '2024-11-14T09:30:00Z',
    status: 'active',
    enrollment_status: 'pending'
  },
  {
    id: 'admin-user-1',
    name: 'Admin Desarrollo',
    email: 'admin@test.com',
    role: 'admin',
    voice_template: {
      id: 'vt-admin-1',
      created_at: '2024-11-01T10:00:00Z',
      samples_count: 5,
      quality_score: 0.95
    },
    created_at: '2024-11-01T09:00:00Z',
    last_login: '2024-11-14T08:45:00Z',
    status: 'active',
    enrollment_status: 'completed'
  },
  {
    id: 'user-2',
    name: 'María García',
    email: 'maria@ejemplo.com',
    role: 'user',
    voice_template: {
      id: 'vt-user-2',
      created_at: '2024-11-02T14:30:00Z',
      samples_count: 3,
      quality_score: 0.87
    },
    created_at: '2024-11-02T14:00:00Z',
    last_login: '2024-11-13T16:20:00Z',
    status: 'active',
    enrollment_status: 'completed'
  },
  {
    id: 'user-3',
    name: 'Carlos López',
    email: 'carlos@ejemplo.com',
    role: 'user',
    voice_template: null,
    created_at: '2024-11-03T11:15:00Z',
    last_login: '2024-11-10T12:00:00Z',
    status: 'inactive',
    enrollment_status: 'pending'
  }
];

// Mock phrases para enrollment y verification
const enrollmentPhrases = [
  "Mi voz es única como mi huella digital",
  "Utilizo mi voz para acceder de forma segura",
  "Mi identidad vocal es mi clave de acceso",
  "Solo mi voz puede abrir esta puerta digital",
  "La biometría vocal protege mis datos"
];

const verificationPhrases = [
  "Verifico mi identidad con mi voz",
  "Mi voz es mi contraseña segura",
  "Accedo usando mi firma vocal",
  "Mi voz autentica mi identidad",
  "Biometría vocal para máxima seguridad"
];

// Mock enrollment sessions
let mockEnrollmentSessions = new Map();
let mockVerificationSessions = new Map();

// Mock statistics
const mockStats = {
  total_users: 156,
  active_users: 143,
  total_verifications_today: 89,
  successful_verifications_today: 84,
  success_rate: 94.2,
  avg_response_time: 142,
  enrollment_completion_rate: 78.5,
  system_uptime: 99.8
};

// Mock activity log
const mockRecentActivity = [
  {
    id: 'act-1',
    user_id: 'user-2',
    user_name: 'María García',
    action: 'verification_success',
    timestamp: '2024-11-14T10:15:00Z',
    details: 'Verificación exitosa desde dispositivo móvil'
  },
  {
    id: 'act-2',
    user_id: 'user-3',
    user_name: 'Carlos López',
    action: 'enrollment_started',
    timestamp: '2024-11-14T10:10:00Z',
    details: 'Iniciado proceso de enrollment'
  },
  {
    id: 'act-3',
    user_id: 'dev-user-1',
    user_name: 'Usuario Desarrollo',
    action: 'login',
    timestamp: '2024-11-14T09:30:00Z',
    details: 'Inicio de sesión exitoso'
  },
  {
    id: 'act-4',
    user_id: 'user-2',
    user_name: 'María García',
    action: 'verification_failed',
    timestamp: '2024-11-14T09:25:00Z',
    details: 'Verificación fallida - ruido ambiental detectado'
  }
];

export const mockApiService = {
  // Auth services
  auth: {
    login: async (credentials) => {
      await simulateNetworkDelay();
      
      // Mock login logic
      const user = mockUsers.find(u => u.email === credentials.email);
      if (!user) {
        throw new Error('Usuario no encontrado');
      }
      
      // Simular validación de contraseña
      if (credentials.password !== '123456') {
        throw new Error('Contraseña incorrecta');
      }
      
      return {
        user,
        token: `mock-token-${user.id}-${Date.now()}`,
        expires_in: 3600
      };
    },

    register: async (userData) => {
      await simulateNetworkDelay();
      
      // Simular validación de email único
      if (mockUsers.find(u => u.email === userData.email)) {
        throw new Error('El email ya está registrado');
      }
      
      const newUser = {
        id: `user-${Date.now()}`,
        name: userData.name,
        email: userData.email,
        role: 'user',
        voice_template: null,
        created_at: new Date().toISOString(),
        last_login: null,
        status: 'active',
        enrollment_status: 'pending'
      };
      
      mockUsers.push(newUser);
      return { message: 'Usuario registrado exitosamente', user_id: newUser.id };
    },

    getProfile: async (userId) => {
      await simulateNetworkDelay();
      const user = mockUsers.find(u => u.id === userId);
      if (!user) {
        throw new Error('Usuario no encontrado');
      }
      return user;
    }
  },

  // Enrollment services
  enrollment: {
    startEnrollment: async (userId) => {
      await simulateNetworkDelay();
      
      const enrollmentId = `enr-${userId}-${Date.now()}`;
      const session = {
        id: enrollmentId,
        user_id: userId,
        status: 'in_progress',
        samples_recorded: 0,
        samples_required: 5,
        current_phrase: enrollmentPhrases[0],
        created_at: new Date().toISOString()
      };
      
      mockEnrollmentSessions.set(enrollmentId, session);
      return session;
    },

    submitAudio: async (enrollmentId, audioBlob, phraseText) => {
      // audioBlob y phraseText serán usados en la implementación real
      console.log('Processing audio for enrollment:', { enrollmentId, audioSize: audioBlob?.size, phrase: phraseText });
      await simulateNetworkDelay();
      
      const session = mockEnrollmentSessions.get(enrollmentId);
      if (!session) {
        throw new Error('Sesión de enrollment no encontrada');
      }
      
      // Simular procesamiento de audio
      const quality_score = Math.random() * 0.3 + 0.7; // 70-100%
      const is_acceptable = quality_score > 0.75;
      
      if (is_acceptable) {
        session.samples_recorded += 1;
        
        if (session.samples_recorded < session.samples_required) {
          session.current_phrase = enrollmentPhrases[session.samples_recorded];
        } else {
          session.status = 'completed';
        }
      }
      
      mockEnrollmentSessions.set(enrollmentId, session);
      
      return {
        success: is_acceptable,
        quality_score,
        message: is_acceptable ? 
          'Muestra de voz aceptada' : 
          'Calidad insuficiente, intenta nuevamente',
        samples_recorded: session.samples_recorded,
        samples_required: session.samples_required,
        next_phrase: session.current_phrase,
        enrollment_completed: session.status === 'completed'
      };
    },

    completeEnrollment: async (enrollmentId) => {
      await simulateNetworkDelay();
      
      const session = mockEnrollmentSessions.get(enrollmentId);
      if (!session || session.status !== 'completed') {
        throw new Error('Enrollment no completado o no encontrado');
      }
      
      // Actualizar usuario con template de voz
      const user = mockUsers.find(u => u.id === session.user_id);
      if (user) {
        user.voice_template = {
          id: `vt-${session.user_id}`,
          created_at: new Date().toISOString(),
          samples_count: session.samples_recorded,
          quality_score: 0.92
        };
        user.enrollment_status = 'completed';
      }
      
      mockEnrollmentSessions.delete(enrollmentId);
      
      return {
        message: 'Enrollment completado exitosamente',
        voice_template_id: `vt-${session.user_id}`
      };
    }
  },

  // Verification services
  verification: {
    startVerification: async (userId) => {
      await simulateNetworkDelay();
      
      const verificationId = `ver-${userId}-${Date.now()}`;
      const phrase = verificationPhrases[Math.floor(Math.random() * verificationPhrases.length)];
      
      const session = {
        id: verificationId,
        user_id: userId,
        challenge_phrase: phrase,
        status: 'waiting_audio',
        created_at: new Date().toISOString()
      };
      
      mockVerificationSessions.set(verificationId, session);
      return session;
    },

    verifyAudio: async (verificationId, audioBlob, phraseText) => {
      // audioBlob y phraseText serán usados en la implementación real
      console.log('Processing audio for verification:', { verificationId, audioSize: audioBlob?.size, phrase: phraseText });
      await simulateNetworkDelay();
      
      const session = mockVerificationSessions.get(verificationId);
      if (!session) {
        throw new Error('Sesión de verificación no encontrada');
      }
      
      // Simular verificación (80% de éxito)
      const confidence_score = Math.random() * 0.4 + 0.6; // 60-100%
      const success = confidence_score > 0.75;
      
      session.status = 'completed';
      session.result = {
        success,
        confidence_score,
        processed_at: new Date().toISOString()
      };
      
      mockVerificationSessions.set(verificationId, session);
      
      return {
        verification_id: verificationId,
        success,
        confidence_score,
        message: success ? 
          'Verificación exitosa' : 
          'Verificación fallida - intenta nuevamente',
        threshold: 0.75
      };
    }
  },

  // Admin services
  admin: {
    getUsers: async (page = 1, limit = 10) => {
      await simulateNetworkDelay();
      
      const startIndex = (page - 1) * limit;
      const endIndex = startIndex + limit;
      const paginatedUsers = mockUsers.slice(startIndex, endIndex);
      
      return {
        users: paginatedUsers,
        total: mockUsers.length,
        page,
        limit,
        total_pages: Math.ceil(mockUsers.length / limit)
      };
    },

    getStats: async () => {
      await simulateNetworkDelay();
      return mockStats;
    },

    deleteUser: async (userId) => {
      await simulateNetworkDelay();
      
      const index = mockUsers.findIndex(u => u.id === userId);
      if (index === -1) {
        throw new Error('Usuario no encontrado');
      }
      
      mockUsers.splice(index, 1);
      return { message: 'Usuario eliminado exitosamente' };
    },

    updateUser: async (userId, userData) => {
      await simulateNetworkDelay();
      
      const user = mockUsers.find(u => u.id === userId);
      if (!user) {
        throw new Error('Usuario no encontrado');
      }
      
      Object.assign(user, userData);
      return { message: 'Usuario actualizado exitosamente', user };
    },

    getRecentActivity: async (limit = 10) => {
      await simulateNetworkDelay();
      return mockRecentActivity.slice(0, limit);
    }
  },

  // Challenge services
  challenges: {
    getEnrollmentPhrase: async () => {
      await simulateNetworkDelay();
      const phrase = enrollmentPhrases[Math.floor(Math.random() * enrollmentPhrases.length)];
      return { phrase, id: `phrase-enr-${Date.now()}` };
    },

    getVerificationPhrase: async () => {
      await simulateNetworkDelay();
      const phrase = verificationPhrases[Math.floor(Math.random() * verificationPhrases.length)];
      return { phrase, id: `phrase-ver-${Date.now()}` };
    }
  }
};

// Export individual services for easier use
export const {
  auth: mockAuthService,
  enrollment: mockEnrollmentService,
  verification: mockVerificationService,
  admin: mockAdminService,
  challenges: mockChallengeService
} = mockApiService;