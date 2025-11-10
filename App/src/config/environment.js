/**
 * Environment Configuration Service
 * Centraliza el manejo de variables de entorno para diferentes ambientes
 */

// Environment detection
export const ENV = {
  DEVELOPMENT: 'development',
  STAGING: 'staging',
  PRODUCTION: 'production'
};

/**
 * Obtiene el valor de una variable de entorno con fallback
 */
const getEnvVar = (key, defaultValue = '') => {
  return import.meta.env[key] ?? defaultValue;
};

/**
 * Convierte string a boolean
 */
const getBoolEnvVar = (key, defaultValue = false) => {
  const value = getEnvVar(key).toLowerCase();
  return value === 'true' || value === '1';
};

/**
 * Convierte string a number
 */
const getNumEnvVar = (key, defaultValue = 0) => {
  const value = getEnvVar(key);
  const parsed = parseInt(value, 10);
  return isNaN(parsed) ? defaultValue : parsed;
};

/**
 * Detecta el ambiente actual
 */
const getCurrentEnvironment = () => {
  const nodeEnv = getEnvVar('VITE_NODE_ENV') || getEnvVar('NODE_ENV') || 'development';
  const mode = import.meta.env.MODE || 'development';
  
  // Prioridad: VITE_NODE_ENV > MODE > NODE_ENV
  const env = getEnvVar('VITE_NODE_ENV') || mode || nodeEnv;
  
  switch (env) {
    case 'production':
    case 'prod':
      return ENV.PRODUCTION;
    case 'staging':
    case 'stage':
      return ENV.STAGING;
    default:
      return ENV.DEVELOPMENT;
  }
};

// Current environment
export const currentEnv = getCurrentEnvironment();

// Development mode checks
export const isDevelopment = currentEnv === ENV.DEVELOPMENT;
export const isStaging = currentEnv === ENV.STAGING;
export const isProduction = currentEnv === ENV.PRODUCTION;

// App configuration
export const appConfig = {
  name: getEnvVar('VITE_APP_NAME', 'VoiceAuth'),
  version: getEnvVar('VITE_APP_VERSION', '1.0.0'),
  environment: currentEnv,
  debug: getBoolEnvVar('VITE_DEBUG', isDevelopment),
  logLevel: getEnvVar('VITE_LOG_LEVEL', 'info'),
};

// API configuration
export const apiConfig = {
  baseURL: getEnvVar('VITE_API_BASE_URL') || getEnvVar('VITE_API_URL', 'http://localhost:8000'),
  timeout: getNumEnvVar('VITE_API_TIMEOUT', 30000),
  retries: getNumEnvVar('VITE_API_RETRIES', 3),
  enableMock: getBoolEnvVar('VITE_ENABLE_MOCK_DATA', isDevelopment),
};

// Authentication configuration
export const authConfig = {
  tokenKey: getEnvVar('VITE_JWT_TOKEN_KEY', 'voiceauth_token'),
  refreshKey: getEnvVar('VITE_JWT_REFRESH_KEY', 'voiceauth_refresh_token'),
  storagePrefix: getEnvVar('VITE_STORAGE_PREFIX', 'voiceauth_'),
  sessionTimeout: getNumEnvVar('VITE_SESSION_TIMEOUT', 3600000),
  jwtSecret: getEnvVar('VITE_JWT_SECRET', 'dev-secret-key'),
  tokenExpiration: getEnvVar('VITE_JWT_EXPIRES_IN', '1h'),
  refreshTokenExpiration: getEnvVar('VITE_REFRESH_TOKEN_EXPIRES_IN', '7d'),
};

// Audio configuration
export const audioConfig = {
  sampleRate: getNumEnvVar('VITE_AUDIO_SAMPLE_RATE', 16000),
  bitDepth: getNumEnvVar('VITE_AUDIO_BIT_DEPTH', 16),
  maxDuration: getNumEnvVar('VITE_AUDIO_MAX_DURATION', 10),
  minDuration: getNumEnvVar('VITE_AUDIO_MIN_DURATION', 3),
};

// Feature flags
export const features = {
  mockData: getBoolEnvVar('VITE_ENABLE_MOCK_DATA', isDevelopment),
  devTools: getBoolEnvVar('VITE_ENABLE_DEV_TOOLS', isDevelopment),
  errorOverlay: getBoolEnvVar('VITE_ENABLE_ERROR_OVERLAY', isDevelopment),
  consoleLogs: getBoolEnvVar('VITE_ENABLE_CONSOLE_LOGS', !isProduction),
  analytics: getBoolEnvVar('VITE_ENABLE_ANALYTICS', isProduction),
  performanceMonitoring: getBoolEnvVar('VITE_ENABLE_PERFORMANCE_MONITORING', isProduction),
  voiceEnrollment: getBoolEnvVar('VITE_ENABLE_VOICE_ENROLLMENT', true),
  voiceVerification: getBoolEnvVar('VITE_ENABLE_VOICE_VERIFICATION', true),
  adminPanel: getBoolEnvVar('VITE_ENABLE_ADMIN_PANEL', true),
  debugMode: getBoolEnvVar('VITE_ENABLE_DEBUG_MODE', isDevelopment),
  darkMode: getBoolEnvVar('VITE_ENABLE_DARK_MODE', true),
};

// UI configuration
export const uiConfig = {
  toastDuration: getNumEnvVar('VITE_TOAST_DURATION', 3000),
  theme: getEnvVar('VITE_DEFAULT_THEME', 'light'),
};

// Security configuration
export const securityConfig = {
  https: getBoolEnvVar('VITE_HTTPS', isProduction),
  corsEnabled: getBoolEnvVar('VITE_CORS_ENABLED', !isProduction),
};

/**
 * Logger condicional basado en el ambiente
 */
export const logger = {
  debug: (...args) => {
    if (features.consoleLogs && appConfig.debug) {
      console.debug('[DEBUG]', ...args);
    }
  },
  info: (...args) => {
    if (features.consoleLogs) {
      console.info('[INFO]', ...args);
    }
  },
  warn: (...args) => {
    if (features.consoleLogs) {
      console.warn('[WARN]', ...args);
    }
  },
  error: (...args) => {
    if (features.consoleLogs) {
      console.error('[ERROR]', ...args);
    }
  },
};

/**
 * Función para logging en desarrollo
 */
export const devLog = (message, data) => {
  if (isDevelopment && appConfig.debug) {
    logger.debug(`[VoiceAuth] ${message}`, data);
  }
};

/**
 * Muestra información del ambiente actual (solo en desarrollo)
 */
export const logEnvironmentInfo = () => {
  if (isDevelopment) {
    logger.info('🚀 VoiceAuth Application Started', {
      environment: appConfig.environment,
      version: appConfig.version,
      apiUrl: apiConfig.baseURL,
      debug: appConfig.debug,
      features,
    });
  }
};

// Configuración completa para export
export const config = {
  app: appConfig,
  api: apiConfig,
  auth: authConfig,
  audio: audioConfig,
  ui: uiConfig,
  security: securityConfig,
  features,
  environment: {
    current: currentEnv,
    isDevelopment,
    isStaging,
    isProduction,
  }
};

export default config;