// Configuration for Banco Pirulete Demo

export const config = {
  // Bank backend port
  port: 3001,
  
  // Main biometric API configuration
  biometricApi: {
    baseUrl: 'http://localhost:8000',
    apiKey: 'banco-pirulete-key-2024',
  },
  
  // Bank company info (sent with every API call)
  company: {
    name: 'Banco Pirulete',
    clientId: 'banco-pirulete',
  },
};

export default config;
