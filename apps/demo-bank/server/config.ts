// Configuration for Banco Familia Demo

export const config = {
  // Bank backend port
  port: 3001,
  
  // JWT Secret
  jwtSecret: 'banco-familia-secret-key-2024-demo',
  jwtExpiresIn: '24h',
  
  // Main biometric API configuration
  biometricApi: {
    baseUrl: 'http://localhost:8000',
    // Credenciales para autenticarse en la API biométrica
    // El banco debe tener una cuenta en el sistema biométrico
    adminEmail: 'admin@familia.com',
    adminPassword: 'AdminFamilia123',
  },
  
  // Bank company info
  company: {
    name: 'Banco Familia',
    clientId: 'banco-familia',
  },
};

export default config;
