#!/usr/bin/env python3
"""
Script de desarrollo para ejecutar la API sin Docker.
Deshabilita la autenticación y usa configuraciones de desarrollo.
"""

import os
import sys
from pathlib import Path

# Agregar el directorio src al path de Python
sys.path.insert(0, str(Path(__file__).parent))

# Configurar variables de entorno para desarrollo
os.environ.setdefault('DEVELOPMENT_MODE', 'true')
os.environ.setdefault('SKIP_AUTH', 'true')
os.environ.setdefault('MOCK_BIOMETRICS', 'true')
os.environ.setdefault('DATABASE_URL', 'sqlite:///./voice_biometrics.db')
os.environ.setdefault('API_HOST', '127.0.0.1')
os.environ.setdefault('API_PORT', '8001')
os.environ.setdefault('LOG_LEVEL', 'DEBUG')

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Iniciando Voice Biometrics API en modo desarrollo...")
    print("📍 URL: http://127.0.0.1:8001")
    print("📚 Documentación: http://127.0.0.1:8001/docs")
    print("🔓 Autenticación: DESHABILITADA")
    print("🔬 Biometría: SIMULADA")
    print()
    
    uvicorn.run(
        "src.main:app",
        host="127.0.0.1",
        port=8001,
        reload=True,
        log_level="debug",
        access_log=True
    )