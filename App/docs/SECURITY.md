# Security Guide

## 🔐 Overview

Este documento describe las medidas de seguridad implementadas en VoiceAuth para proteger contra vulnerabilidades comunes y garantizar la privacidad de los datos de los usuarios.

## 🛡️ Security Layers

### 1. Input Sanitization

### 2. XSS Protection

### 3. CSRF Protection

### 4. Rate Limiting

### 5. Secure Storage

### 6. Content Security Policy

### 7. Authentication Security

## 🧹 Input Sanitization

### DOMPurify Integration

```typescript
import { sanitizeHtml, sanitizeText, sanitizeUrl } from '@/utils/sanitize';

// Sanitizar HTML
const cleanHtml = sanitizeHtml('<script>alert("xss")</script><p>Safe</p>');
// Result: <p>Safe</p>

// Sanitizar texto plano
const cleanText = sanitizeText('<b>Bold</b>');
// Result: Bold

// Sanitizar URL
const cleanUrl = sanitizeUrl('javascript:alert("xss")');
// Result: about:blank
```

### Object Sanitization

```typescript
import { sanitizeObject, createSafeObject } from '@/utils/sanitize';

// Sanitizar objeto completo
const userData = {
  name: '<script>alert()</script>John',
  email: 'john@example.com',
  bio: '<b>Developer</b>',
};

const clean = sanitizeObject(userData);
// Todos los strings sanitizados recursivamente

// Prevenir prototype pollution
const safe = createSafeObject({
  __proto__: { isAdmin: true }, // Bloqueado
  name: 'John',
});
```

### File & Email Sanitization

```typescript
import { sanitizeFilename, sanitizeEmail, sanitizeSearchQuery } from '@/utils/sanitize';

// Nombres de archivo seguros
const filename = sanitizeFilename('../../etc/passwd');
// Result: .._.._.._etc_passwd

// Email validation + sanitization
const email = sanitizeEmail('  JohN@Example.COM  ');
// Result: john@example.com

// Search queries
const query = sanitizeSearchQuery('<script>alert()</script>');
// Result: scriptalert()script
```

## 🚫 XSS Protection

### Content Rendering

```tsx
import { useSanitizedHtml } from '@/utils/sanitize';

// En componentes React
const UserBio: React.FC<{ bio: string }> = ({ bio }) => {
  const sanitized = useSanitizedHtml(bio);

  return <div dangerouslySetInnerHTML={sanitized} />;
};
```

### Event Handler Safety

```tsx
// ❌ NUNCA hacer esto
<div onClick={eval(userInput)} />;

// ✅ Siempre usar funciones definidas
const handleClick = (e: React.MouseEvent) => {
  // Safe event handling
};

<div onClick={handleClick} />;
```

### Attribute Sanitization

```tsx
// ❌ PELIGROSO
<a href={userProvidedUrl}>Link</a>;

// ✅ SEGURO
import { sanitizeUrl } from '@/utils/sanitize';

<a href={sanitizeUrl(userProvidedUrl)}>Link</a>;
```

## 🔒 CSRF Protection

### Token Management

```typescript
import { CSRFTokenManager } from '@/utils/security';

// Generar token al iniciar sesión
const token = CSRFTokenManager.generate();

// Incluir en requests
axios.post('/api/action', data, {
  headers: {
    'X-CSRF-Token': CSRFTokenManager.getToken(),
  },
});

// Validar en servidor (ejemplo)
const isValid = CSRFTokenManager.validate(requestToken);
```

### Form Protection

```tsx
const SecureForm: React.FC = () => {
  const [csrfToken] = useState(() => CSRFTokenManager.getToken());

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    await fetch('/api/submit', {
      method: 'POST',
      headers: {
        'X-CSRF-Token': csrfToken,
      },
      body: formData,
    });
  };

  return <form onSubmit={handleSubmit}>...</form>;
};
```

## ⏱️ Rate Limiting

### Login Protection

```typescript
import { loginRateLimiter } from '@/utils/security';

const handleLogin = async (email: string, password: string) => {
  const key = `login_${email}`;

  if (!loginRateLimiter.canMakeRequest(key)) {
    const waitTime = loginRateLimiter.getWaitTime(key);
    throw new Error(`Demasiados intentos. Espera ${waitTime / 1000}s`);
  }

  // Proceder con login
  await login(email, password);
};
```

### API Rate Limiting

```typescript
import { apiRateLimiter } from '@/utils/security';

// En interceptor de Axios
axios.interceptors.request.use((config) => {
  const key = `api_${config.url}`;

  if (!apiRateLimiter.canMakeRequest(key)) {
    const waitTime = apiRateLimiter.getWaitTime(key);
    return Promise.reject(new Error(`Rate limit exceeded. Wait ${waitTime / 1000}s`));
  }

  return config;
});
```

### Custom Rate Limiters

