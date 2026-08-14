# VoiceAuth Frontend

Sistema de autenticación biométrica por voz con React + Vite + Tailwind CSS.

## 🚀 Inicio Rápido

```bash
# Instalar dependencias
bun install

# Configurar entorno
cp .env.example .env

# Iniciar desarrollo
bun dev
```

**App disponible en**: http://localhost:5173

## 📁 Estructura

```
App/
├── src/
│   ├── components/     # Componentes React
│   │   ├── admin/      # Panel de administración
│   │   ├── auth/       # Login, Register
│   │   ├── enrollment/ # Registro de voz
│   │   ├── ui/         # Componentes reutilizables
│   │   └── verification/
│   ├── context/        # React Contexts (Auth, Theme)
│   ├── hooks/          # Custom hooks
│   ├── pages/          # Vistas
│   ├── services/       # API y servicios
│   ├── types/          # TypeScript types
│   └── utils/          # Utilidades
├── public/             # Assets estáticos
└── index.html          # Entry point
```

## ⚙️ Scripts

```bash
bun dev           # Servidor de desarrollo
bun run build     # Build de producción
bun run preview   # Preview del build
bun run lint      # Linting + fix
bun run format    # Formatear código
bun test          # Ejecutar tests
bun run typecheck # Verificar tipos
```

## 🔧 Configuración

Variables en `.env`:
```env
VITE_API_URL=http://localhost:8000
VITE_ENABLE_MOCK_DATA=false
```

## 🧪 Testing

```bash
bun test              # Tests unitarios
bun run test:watch    # Mode watch
bun run test:coverage # Con cobertura
```

## 📚 Documentación

Ver [`docs/arquitectura/FRONTEND.md`](../docs/arquitectura/FRONTEND.md) para documentación técnica.
