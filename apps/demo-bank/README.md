# 🏦 Banco Familia - Demo de Integración Biométrica

Aplicación demo que simula un banco real integrando el sistema de autenticación biométrica por voz.

## 🌟 Características

- **Autenticación biométrica por voz** integrada
- **Gestión de cuentas bancarias** con saldos y transacciones
- **Transferencias bancarias** con verificación por PIN y voz
- **Gestión de contactos** para transferencias frecuentes
- **Interfaz moderna** con React + TypeScript + Vite

## 👥 Usuarios Pre-configurados

El sistema incluye los siguientes usuarios de la familia:

| Email | Password | RUT | Balance | Verificación por Voz |
|-------|----------|-----|---------|---------------------|
| ft.fernandotomas@gmail.com | tomas123 | 20904540-0 | $2,500,000 | ✅ Activa |
| piapobletech@gmail.com | pia123 | 18572849-8 | $1,200,000 | ✅ Activa |
| anachamorromunoz@gmail.com | ana123 | 9555737-6 | $1,500,000 | ✅ Activa |
| rapomo3@gmail.com | raul123 | 8385075-2 | $1,800,000 | ✅ Activa |
| maolivautal@gmail.com | matias123 | 21016246-1 | $900,000 | ✅ Activa |
| ignacio.norambuena1990@gmail.com | ignacio123 | 21013703-3 | $750,000 | ✅ Activa |

## 🚀 Instalación

```bash
# Instalar dependencias
bun install

# Iniciar servidor backend (puerto 3001)
bun run server

# En otra terminal, iniciar frontend (puerto 5174)
bun run dev
```

## ⚙️ Configuración

La configuración del banco se encuentra en `server/config.ts`:

```typescript
export const config = {
  port: 3001,
  biometricApi: {
    baseUrl: 'http://localhost:8000',
    adminEmail: 'admin@familia.com',
    adminPassword: 'AdminFamilia123',
  },
  company: {
    name: 'Banco Familia',
    clientId: 'banco-familia',
  },
};
```

## 📋 Requisitos

- **Node.js** 18+ o **Bun** runtime
- **API Biométrica** corriendo en `http://localhost:8000`
- Los usuarios deben estar enrollados en la API biométrica

## 🔒 Seguridad

- Transferencias menores a $200,000: Solo requieren PIN
- Transferencias mayores a $200,000: Requieren PIN + verificación por voz
- Todos los usuarios tienen verificación biométrica activa

## 🛠️ Tecnologías

- **Frontend**: React 19, TypeScript, Tailwind CSS, Vite
- **Backend**: Hono (Node.js), SQLite, JWT
- **Integración**: API REST con sistema biométrico
