# Testing Guide

## 📋 Overview

Este proyecto utiliza **Vitest** y **React Testing Library** para testing unitario y de integración.

## 🚀 Comandos Disponibles

```bash
# Ejecutar todos los tests una vez
npm test

# Ejecutar tests en modo watch (desarrollo)
npm run test:watch

# Ejecutar tests con interfaz UI
npm run test:ui

# Generar reporte de cobertura
npm run test:coverage
```

## 🏗️ Estructura de Tests

```
src/
├── components/
│   └── ui/
│       └── __tests__/          # Tests de componentes UI
│           ├── Button.test.jsx
│           └── Card.test.jsx
└── test/
    ├── setup.js                # Configuración global de tests
    └── __tests__/              # Tests de servicios y contextos
        ├── auth.test.jsx
        └── storage.test.js
```

## ✅ Ejemplos de Tests

### Test de Componente Simple

```jsx
// Button.test.jsx
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import Button from '../Button';

describe('Button Component', () => {
  it('renders button with text', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('handles click events', async () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click</Button>);

    const button = screen.getByText('Click');
    await userEvent.click(button);

    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
```

### Test de Servicio

```javascript
// storage.test.js
import { describe, it, expect, beforeEach } from 'vitest';
import { storageService } from '../../services/storage';

describe('Storage Service', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('stores and retrieves items', () => {
    const testData = { name: 'test', value: 123 };
    storageService.setItem('test-key', testData);

    const retrieved = storageService.getItem('test-key');
    expect(retrieved).toEqual(testData);
  });
});
```

### Test con Context Providers

```jsx
// auth.test.jsx
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../../context/AuthContext';
import { ThemeProvider } from '../../context/ThemeContext';

describe('Authentication Context', () => {
  const wrapper = ({ children }) => (
    <BrowserRouter>
      <ThemeProvider>
        <AuthProvider>{children}</AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  );

  it('provides authentication context', () => {
    const TestComponent = () => {
      const { user, isAuthenticated } = useAuth();
      return (
        <div>
          <p>Authenticated: {isAuthenticated ? 'yes' : 'no'}</p>
          <p>User: {user?.name || 'none'}</p>
        </div>
      );
    };

    render(<TestComponent />, { wrapper });
    expect(screen.getByText(/Authenticated:/)).toBeInTheDocument();
  });
});
```

## 🔧 Configuración

### vitest.config.js

```javascript
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.js',
    css: true,
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: ['node_modules/', 'src/test/', '**/*.config.js', '**/mockApi.js'],
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
```

### src/test/setup.js

El archivo de setup configura:

- Cleanup automático después de cada test
- Mock de `window.matchMedia` para tests de dark mode
- Mock de `localStorage` con soporte completo
- Mock de `IntersectionObserver`
- `userEvent` global para interacciones de usuario

## 📊 Cobertura de Tests

Para ver el reporte de cobertura:

```bash
npm run test:coverage
```

El reporte se genera en `coverage/index.html` y se puede abrir en el navegador.

### Objetivos de Cobertura

- **Statements**: > 80%
- **Branches**: > 75%
- **Functions**: > 80%
- **Lines**: > 80%

## 🎯 Best Practices

### 1. Organización

- Coloca tests cerca de los componentes que testean
- Usa `__tests__` para agrupar tests relacionados
- Nombra archivos de test con `.test.jsx` o `.test.js`

### 2. Nomenclatura

```javascript
describe('ComponentName', () => {
  it('does something specific', () => {
    // test implementation
  });
});
```

### 3. Qué Testear

✅ **SÍ testear:**

- Renderizado de componentes
- Interacciones de usuario (clicks, inputs)
- Lógica de negocio
- Manejo de errores
- Estados y props

❌ **NO testear:**

- Detalles de implementación
- Librerías de terceros
- Código trivial

### 4. Mocking

```javascript
// Mock de función
const mockFn = vi.fn();

// Mock de módulo
vi.mock('../../services/api', () => ({
  fetchUser: vi.fn(() => Promise.resolve({ id: 1, name: 'Test' })),
}));
```

### 5. Async Testing

```javascript
// Esperar por elemento
await waitFor(() => {
  expect(screen.getByText('Loaded')).toBeInTheDocument();
});

// Esperar por cambio
await waitForElementToBeRemoved(() => screen.queryByText('Loading...'));
```

## 🐛 Debugging Tests

### Ver UI de Tests

```bash
npm run test:ui
```

Abre una interfaz web interactiva para explorar y debuggear tests.

### Logs y Debug

```javascript
import { screen, debug } from '@testing-library/react';

// Imprimir el DOM actual
screen.debug();

// Imprimir un elemento específico
debug(screen.getByRole('button'));
```

### Ejecutar Test Específico

```bash
# Solo tests que contienen "Button"
npx vitest Button

# Solo un archivo
npx vitest src/components/ui/__tests__/Button.test.jsx
```

## 🔗 Recursos

- [Vitest Documentation](https://vitest.dev/)
- [React Testing Library](https://testing-library.com/react)
- [Testing Library Queries](https://testing-library.com/docs/queries/about)
- [Common Mistakes](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)

## 📝 Checklist para Nuevos Tests

- [ ] Test describe el comportamiento, no la implementación
- [ ] Usa queries apropiadas (getBy, findBy, queryBy)
- [ ] Limpia efectos secundarios (useEffect, timers, etc.)
- [ ] Mock de APIs externas
- [ ] Tests son independientes entre sí
- [ ] Usa `userEvent` en lugar de `fireEvent`
- [ ] Verifica accesibilidad (roles, labels)
