/**
 * Rate Limiter para prevenir abuso de requests
 */
export class RateLimiter {
  private requests: Map<string, number[]> = new Map();
  private maxRequests: number;
  private windowMs: number;

  constructor(maxRequests: number = 10, windowMs: number = 60000) {
    this.maxRequests = maxRequests;
    this.windowMs = windowMs;
  }

  /**
   * Verifica si se permite un request
   */
  canMakeRequest(key: string): boolean {
    const now = Date.now();
    const requests = this.requests.get(key) || [];

    // Filtrar requests dentro de la ventana
    const recentRequests = requests.filter((timestamp) => now - timestamp < this.windowMs);

    if (recentRequests.length >= this.maxRequests) {
      return false;
    }

    // Agregar nuevo request
    recentRequests.push(now);
    this.requests.set(key, recentRequests);

    return true;
  }

  /**
   * Obtiene tiempo de espera hasta el próximo request permitido
   */
  getWaitTime(key: string): number {
    const now = Date.now();
    const requests = this.requests.get(key) || [];

    if (requests.length < this.maxRequests) {
      return 0;
    }

    const oldestRequest = Math.min(...requests);
    return Math.max(0, this.windowMs - (now - oldestRequest));
  }

  /**
   * Resetea el contador para una key
   */
  reset(key: string): void {
    this.requests.delete(key);
  }

  /**
   * Limpia requests antiguos
   */
  cleanup(): void {
    const now = Date.now();

    this.requests.forEach((timestamps, key) => {
      const recent = timestamps.filter((timestamp) => now - timestamp < this.windowMs);

      if (recent.length === 0) {
        this.requests.delete(key);
      } else {
        this.requests.set(key, recent);
      }
    });
  }
}

// Rate limiters globales
export const loginRateLimiter = new RateLimiter(5, 15 * 60 * 1000); // 5 intentos por 15 min
export const apiRateLimiter = new RateLimiter(30, 60 * 1000); // 30 requests por minuto
export const enrollmentRateLimiter = new RateLimiter(3, 60 * 60 * 1000); // 3 registros por hora

/**
 * CSRF Token Manager
 */
export class CSRFTokenManager {
  private static TOKEN_KEY = 'csrf_token';
  private static token: string | null = null;

  /**
   * Genera un nuevo CSRF token
   */
  static generate(): string {
    const array = new Uint8Array(32);
    crypto.getRandomValues(array);
    const token = Array.from(array, (byte) => byte.toString(16).padStart(2, '0')).join('');

    this.token = token;
    sessionStorage.setItem(this.TOKEN_KEY, token);

    return token;
  }

  /**
   * Obtiene el CSRF token actual
   */
  static getToken(): string {
    if (!this.token) {
      this.token = sessionStorage.getItem(this.TOKEN_KEY);
    }

    if (!this.token) {
      return this.generate();
    }

    return this.token;
  }

  /**
   * Valida un CSRF token
   */
  static validate(token: string): boolean {
    const currentToken = this.getToken();
    return token === currentToken;
  }

  /**
   * Limpia el CSRF token
   */
  static clear(): void {
    this.token = null;
    sessionStorage.removeItem(this.TOKEN_KEY);
  }
}

/**
 * Secure Headers Configuration
 */
export const SECURITY_HEADERS = {
  'Content-Security-Policy':
    "default-src 'self'; " +
    "script-src 'self' 'unsafe-inline' 'unsafe-eval'; " +
    "style-src 'self' 'unsafe-inline'; " +
    "img-src 'self' data: https:; " +
    "font-src 'self' data:; " +
    "connect-src 'self' https://api.example.com; " +
    "media-src 'self' blob:; " +
    "frame-ancestors 'none'; " +
    "base-uri 'self'; " +
    "form-action 'self';",
  'X-Frame-Options': 'DENY',
  'X-Content-Type-Options': 'nosniff',
  'Referrer-Policy': 'strict-origin-when-cross-origin',
  'Permissions-Policy':
    'microphone=(self), ' +
    'camera=(self), ' +
    'geolocation=(), ' +
    'payment=(), ' +
    'usb=(), ' +
    'magnetometer=(), ' +
    'gyroscope=(), ' +
    'accelerometer=()',
};

