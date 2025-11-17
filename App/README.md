# 🎙️ VoiceAuth

Sistema de autenticación biométrica por voz con interfaz web moderna y segura.

![React](https://img.shields.io/badge/React-19.2.0-61DAFB?logo=react)
![Vite](https://img.shields.io/badge/Vite-7.2.2-646CFF?logo=vite)
![Tailwind](https://img.shields.io/badge/Tailwind-4.1.17-38B2AC?logo=tailwind-css)
![Tests](https://img.shields.io/badge/Tests-14%20passing-success)

## 📋 Tabla de Contenidos

- [Características](#-características)
- [Tecnologías](#️-tecnologías)
- [Requisitos](#-requisitos)
- [Instalación](#-instalación)
- [Configuración](#️-configuración)
- [Uso](#-uso)
- [Testing](#-testing)
- [Arquitectura](#️-arquitectura)
- [Scripts Disponibles](#-scripts-disponibles)
- [Documentación](#-documentación)
- [Contribuir](#-contribuir)

## ✨ Características

### 🔐 Autenticación Biométrica

- **Registro por voz** con análisis de calidad de audio
- **Verificación biométrica** en tiempo real
- **Multi-rol** (Usuario, Administrador, Super Admin)
- Gestión segura de tokens y sesiones

### 🎨 Interfaz Moderna

- **Dark Mode** con persistencia en localStorage
- Diseño **responsive** y accesible
- Componentes reutilizables con **Tailwind CSS**
- Efectos glass morphism y gradientes

### 📊 Panel de Administración

- Gestión de usuarios y permisos
- Métricas del sistema en tiempo real
- Dashboard con estadísticas

### 🛠️ Calidad de Código

- **ESLint** + **Prettier** para formato consistente
- **Tests** unitarios y de integración con Vitest
- Configuración de ambientes (development, staging, production)
- TypeScript-ready con soporte de path aliases

## 🛠️ Tecnologías

### Core

- **React 19.2.0** - Framework UI
- **Vite 7.2.2** - Build tool y dev server
- **React Router 7.9.6** - Enrutamiento
- **Axios 1.7.9** - Cliente HTTP

### Styling

- **Tailwind CSS 4.1.17** - Framework CSS utility-first
- **Lucide React** - Iconos modernos
- **clsx** - Utilidad para clases condicionales

### Testing

- **Vitest 4.0.9** - Framework de testing
- **React Testing Library** - Testing de componentes
- **jsdom** - Simulación de DOM

### Calidad de Código

- **ESLint 9.39.1** - Linter
- **Prettier 3.6.2** - Formatter
- **eslint-plugin-react-hooks** - Reglas para hooks
- **eslint-plugin-react-refresh** - Fast Refresh

## 📦 Requisitos

- **Node.js** >= 18.0.0
- **npm** >= 9.0.0 o **yarn** >= 1.22.0

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/tomipoch/Proyecto.git
cd Proyecto/App
```

### 2. Instalar dependencias

```bash
npm install
```

### 3. Crear archivo de configuración

Copia el archivo de ejemplo de variables de entorno:

```bash
cp .env.example .env
```

### 4. Configurar variables de entorno

Edita `.env` con tus configuraciones:

```env
# API Configuration
VITE_API_BASE_URL=http://localhost:3000/api
VITE_API_TIMEOUT=30000

# Environment
VITE_ENVIRONMENT=development

# Features
VITE_ENABLE_MOCK_API=true
VITE_ENABLE_CONSOLE_LOGS=true
VITE_ENABLE_ANALYTICS=false

# Auth
VITE_TOKEN_REFRESH_ENABLED=true
VITE_TOKEN_REFRESH_INTERVAL=300000
```

## ⚙️ Configuración

### Ambientes Disponibles

El proyecto soporta tres ambientes:

#### Development

```bash
npm run dev
```

- API Mock habilitada
- Logs de consola activados
- Hot Module Replacement (HMR)

#### Staging

```bash
npm run start:staging
```

- API real en servidor de staging
- Logs limitados
- Build optimizado

#### Production

```bash
npm run build:prod
npm run preview:prod
```

- API de producción
- Sin logs
- Bundle optimizado y minificado

### Configuración de Path Aliases

El proyecto usa `@` como alias para `src/`:

```javascript
// Antes
import Button from '../../../components/ui/Button';

// Después
import Button from '@/components/ui/Button';
```

## 💻 Uso

### Iniciar servidor de desarrollo

```bash
npm run dev
```

La aplicación estará disponible en `http://localhost:5173`

### Usuarios de prueba (Mock API)

```javascript
// Usuario normal
email: user@example.com
password: user123

// Administrador
email: admin@example.com
password: admin123

// Super Admin
email: superadmin@example.com
password: superadmin123
```

### Flujo de Registro

1. Navegar a `/register`
2. Completar información personal
3. Grabar muestras de voz (3 requeridas)
4. Sistema valida calidad de audio
5. Registro completado

### Flujo de Verificación

1. Login con credenciales
2. Navegar a `/verification`
3. Grabar voz para verificación
4. Sistema compara con muestras registradas
5. Acceso concedido/denegado

## 🧪 Testing

### Ejecutar tests

```bash
# Todos los tests
npm test

# Mode watch (desarrollo)
npm run test:watch

# UI interactiva
npm run test:ui

# Con cobertura
npm run test:coverage
```

### Estructura de tests

```
src/
├── components/
│   └── ui/
│       └── __tests__/
│           ├── Button.test.jsx
│           └── Card.test.jsx
└── test/
    ├── setup.js
    └── __tests__/
        ├── auth.test.jsx
        └── storage.test.js
```

Ver [TESTING.md](./TESTING.md) para guía completa.

## 🏗️ Arquitectura

### Estructura del Proyecto

```
App/
├── public/              # Assets estáticos
├── src/
│   ├── assets/         # Imágenes, fonts
│   ├── components/     # Componentes React
│   │   ├── admin/     # Componentes de admin
│   │   ├── auth/      # Login, Register
│   │   ├── enrollment/# Registro de voz
│   │   ├── ui/        # Componentes reutilizables
│   │   └── verification/
│   ├── config/        # Configuración
│   │   └── environment.js
│   ├── context/       # React Contexts
│   │   ├── AuthContext.jsx
│   │   ├── ThemeContext.jsx
│   │   └── theme.js
│   ├── hooks/         # Custom hooks
│   ├── pages/         # Páginas/Vistas
│   ├── services/      # Servicios API
│   │   ├── api.js
│   │   ├── apiServices.js
│   │   ├── mockApi.js
│   │   └── storage.js
│   ├── test/          # Setup de testing
│   ├── utils/         # Utilidades
│   ├── App.jsx        # Componente principal
│   └── main.jsx       # Entry point
├── .env.example       # Variables de entorno
├── .prettierrc        # Configuración Prettier
├── eslint.config.js   # Configuración ESLint
├── package.json
├── tailwind.config.js # Configuración Tailwind
└── vite.config.js     # Configuración Vite
```

### Patrones de Diseño

#### 1. Context API para Estado Global

```javascript
// AuthContext - Gestión de autenticación
// ThemeContext - Dark mode
// SettingsModalContext - Modales
```

#### 2. Custom Hooks

```javascript
useAuth(); // Autenticación
useTheme(); // Tema
useAudioRecording(); // Grabación de voz
useDashboardStats(); // Estadísticas
```

#### 3. Service Layer

```javascript
api.js; // Cliente HTTP base
apiServices.js; // Endpoints específicos
mockApi.js; // API simulada para desarrollo
storage.js; // Abstracción de localStorage
```

#### 4. Componentes Atómicos

```
Atoms:    Button, Input, Card
Molecules: AudioRecorder, StatusIndicator
Organisms: EnrollmentWizard, VoiceVerification
Templates: MainLayout, Sidebar
Pages:    LoginPage, DashboardPage
```

### Flujo de Datos

```
User Action → Component → Custom Hook → Service → API
                ↓                          ↓
              Context ← Update State ← Response
                ↓
           Re-render
```

## 📜 Scripts Disponibles

### Desarrollo

```bash
npm run dev              # Inicia dev server
npm run dev:local        # Dev con config local
npm run dev:watch        # Dev con HMR
npm run dev:network      # Expone en red local
```

### Build

```bash
npm run build            # Build producción
npm run build:dev        # Build development
npm run build:staging    # Build staging
npm run build:analyze    # Analiza bundle size
```

### Preview

```bash
npm run preview          # Preview del build
npm run preview:dev      # Preview development
npm run preview:staging  # Preview staging
npm run preview:prod     # Preview production
```

### Calidad de Código

```bash
npm run lint             # Ejecuta ESLint
npm run lint:fix         # Fix automático
npm run format           # Formatea código
npm run format:check     # Verifica formato
```

### Testing

```bash
npm test                 # Ejecuta tests
npm run test:watch       # Mode watch
npm run test:ui          # UI interactiva
npm run test:coverage    # Genera reporte
```

### Utilidades

```bash
npm run clean            # Limpia cache y dist
npm start                # Alias de npm run dev
```

## 📚 Documentación

### Guías Técnicas

- [**TESTING.md**](./TESTING.md) - Guía completa de testing con Vitest
- [**CODE_FORMAT.md**](./CODE_FORMAT.md) - Estándares de formato con Prettier
- [**ENVIRONMENTS.md**](./ENVIRONMENTS.md) - Configuración de ambientes
- [**GIT_HOOKS.md**](./GIT_HOOKS.md) - Git hooks con Husky y lint-staged
- [**CI_CD.md**](./CI_CD.md) - Pipeline de CI/CD con GitHub Actions

### Documentación del Sistema

- [**LOGIN_SYSTEM.md**](./LOGIN_SYSTEM.md) - Sistema de autenticación
- [**DARK_MODE_IMPLEMENTATION.md**](./DARK_MODE_IMPLEMENTATION.md) - Implementación de dark mode
- [**PERFORMANCE.md**](./PERFORMANCE.md) - Optimización y performance
- [**ACCESSIBILITY.md**](./ACCESSIBILITY.md) - Guía de accesibilidad
- [**TYPESCRIPT.md**](./TYPESCRIPT.md) - Migración a TypeScript
- [**SECURITY.md**](./SECURITY.md) - Guía de seguridad

### Contribución

- [**CONTRIBUTING.md**](./CONTRIBUTING.md) - Guía para contribuir
- [**CODE_OF_CONDUCT.md**](./CODE_OF_CONDUCT.md) - Código de conducta
- [**CHANGELOG.md**](./CHANGELOG.md) - Historial de cambios
- [**LICENSE**](./LICENSE) - Licencia MIT

## 🤝 Contribuir

### Setup para desarrollo

1. Fork el proyecto
2. Crea tu rama: `git checkout -b feature/nueva-caracteristica`
3. Instala dependencias: `npm install`
4. Realiza cambios
5. Ejecuta tests: `npm test`
6. Ejecuta linter: `npm run lint:fix`
7. Formatea código: `npm run format`
8. Commit: `git commit -m 'Add: nueva característica'`
9. Push: `git push origin feature/nueva-caracteristica`
10. Abre un Pull Request

### Convenciones de Commits

```
feat: Nueva característica
fix: Corrección de bug
docs: Cambios en documentación
style: Formato, punto y coma, etc
refactor: Refactorización de código
test: Tests
chore: Tareas de mantenimiento
```

### Code Review Checklist

- [ ] Tests pasan (`npm test`)
- [ ] Linter pasa (`npm run lint`)
- [ ] Código formateado (`npm run format`)
- [ ] Sin console.logs innecesarios
- [ ] Documentación actualizada
- [ ] Build exitoso (`npm run build`)

## 🔒 Seguridad

- Tokens JWT con refresh automático
- Sanitización de inputs
- Validación en cliente y servidor
- Headers de seguridad (CORS, CSP)
- Almacenamiento seguro en localStorage con prefijos

### Reportar Vulnerabilidades

Para reportar vulnerabilidades de seguridad, contacta a través de issues privados en GitHub.

## 📊 Métricas del Proyecto

- **Componentes**: 25+
- **Tests**: 14 (100% passing)
- **Bundle Size**: ~127KB CSS (optimizado)
- **Build Time**: <500ms
- **Lighthouse Score**: 95+ (Performance)

## 📝 Changelog

Ver [CHANGELOG.md](./CHANGELOG.md) para historial de cambios.

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver [LICENSE](./LICENSE) para más detalles.

## 👥 Autores

- **Tomás Ipinza** - [@tomipoch](https://github.com/tomipoch)

## 🙏 Agradecimientos

- Equipo de React por el framework
- Comunidad de Tailwind CSS
- Contribuidores de Vite
- Testing Library team

## 📞 Soporte

- 📧 Email: [tu-email@ejemplo.com]
- 🐛 Issues: [GitHub Issues](https://github.com/tomipoch/Proyecto/issues)
- 💬 Discusiones: [GitHub Discussions](https://github.com/tomipoch/Proyecto/discussions)

---

**Desarrollado con ❤️ usando React + Vite + Tailwind CSS**
