# TypeScript Migration Guide

## 📘 Overview

Este documento describe la migración del proyecto VoiceAuth de JavaScript a TypeScript, incluyendo configuración, tipos, y mejores prácticas.

## 🎯 Beneficios de TypeScript

### Type Safety

- ✅ Detección de errores en tiempo de compilación
- ✅ Autocompletado inteligente en el IDE
- ✅ Refactorización segura
- ✅ Documentación implícita del código

### Developer Experience

- ✅ IntelliSense mejorado
- ✅ Navegación de código más fácil
- ✅ Mejor mantenibilidad
- ✅ Menor cantidad de bugs en producción

## 📦 Dependencias Instaladas

```json
{
  "devDependencies": {
    "typescript": "^5.x",
    "@types/react": "^18.x",
    "@types/react-dom": "^18.x",
    "@types/node": "^20.x",
    "@types/dompurify": "^3.x",
    "@typescript-eslint/eslint-plugin": "^6.x",
    "@typescript-eslint/parser": "^6.x"
  },
  "dependencies": {
    "zod": "^3.x",
    "dompurify": "^3.x"
  }
}
```

## ⚙️ Configuración

### tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "jsx": "react-jsx",
    "module": "ESNext",
    "moduleResolution": "bundler",

    // Strict Type Checking
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "strictBindCallApply": true,
    "strictPropertyInitialization": true,
    "noImplicitThis": true,
    "alwaysStrict": true,

    // Additional Checks
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,

    // Path Aliases
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"],
      "@components/*": ["./src/components/*"],
      "@pages/*": ["./src/pages/*"],
      "@hooks/*": ["./src/hooks/*"],
      "@services/*": ["./src/services/*"],
      "@utils/*": ["./src/utils/*"],
      "@types/*": ["./src/types/*"],
      "@context/*": ["./src/context/*"],
      "@config/*": ["./src/config/*"]
    }
  }
}
```

### Scripts package.json

```json
{
  "scripts": {
    "typecheck": "tsc --noEmit",
    "build": "tsc && vite build",
    "dev": "vite"
  }
}
```

## 📁 Estructura de Tipos

```
src/
├── types/
│   ├── index.ts          # Tipos principales exportados
│   ├── auth.types.ts     # Tipos de autenticación
│   ├── api.types.ts      # Tipos de API
│   └── components.types.ts  # Props de componentes
└── vite-env.d.ts         # Tipos de environment
```

## 🎨 Tipos Principales

### User & Auth

```typescript
export interface User {
  id: string;
  email: string;
  username: string;
  fullName: string;
  role: UserRole;
  isVerified: boolean;
  voiceProfile?: VoiceProfile;
  createdAt: string;
  updatedAt: string;
}

export enum UserRole {
  USER = 'user',
  ADMIN = 'admin',
  SUPER_ADMIN = 'super_admin',
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
}

export interface LoginCredentials {
  email: string;
  password: string;
  rememberMe?: boolean;
}
```

### API Responses

```typescript
export interface ApiResponse<T = unknown> {
  success: boolean;
  data: T;
  message?: string;
}

export interface ApiError {
  success: false;
  message: string;
  errors?: Record<string, string[]>;
  statusCode: number;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}
```

### Component Props

```typescript
export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}
```

### Context Types

```typescript
export interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<void>;
  updateUser: (user: Partial<User>) => void;
}
```

## 🔧 Utility Types

```typescript
// Nullable & Optional
export type Nullable<T> = T | null;
export type Optional<T> = T | undefined;
export type Maybe<T> = T | null | undefined;

// Deep Partial
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

// Require At Least One
export type RequireAtLeastOne<T, Keys extends keyof T = keyof T> = Pick<T, Exclude<keyof T, Keys>> &
  {
    [K in Keys]-?: Required<Pick<T, K>> & Partial<Pick<T, Exclude<Keys, K>>>;
  }[Keys];

// With Required
export type WithRequired<T, K extends keyof T> = T & { [P in K]-?: T[P] };
```

## 📝 Migración de Componentes

### Antes (JavaScript)

```jsx
// Button.jsx
export const Button = ({ children, variant, onClick, ...props }) => {
  return (
    <button className={`btn btn-${variant}`} onClick={onClick} {...props}>
      {children}
    </button>
  );
};
```

### Después (TypeScript)

```tsx
// Button.tsx
import { ButtonProps } from '@types';

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  onClick,
  ...props
}) => {
  return (
    <button className={`btn btn-${variant}`} onClick={onClick} {...props}>
      {children}
    </button>
  );
};
```

## 🎣 Migración de Hooks

### Antes (JavaScript)

```javascript
// useAuth.js
export const useAuth = () => {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const login = async (credentials) => {
    // ...
  };

  return { user, isLoading, login };
};
```

### Después (TypeScript)

```typescript
// useAuth.ts
import { User, LoginCredentials, UseAuthReturn } from '@types';

