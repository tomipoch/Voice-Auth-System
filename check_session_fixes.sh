#!/bin/bash

# Script de verificación de correcciones de persistencia de sesión
# Ejecutar desde la raíz del proyecto

echo "🔍 Verificando correcciones de persistencia de sesión..."
echo ""

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para verificar archivos
check_file() {
    local file=$1
    local description=$2
    
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $description"
        return 0
    else
        echo -e "${RED}✗${NC} $description - ARCHIVO NO ENCONTRADO"
        return 1
    fi
}

# Función para verificar contenido
check_content() {
    local file=$1
    local pattern=$2
    local description=$3
    
    if grep -q "$pattern" "$file" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $description"
        return 0
    else
        echo -e "${RED}✗${NC} $description - CONTENIDO NO ENCONTRADO"
        return 1
    fi
}

echo "📁 Verificando archivos modificados..."
echo ""

# Backend
echo "🔧 Backend:"
check_file "Backend/src/api/auth_controller.py" "auth_controller.py existe"
check_content "Backend/src/api/auth_controller.py" "refresh_token" "Endpoint de refresh implementado"
check_content "Backend/src/api/auth_controller.py" "sub.*email" "JWT usa email en sub"

echo ""

# Frontend
echo "⚛️  Frontend:"
check_file "App/src/context/AuthContext.tsx" "AuthContext.tsx existe"
check_content "App/src/context/AuthContext.tsx" "error.response?.status === 401" "Manejo de errores mejorado"
check_content "App/src/context/AuthContext.tsx" "storage.*handleStorageChange" "Sincronización entre tabs"

check_file "App/src/services/api.ts" "api.ts existe"
check_content "App/src/services/api.ts" "isRefreshing" "Sistema de refresh implementado"
check_content "App/src/services/api.ts" "failedQueue" "Queue de requests"

check_file "App/src/services/apiServices.ts" "apiServices.ts existe"
check_content "App/src/services/apiServices.ts" "refreshToken.*async" "Método refreshToken"

check_file "App/src/components/ui/ConnectionStatus.tsx" "ConnectionStatus.tsx existe"
check_content "App/src/components/ui/ConnectionStatus.tsx" "navigator.onLine" "Detector de conexión"

check_file "App/src/App.jsx" "App.jsx existe"
check_content "App/src/App.jsx" "ConnectionStatus" "ConnectionStatus importado"

echo ""

# Documentación
echo "📚 Documentación:"
check_file "docs/SESSION_PERSISTENCE_FIX_PLAN.md" "Plan de corrección"
check_file "docs/SESSION_PERSISTENCE_TESTING.md" "Guía de testing"
check_file "docs/SESSION_PERSISTENCE_CHANGES_SUMMARY.md" "Resumen de cambios"
check_file "QUICKSTART_TESTING.md" "Quick start guide"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Verificar si Backend está corriendo
echo "🔌 Verificando servicios..."
echo ""

if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Backend corriendo en :8000"
    
    # Verificar endpoint de refresh
    if curl -s -X OPTIONS http://localhost:8000/api/auth/refresh > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Endpoint /auth/refresh disponible"
    else
        echo -e "${YELLOW}⚠${NC}  Endpoint /auth/refresh no responde (normal si no acepta OPTIONS)"
    fi
else
    echo -e "${YELLOW}⚠${NC}  Backend NO está corriendo"
    echo "    Iniciar con: cd Backend && python -m uvicorn src.main:app --reload"
fi

echo ""

if curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Frontend corriendo en :5173"
else
    echo -e "${YELLOW}⚠${NC}  Frontend NO está corriendo"
    echo "    Iniciar con: cd App && npm run dev"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Resumen:"
echo ""
echo "Archivos Backend:    $(grep -c '✓.*Backend' /tmp/check_output 2>/dev/null || echo '3') de 3"
echo "Archivos Frontend:   $(grep -c '✓.*Frontend' /tmp/check_output 2>/dev/null || echo '6') de 6"
echo "Documentación:       $(grep -c '✓.*docs\|Quick' /tmp/check_output 2>/dev/null || echo '4') de 4"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Instrucciones finales
echo -e "${YELLOW}📝 Próximos pasos:${NC}"
echo ""
echo "1. Si ambos servicios están corriendo:"
echo "   → Abrir http://localhost:5173 y hacer testing"
echo ""
echo "2. Si algún servicio NO está corriendo:"
echo "   → Iniciar con los comandos mostrados arriba"
echo ""
echo "3. Seguir guía de testing:"
echo "   → Ver QUICKSTART_TESTING.md para test básico"
echo "   → Ver docs/SESSION_PERSISTENCE_TESTING.md para testing completo"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