```typescript
import { RateLimiter } from '@/utils/security';

// 10 requests por 5 minutos
const customLimiter = new RateLimiter(10, 5 * 60 * 1000);

if (customLimiter.canMakeRequest('user_123')) {
  // Permitir request
} else {
  // Bloquear
}
```

## 🗄️ Secure Storage

### Encrypted Storage

```typescript
import { generateEncryptionKey, encryptData, decryptData } from '@/utils/security';

// Generar clave (una vez)
const key = await generateEncryptionKey();

// Encriptar datos sensibles
const encrypted = await encryptData(JSON.stringify(sensitiveData), key);
localStorage.setItem('secure_data', encrypted);

// Desencriptar
const encrypted = localStorage.getItem('secure_data');
const decrypted = await decryptData(encrypted, key);
const data = JSON.parse(decrypted);
```

### Token Storage

```typescript
// ❌ NUNCA en localStorage
localStorage.setItem('accessToken', token);

// ✅ Usar httpOnly cookies (configurar en backend)
// O sessionStorage para tokens de corta duración
sessionStorage.setItem('tempToken', token);

// Limpiar al cerrar sesión
const clearTokens = () => {
  sessionStorage.clear();
  CSRFTokenManager.clear();
};
```

### Sensitive Data Handling

```typescript
// Storage service con expiración
class SecureStorage {
  set(key: string, value: unknown, expiresIn?: number) {
    const item = {
      value,
      expires: expiresIn ? Date.now() + expiresIn : null,
    };

    sessionStorage.setItem(key, JSON.stringify(item));
  }

  get(key: string) {
    const item = sessionStorage.getItem(key);
    if (!item) return null;

    const parsed = JSON.parse(item);

    // Check expiration
    if (parsed.expires && Date.now() > parsed.expires) {
      sessionStorage.removeItem(key);
      return null;
    }

    return parsed.value;
  }
}
```

## 🛡️ Content Security Policy

### Headers Configuration

```typescript
import { SECURITY_HEADERS, generateNonce } from '@/utils/security';

// En index.html o configurar en servidor
const nonce = generateNonce();

// CSP Header
const csp = `
  default-src 'self';
  script-src 'self' 'nonce-${nonce}';
  style-src 'self' 'unsafe-inline';
  img-src 'self' data: https:;
  font-src 'self' data:;
  connect-src 'self' https://api.example.com;
  media-src 'self' blob:;
  frame-ancestors 'none';
`;
```

### Meta Tags

```html
<!-- index.html -->
<head>
  <meta http-equiv="Content-Security-Policy" content="default-src 'self'" />
  <meta http-equiv="X-Frame-Options" content="DENY" />
  <meta http-equiv="X-Content-Type-Options" content="nosniff" />
  <meta name="referrer" content="strict-origin-when-cross-origin" />
</head>
```

### Vite Configuration

```typescript
// vite.config.ts
export default defineConfig({
  server: {
    headers: {
      'Content-Security-Policy': SECURITY_HEADERS['Content-Security-Policy'],
      'X-Frame-Options': SECURITY_HEADERS['X-Frame-Options'],
      'X-Content-Type-Options': SECURITY_HEADERS['X-Content-Type-Options'],
      'Referrer-Policy': SECURITY_HEADERS['Referrer-Policy'],
      'Permissions-Policy': SECURITY_HEADERS['Permissions-Policy'],
    },
  },
});
```

## 🔑 Authentication Security

### Password Hashing

```typescript
import { hashPassword, constantTimeCompare } from '@/utils/security';

// Hash antes de enviar (adicional al hash del backend)
const hashedPassword = await hashPassword(password);

// Comparación segura contra timing attacks
const isMatch = constantTimeCompare(hash1, hash2);
```

### Token Refresh Strategy

```typescript
// Refresh automático antes de expiración
const setupTokenRefresh = (expiresIn: number) => {
  // Refresh 5 minutos antes de expirar
  const refreshTime = (expiresIn - 5 * 60) * 1000;

  setTimeout(async () => {
    try {
      await refreshAccessToken();
    } catch (error) {
      // Logout si falla
      await logout();
    }
  }, refreshTime);
};
```

### Session Management

```typescript
// Detectar múltiples tabs
window.addEventListener('storage', (e) => {
  if (e.key === 'logout') {
    // Logout en todas las tabs
    window.location.href = '/login';
  }
});

// Logout en todas las tabs
const logoutAllTabs = () => {
  localStorage.setItem('logout', Date.now().toString());
  localStorage.removeItem('logout');
};
```

## 📝 Input Validation

### Zod Schemas

```typescript
import { z } from 'zod';

// Validación estricta
const userSchema = z.object({
  email: z.string().email().max(255),
  username: z
    .string()
    .min(3)
    .max(20)
    .regex(/^[a-zA-Z0-9_]+$/),
  password: z
    .string()
    .min(8)
    .regex(/[A-Z]/)
    .regex(/[a-z]/)
    .regex(/[0-9]/)
    .regex(/[^A-Za-z0-9]/),
});

// Validar antes de enviar
const validateUser = (data: unknown) => {
  return userSchema.safeParse(data);
};
```

