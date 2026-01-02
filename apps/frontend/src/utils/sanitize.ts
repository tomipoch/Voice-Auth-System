import DOMPurify from 'dompurify';

/**
 * Configuración de seguridad para DOMPurify
 */
const PURIFY_CONFIG = {
  ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'br', 'span'],
  ALLOWED_ATTR: ['href', 'title', 'target'],
  ALLOW_DATA_ATTR: false,
  ALLOWED_URI_REGEXP:
    /^(?:(?:(?:f|ht)tps?|mailto|tel|callto|sms|cid|xmpp):|[^a-z]|[a-z+.\-]+(?:[^a-z+.\-:]|$))/i,
};

/**
 * Sanitiza HTML para prevenir XSS
 */
export const sanitizeHtml = (dirty: string, config?: Record<string, unknown>): string => {
  const finalConfig = config ? { ...PURIFY_CONFIG, ...config } : PURIFY_CONFIG;
  return String(DOMPurify.sanitize(dirty, finalConfig as never));
};

/**
 * Sanitiza texto plano eliminando cualquier HTML
 */
export const sanitizeText = (text: string): string => {
  return DOMPurify.sanitize(text, { ALLOWED_TAGS: [], ALLOWED_ATTR: [] });
};

/**
 * Sanitiza URL para prevenir javascript: y data: URIs maliciosos
 */
export const sanitizeUrl = (url: string): string => {
  const cleaned = url.trim();

  // Bloquear protocolos peligrosos
  const dangerousProtocols = ['javascript:', 'data:', 'vbscript:', 'file:'];
  const lowerUrl = cleaned.toLowerCase();

  if (dangerousProtocols.some((protocol) => lowerUrl.startsWith(protocol))) {
    return 'about:blank';
  }

  return sanitizeText(cleaned);
};

/**
 * Escapa caracteres HTML especiales
 */
export const escapeHtml = (text: string): string => {
  const map: Record<string, string> = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#x27;',
    '/': '&#x2F;',
  };

  return text.replace(/[&<>"'/]/g, (char) => map[char] ?? char);
};

/**
 * Sanitiza objeto eliminando propiedades potencialmente peligrosas
 */
export const sanitizeObject = <T extends Record<string, unknown>>(obj: T): Partial<T> => {
  const sanitized: Record<string, unknown> = { ...obj };

  Object.keys(sanitized).forEach((key) => {
    const value = sanitized[key];

    // Sanitizar strings
    if (typeof value === 'string') {
      sanitized[key] = sanitizeText(value);
    }

    // Recursivo para objetos anidados
    if (value && typeof value === 'object' && !Array.isArray(value)) {
      sanitized[key] = sanitizeObject(value as Record<string, unknown>);
    }

    // Sanitizar arrays
    if (Array.isArray(value)) {
      sanitized[key] = value.map((item) =>
        typeof item === 'string'
          ? sanitizeText(item)
          : typeof item === 'object'
            ? sanitizeObject(item as Record<string, unknown>)
            : item
      );
    }
  });

  return sanitized as Partial<T>;
};

/**
 * Valida y sanitiza email
 */
export const sanitizeEmail = (email: string): string => {
  const cleaned = email.trim().toLowerCase();
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  if (!emailRegex.test(cleaned)) {
    throw new Error('Invalid email format');
  }

  return sanitizeText(cleaned);
};

/**
 * Sanitiza nombre de archivo
 */
export const sanitizeFilename = (filename: string): string => {
  return filename
    .replace(/[^a-zA-Z0-9._-]/g, '_') // Reemplazar caracteres no seguros
    .replace(/_{2,}/g, '_') // Eliminar guiones bajos consecutivos
    .slice(0, 255); // Limitar longitud
};

/**
 * Sanitiza input de búsqueda
 */
export const sanitizeSearchQuery = (query: string): string => {
  return sanitizeText(query)
    .replace(/[<>]/g, '') // Eliminar brackets
    .trim()
    .slice(0, 500); // Limitar longitud
};

/**
 * Valida y sanitiza número de teléfono
 */
export const sanitizePhoneNumber = (phone: string): string => {
  return phone.replace(/[^0-9+\-() ]/g, '').trim();
};

/**
 * Previene ataques de prototype pollution
 */
export const isPrototypePolluted = (key: string): boolean => {
  const dangerousKeys = ['__proto__', 'constructor', 'prototype'];
  return dangerousKeys.includes(key);
};

/**
 * Crea un objeto seguro sin prototype pollution
 */
export const createSafeObject = <T extends Record<string, unknown>>(obj: T): T => {
  const safe = Object.create(null);

  Object.keys(obj).forEach((key) => {
    if (!isPrototypePolluted(key)) {
      safe[key] = obj[key];
    }
  });

  return safe;
};

/**
 * Hook de React para sanitizar contenido antes de renderizar
 */
export const useSanitizedHtml = (html: string, config?: Record<string, unknown>) => {
  return {
    __html: sanitizeHtml(html, config),
  };
};