/**
 * Genera nonce para CSP
 */
export const generateNonce = (): string => {
  const array = new Uint8Array(16);
  crypto.getRandomValues(array);
  return btoa(String.fromCharCode(...array));
};

/**
 * Encrypts data usando Web Crypto API
 */
export const encryptData = async (data: string, key: CryptoKey): Promise<string> => {
  const encoder = new TextEncoder();
  const dataBuffer = encoder.encode(data);

  const iv = crypto.getRandomValues(new Uint8Array(12));
  const encrypted = await crypto.subtle.encrypt(
    {
      name: 'AES-GCM',
      iv: iv,
    },
    key,
    dataBuffer
  );

  // Combinar IV + encrypted data
  const combined = new Uint8Array(iv.length + encrypted.byteLength);
  combined.set(iv);
  combined.set(new Uint8Array(encrypted), iv.length);

  return btoa(String.fromCharCode(...combined));
};

/**
 * Decrypts data usando Web Crypto API
 */
export const decryptData = async (encryptedData: string, key: CryptoKey): Promise<string> => {
  const combined = Uint8Array.from(atob(encryptedData), (c) => c.charCodeAt(0));

  const iv = combined.slice(0, 12);
  const data = combined.slice(12);

  const decrypted = await crypto.subtle.decrypt(
    {
      name: 'AES-GCM',
      iv: iv,
    },
    key,
    data
  );

  const decoder = new TextDecoder();
  return decoder.decode(decrypted);
};

/**
 * Genera una clave de encriptación
 */
export const generateEncryptionKey = async (): Promise<CryptoKey> => {
  return await crypto.subtle.generateKey(
    {
      name: 'AES-GCM',
      length: 256,
    },
    true, // extractable
    ['encrypt', 'decrypt']
  );
};

/**
 * Hash de contraseña usando Web Crypto API
 */
export const hashPassword = async (password: string): Promise<string> => {
  const encoder = new TextEncoder();
  const data = encoder.encode(password);
  const hash = await crypto.subtle.digest('SHA-256', data);
  return Array.from(new Uint8Array(hash))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
};

/**
 * Previene timing attacks comparando strings
 */
export const constantTimeCompare = (a: string, b: string): boolean => {
  if (a.length !== b.length) {
    return false;
  }

  let result = 0;
  for (let i = 0; i < a.length; i++) {
    result |= a.charCodeAt(i) ^ b.charCodeAt(i);
  }

  return result === 0;
};

/**
 * Input sanitization para SQL injection prevention (aunque uses ORM)
 */
export const escapeSqlString = (str: string): string => {
  return str.replace(/[\0\x08\x09\x1a\n\r"'\\%]/g, (char) => {
    switch (char) {
      case '\0':
        return '\\0';
      case '\x08':
        return '\\b';
      case '\x09':
        return '\\t';
      case '\x1a':
        return '\\z';
      case '\n':
        return '\\n';
      case '\r':
        return '\\r';
      case '"':
      case "'":
      case '\\':
      case '%':
        return '\\' + char;
      default:
        return char;
    }
  });
};

/**
 * Verifica si el origen del request es válido
 */
export const isValidOrigin = (origin: string): boolean => {
  const allowedOrigins = [
    'http://localhost:5173',
    'http://localhost:4173',
    'https://voiceauth.example.com', // Cambiar por tu dominio
  ];

  return allowedOrigins.includes(origin);
};

/**
 * Limpia automáticamente rate limiters cada 5 minutos
 */
if (typeof window !== 'undefined') {
  setInterval(
    () => {
      loginRateLimiter.cleanup();
      apiRateLimiter.cleanup();
      enrollmentRateLimiter.cleanup();
    },
    5 * 60 * 1000
  );
}