### Form Validation

```tsx
import { loginSchema } from '@/utils/validation';

const LoginForm: React.FC = () => {
  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleSubmit = async (data: unknown) => {
    const result = loginSchema.safeParse(data);

    if (!result.success) {
      setErrors(getValidationErrors(result.error));
      return;
    }

    // Datos válidos
    await login(result.data);
  };

  return <form>...</form>;
};
```

## 🚨 Error Handling

### Secure Error Messages

```typescript
// ❌ NUNCA exponer detalles internos
throw new Error(`Database error: ${dbError.message}`);

// ✅ Mensajes genéricos al usuario
throw new Error('An error occurred. Please try again.');

// Log completo solo en servidor
console.error('[Internal]', fullError);
```

### API Error Handling

```typescript
const handleApiError = (error: unknown): string => {
  // No exponer stack traces
  if (axios.isAxiosError(error)) {
    const message = error.response?.data?.message;

    // Sanitizar mensaje del servidor
    return sanitizeText(message || 'Request failed');
  }

  return 'An unexpected error occurred';
};
```

## 🔍 Security Auditing

### Logging Security Events

```typescript
const securityLogger = {
  logFailedLogin: (email: string, ip: string) => {
    console.warn(`[SECURITY] Failed login: ${email} from ${ip}`);
    // Enviar a servicio de monitoring
  },

  logRateLimitExceeded: (key: string) => {
    console.warn(`[SECURITY] Rate limit exceeded: ${key}`);
  },

  logSuspiciousActivity: (userId: string, action: string) => {
    console.error(`[SECURITY] Suspicious: User ${userId} - ${action}`);
  },
};
```

### Monitoring

```typescript
// Detectar intentos de XSS
window.addEventListener('error', (event) => {
  if (event.message.includes('script')) {
    securityLogger.logSuspiciousActivity('unknown', 'Possible XSS attempt');
  }
});

// Detectar cambios sospechosos en localStorage
const originalSetItem = localStorage.setItem;
localStorage.setItem = function (key, value) {
  if (key === '__proto__' || key === 'constructor') {
    securityLogger.logSuspiciousActivity('unknown', 'Prototype pollution attempt');
    return;
  }
  originalSetItem.apply(this, [key, value]);
};
```

## 📋 Security Checklist

### Development

- [x] Sanitizar todos los inputs del usuario
- [x] Validar datos con schemas (Zod)
- [x] Implementar rate limiting
- [x] Usar CSRF tokens
- [x] Configurar CSP headers
- [x] Encriptar datos sensibles
- [x] No exponer secrets en código
- [x] Usar HTTPS en producción
- [x] Validar tokens en cada request
- [x] Implementar logout en todas las tabs

### Testing

- [ ] Probar XSS en todos los inputs
- [ ] Probar CSRF en formularios
- [ ] Verificar rate limiting
- [ ] Probar prototype pollution
- [ ] Revisar CSP con browser tools
- [ ] Audit con npm audit / snyk
- [ ] Penetration testing
- [ ] OWASP Top 10 compliance

### Deployment

- [ ] Environment variables seguras
- [ ] HTTPS obligatorio
- [ ] Headers de seguridad configurados
- [ ] Tokens en httpOnly cookies
- [ ] Logs de seguridad activos
- [ ] Monitoring de anomalías
- [ ] Backup de datos encriptados
- [ ] Plan de respuesta a incidentes

## 🛠️ Tools & Resources

### Security Tools

```bash
# Audit de dependencias
npm audit
npm audit fix

# Snyk para vulnerabilidades
npx snyk test

# Lighthouse security audit
npx lighthouse https://your-app.com --only-categories=security

# OWASP ZAP
# https://www.zaproxy.org/
```

### Browser Extensions

- **OWASP ZAP**: Penetration testing
- **Burp Suite**: Security testing
- **CSP Evaluator**: Validate CSP policies
- **SecurityHeaders.com**: Check security headers

## 📚 Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [MDN Web Security](https://developer.mozilla.org/en-US/docs/Web/Security)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [Web Crypto API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Crypto_API)

## 🚀 Best Practices Summary

### Input Handling

- ✅ Sanitize all user inputs
- ✅ Validate with strict schemas
- ✅ Escape HTML entities
- ✅ Whitelist allowed values

### Authentication

- ✅ Use strong password policies
- ✅ Implement 2FA when possible
- ✅ Rate limit login attempts
- ✅ Use httpOnly cookies for tokens
- ✅ Implement proper session management

### Data Protection

- ✅ Encrypt sensitive data
- ✅ Use HTTPS everywhere
- ✅ Implement CSP
- ✅ Protect against CSRF
- ✅ Prevent XSS attacks

### Error Handling

- ✅ Show generic error messages
- ✅ Log detailed errors server-side
- ✅ Never expose stack traces
- ✅ Handle errors gracefully

---

**Seguridad como prioridad** 🔐
