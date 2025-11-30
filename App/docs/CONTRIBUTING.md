# Contributing to VoiceAuth

¡Gracias por tu interés en contribuir a VoiceAuth! 🎉

## 📋 Tabla de Contenidos

- [Código de Conducta](#código-de-conducta)
- [¿Cómo puedo contribuir?](#cómo-puedo-contribuir)
- [Setup de Desarrollo](#setup-de-desarrollo)
- [Guías de Estilo](#guías-de-estilo)
- [Proceso de Pull Request](#proceso-de-pull-request)
- [Reportar Bugs](#reportar-bugs)
- [Sugerir Features](#sugerir-features)

## 📜 Código de Conducta

Este proyecto sigue nuestro [Código de Conducta](CODE_OF_CONDUCT.md). Al participar, se espera que lo respetes.

## 🤝 ¿Cómo puedo contribuir?

### Tipos de Contribuciones

- 🐛 **Reportar bugs**
- ✨ **Sugerir nuevas features**
- 📝 **Mejorar documentación**
- 🧪 **Escribir tests**
- 🔧 **Arreglar bugs**
- 💡 **Implementar features**
- 🎨 **Mejorar UI/UX**

## 🛠️ Setup de Desarrollo

### 1. Fork y Clone

```bash
# Fork el repositorio en GitHub
# Luego clona tu fork
git clone https://github.com/TU-USUARIO/Proyecto.git
cd Proyecto/App
```

### 2. Configurar Upstream

```bash
git remote add upstream https://github.com/tomipoch/Proyecto.git
git fetch upstream
```

### 3. Instalar Dependencias

```bash
npm install
```

### 4. Configurar Ambiente

```bash
cp .env.example .env
# Edita .env con tus configuraciones
```

### 5. Iniciar Desarrollo

```bash
npm run dev
```

### 6. Verificar Setup

```bash
# Ejecutar tests
npm test

# Lint
npm run lint

# Format
npm run format

# Build
npm run build
```

## 📐 Guías de Estilo

### Código

#### JavaScript/React

- **ES6+** features
- **Functional components** con hooks
- **PropTypes** o TypeScript para type checking
- **Nombres descriptivos** para variables y funciones
- **Comentarios** solo cuando sea necesario

```javascript
// ✅ Good
const [isLoading, setIsLoading] = useState(false);

const handleUserLogin = async (credentials) => {
  // Implementation
};

// ❌ Bad
const [x, setX] = useState(false);

const f = async (c) => {
  // Implementation
};
```

#### CSS/Tailwind

- **Tailwind utility classes** primero
- **Custom CSS** solo cuando sea necesario
- **Mobile-first** approach
- **Dark mode** considerado

```jsx
// ✅ Good
<button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 dark:bg-blue-500">
  Click me
</button>

// ❌ Bad
<button style={{ padding: '8px 16px', backgroundColor: '#2563eb' }}>
  Click me
</button>
```

### Commits

Seguimos [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**

- `feat`: Nueva feature
- `fix`: Bug fix
- `docs`: Solo documentación
- `style`: Formato, punto y coma, etc
- `refactor`: Refactorización
- `test`: Tests
- `chore`: Mantenimiento

**Examples:**

```bash
feat(auth): add biometric verification

Implemented voice biometric verification with quality check.

Closes #123

fix(ui): button hover state in dark mode

The button wasn't showing proper hover state in dark mode.

docs: update installation instructions

test(storage): add tests for localStorage service
```

### Branches

**Formato:**

```
<type>/<short-description>
```

**Examples:**

```bash
feature/voice-enrollment
fix/dark-mode-button
docs/api-documentation
refactor/auth-service
test/component-testing
```

## 🔄 Proceso de Pull Request

### 1. Crear Branch

```bash
git checkout -b feature/nueva-feature
```

### 2. Hacer Cambios

```bash
# Editar archivos
git add .
git commit -m "feat: nueva feature"
```

### 3. Mantener Actualizado

```bash
git fetch upstream
git rebase upstream/main
```

### 4. Push

```bash
git push origin feature/nueva-feature
```

### 5. Crear PR

- Ve a GitHub y crea el Pull Request
- Llena la plantilla de PR
- Asegúrate que los checks pasen

### 6. Code Review

- Responde a comentarios
- Haz cambios solicitados
- Push los cambios (automáticamente se actualizan en el PR)

### 7. Merge

Una vez aprobado, un mantenedor hará merge del PR.

## ✅ Checklist para PRs

Antes de crear tu PR, verifica:

- [ ] Tests pasan (`npm test`)
- [ ] Lint pasa (`npm run lint`)
- [ ] Código formateado (`npm run format`)
- [ ] Build exitoso (`npm run build`)
- [ ] Documentación actualizada
- [ ] Commits siguen convenciones
- [ ] Branch actualizado con main
- [ ] Sin console.logs
- [ ] Sin código comentado
- [ ] Tests nuevos para nueva funcionalidad

## 🐛 Reportar Bugs

### Antes de Reportar

1. **Busca** en issues existentes
2. **Verifica** que estás usando la última versión
3. **Reproduce** el bug consistentemente

### Template de Bug Report

```markdown
**Descripción del Bug**
Descripción clara y concisa del bug.

**Pasos para Reproducir**

1. Ve a '...'
2. Click en '...'
3. Scroll down to '...'
4. Ver error

**Comportamiento Esperado**
Qué esperabas que pasara.

**Screenshots**
Si aplica, agrega screenshots.

**Ambiente:**

- OS: [ej: macOS 14.0]
- Browser: [ej: Chrome 120]
- Node.js: [ej: 18.0.0]
- Version: [ej: 1.0.0]

**Contexto Adicional**
Cualquier otra información relevante.
```

## ✨ Sugerir Features

### Template de Feature Request

```markdown
**¿Tu feature está relacionado con un problema?**
Descripción clara del problema.

**Describe la solución que te gustaría**
Descripción clara de lo que quieres que pase.

**Describe alternativas que consideraste**
Otras soluciones o features que consideraste.

**Contexto Adicional**
Screenshots, mockups, etc.
```

## 🧪 Testing Guidelines

### Escribir Tests

```javascript
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';

describe('ComponentName', () => {
  it('renders correctly', () => {
    render(<ComponentName />);
    expect(screen.getByText('Expected Text')).toBeInTheDocument();
  });

  it('handles user interaction', async () => {
    render(<ComponentName />);
    await userEvent.click(screen.getByRole('button'));
    expect(screen.getByText('Updated Text')).toBeInTheDocument();
  });
});
```

### Coverage

Mantener cobertura > 80%:

```bash
npm run test:coverage
```

## 📝 Documentación

### README

Actualizar README.md si:

- Agregas nueva feature
- Cambias API
- Modificas instalación
- Actualizas configuración

### Comentarios

```javascript
/**
 * Registra un nuevo usuario con verificación biométrica
 * @param {Object} userData - Datos del usuario
 * @param {string} userData.email - Email del usuario
 * @param {string} userData.password - Password
 * @param {Array} userData.voiceSamples - Muestras de voz
 * @returns {Promise<Object>} Usuario registrado
 */
async function registerUser(userData) {
  // Implementation
}
```

## 🎯 Prioridades

### High Priority

- 🔴 Bugs críticos
- 🔴 Vulnerabilidades de seguridad
- 🔴 Features bloqueantes

### Medium Priority

- 🟡 Mejoras de performance
- 🟡 Refactorizaciones
- 🟡 Documentación

### Low Priority

- 🟢 Features nice-to-have
- 🟢 Mejoras de UI
- 🟢 Optimizaciones menores

## 💬 Comunicación

### Channels

- **Issues**: Para bugs y features
- **Discussions**: Para preguntas y discusiones
- **Email**: Para temas sensibles

### Response Times

- **Bugs críticos**: 24 horas
- **PRs**: 2-3 días
- **Issues**: 1 semana
- **Discussions**: Best effort

## 🏆 Reconocimientos

Todos los contribuidores serán:

- Listados en README.md
- Mencionados en releases
- Agradecidos públicamente

## 📚 Recursos

- [React Docs](https://react.dev)
- [Vite Docs](https://vitejs.dev)
- [Tailwind CSS](https://tailwindcss.com)
- [Testing Library](https://testing-library.com)
- [Conventional Commits](https://www.conventionalcommits.org)

## ❓ Preguntas

¿Tienes preguntas? ¡No dudes en:

- Abrir una discussion
- Comentar en un issue
- Contactar a los mantenedores

---

**¡Gracias por contribuir! 🙏**
