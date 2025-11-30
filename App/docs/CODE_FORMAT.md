# Guía de Formato de Código

Este proyecto utiliza **Prettier** y **ESLint** para mantener un código limpio y consistente.

## 🎨 Configuración de Prettier

El proyecto está configurado con las siguientes reglas de formato:

- **Semi**: `;` al final de las declaraciones
- **Single Quotes**: Comillas simples para strings
- **Print Width**: 100 caracteres por línea
- **Tab Width**: 2 espacios
- **Trailing Commas**: ES5 (objetos, arrays)
- **Arrow Parens**: Siempre usar paréntesis en funciones flecha
- **End of Line**: LF (Unix)
- **Bracket Spacing**: Espacios en llaves de objetos

## 📝 Comandos Disponibles

### Formatear Código

```bash
# Formatear todo el código
npm run format

# Verificar formato sin modificar
npm run format:check
```

### Linting

```bash
# Ejecutar linter
npm run lint

# Arreglar errores automáticamente
npm run lint:fix
```

### Workflow Recomendado

```bash
# Antes de commit
npm run format && npm run lint:fix
```

## 🔧 Configuración de VS Code

El proyecto incluye configuración automática para VS Code:

1. Instala las extensiones recomendadas (`.vscode/extensions.json`)
2. El formato se aplicará automáticamente al guardar
3. Los errores de ESLint se corregirán al guardar

### Extensiones Recomendadas

- **Prettier - Code formatter** (`esbenp.prettier-vscode`)
- **ESLint** (`dbaeumer.vscode-eslint`)
- **Tailwind CSS IntelliSense** (`bradlc.vscode-tailwindcss`)

## 📋 Reglas Principales

### JavaScript/JSX

```javascript
// ✅ Correcto
const greeting = 'Hello World';
const sum = (a, b) => a + b;

// ❌ Incorrecto
const greeting = 'Hello World';
const sum = (a, b) => a + b;
```

### Imports

```javascript
// ✅ Correcto
import { useState, useEffect } from 'react';
import Button from './Button';

// ❌ Incorrecto
import { useState, useEffect } from 'react';
import Button from './Button';
```

### Objetos y Arrays

```javascript
// ✅ Correcto
const config = {
  name: 'VoiceAuth',
  version: '1.0.0',
};

const items = [1, 2, 3];

// ❌ Incorrecto
const config = { name: 'VoiceAuth', version: '1.0.0' };
const items = [1, 2, 3];
```

## 🚫 Archivos Ignorados

Prettier ignora automáticamente:

- `node_modules/`
- `dist/`
- `build/`
- `.env*`
- Archivos minificados (`*.min.js`, `*.min.css`)

## 🔍 Integración con Git

### Pre-commit Hook (Opcional)

Para formatear automáticamente antes de cada commit, instala husky:

```bash
npm install --save-dev husky lint-staged
npx husky init
```

Luego agrega en `package.json`:

```json
{
  "lint-staged": {
    "src/**/*.{js,jsx,ts,tsx}": ["prettier --write", "eslint --fix"]
  }
}
```

## 💡 Tips

1. **Usa `npm run format` antes de commits importantes**
2. **Configura tu editor para formatear al guardar**
3. **Revisa los warnings de ESLint regularmente**
4. **Mantén el código consistente con las reglas establecidas**

## 🐛 Solución de Problemas

### Prettier no formatea al guardar

1. Verifica que la extensión esté instalada
2. Revisa la configuración en `.vscode/settings.json`
3. Reinicia VS Code

### Conflictos entre ESLint y Prettier

El proyecto usa `eslint-config-prettier` para evitar conflictos. Si encuentras alguno:

```bash
npm run lint:fix && npm run format
```

### Errores después de formatear

Algunos errores de ESLint requieren corrección manual. Ejecuta:

```bash
npm run lint
```

Para ver los errores restantes.