export const useAuth = (): UseAuthReturn => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const login = async (credentials: LoginCredentials): Promise<void> => {
    // ...
  };

  return { user, isLoading, login };
};
```

## 🔐 Migración de Services

### API Service con TypeScript

```typescript
// api.ts
import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import { ApiResponse, ApiError } from '@types';

class ApiService {
  private client: AxiosInstance;

  constructor(baseURL: string) {
    this.client = axios.create({ baseURL });
  }

  async get<T>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    try {
      const response = await this.client.get<ApiResponse<T>>(url, config);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async post<T, D = unknown>(
    url: string,
    data?: D,
    config?: AxiosRequestConfig
  ): Promise<ApiResponse<T>> {
    try {
      const response = await this.client.post<ApiResponse<T>>(url, data, config);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  private handleError(error: unknown): ApiError {
    // Error handling logic
  }
}

export const apiService = new ApiService(import.meta.env.VITE_API_URL);
```

## 🛡️ Type Guards

```typescript
// Type guards para validación en runtime
export const isUser = (value: unknown): value is User => {
  return (
    typeof value === 'object' &&
    value !== null &&
    'id' in value &&
    'email' in value &&
    'role' in value
  );
};

export const isApiResponse = <T>(value: unknown): value is ApiResponse<T> => {
  return typeof value === 'object' && value !== null && 'success' in value && 'data' in value;
};
```

## 🎯 Best Practices

### DO ✅

```typescript
// 1. Usar interfaces para props y tipos públicos
interface UserProps {
  user: User;
  onEdit: (id: string) => void;
}

// 2. Usar type para unions y intersections
type Status = 'idle' | 'loading' | 'success' | 'error';
type WithTimestamp = User & { timestamp: number };

// 3. Usar generics para reutilización
function useState<T>(initialValue: T): [T, (value: T) => void] {
  // ...
}

// 4. Usar const assertions
const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  DASHBOARD: '/dashboard',
} as const;

// 5. Tipar event handlers
const handleClick = (event: React.MouseEvent<HTMLButtonElement>): void => {
  // ...
};

// 6. Usar utility types de React
const Component: React.FC<PropsWithChildren<MyProps>> = ({ children, ...props }) => {
  // ...
};
```

### DON'T ❌

```typescript
// 1. Evitar 'any'
const data: any = {}; // ❌

// 2. No usar type assertions innecesarias
const value = data as string; // ❌ solo si realmente lo necesitas

// 3. No duplicar tipos
interface User {
  id: string;
}
interface UserData {
  id: string;
} // ❌ usa User

// 4. No ignorar errores de tipo
// @ts-ignore  // ❌
const result = dangerousOperation();

// 5. No usar unknown sin validación
const value: unknown = getUnknownValue();
console.log(value.toString()); // ❌ validar primero
```

## 📊 Validación con Zod

```typescript
import { z } from 'zod';

// Schema definition
export const loginSchema = z.object({
  email: z.string().email('Email inválido'),
  password: z.string().min(8, 'Mínimo 8 caracteres'),
});

// Type inference
export type LoginFormData = z.infer<typeof loginSchema>;

// Validation
const validateLogin = (data: unknown) => {
  const result = loginSchema.safeParse(data);

  if (!result.success) {
    return { success: false, errors: result.error };
  }

  return { success: true, data: result.data };
};
```

## 🔍 Debugging Tips

### VSCode Settings

```json
{
  "typescript.tsdk": "node_modules/typescript/lib",
  "typescript.enablePromptUseWorkspaceTsdk": true,
  "typescript.suggest.autoImports": true,
  "typescript.updateImportsOnFileMove.enabled": "always"
}
```

### Useful Commands

```bash
# Type check sin build
npm run typecheck

# Ver errores específicos
tsc --noEmit --pretty

# Generar declaraciones de tipo
tsc --declaration --emitDeclarationOnly --outDir dist/types
```

## 📚 Resources

- [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)
- [React TypeScript Cheatsheet](https://react-typescript-cheatsheet.netlify.app/)
- [Zod Documentation](https://zod.dev/)
- [Type Challenges](https://github.com/type-challenges/type-challenges)

## 🚀 Migration Checklist

- [x] Instalar TypeScript y tipos
- [x] Crear tsconfig.json
- [x] Definir tipos principales en src/types/
- [x] Configurar path aliases
- [ ] Migrar archivos de configuración (.js → .ts)
- [ ] Migrar services y utilities
- [ ] Migrar hooks
- [ ] Migrar contexts
- [ ] Migrar componentes (.jsx → .tsx)
- [ ] Actualizar imports
- [ ] Correr typecheck y fix errores
- [ ] Actualizar tests

---

**TypeScript para código más seguro y mantenible** 🎯
