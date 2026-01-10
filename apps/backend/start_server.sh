#!/bin/bash

# Script para iniciar el servidor de desarrollo
cd "$(dirname "$0")"
source venv/bin/activate

# API Keys para empresas cliente (incluye Banco Pirulete para demo)
export API_KEYS='{
  "dev-api-key": {
    "client_id": "dev-client",
    "client_name": "Development Client",
    "rate_limit": 1000,
    "permissions": ["verify", "enroll", "challenge"]
  },
  "banco-pirulete-key-2024": {
    "client_id": "banco-pirulete",
    "client_name": "Banco Pirulete",
    "rate_limit": 500,
    "permissions": ["verify", "enroll", "challenge"]
  }
}'

# Modo desarrollo - permite requests sin API key para endpoints de auth
export DEVELOPMENT_MODE=true

# Ignorar directorios de modelos para evitar reinicios en bucle
uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload --reload-exclude "models/*" --reload-exclude "*.ckpt" --reload-exclude "*.pth" --reload-exclude "evaluation/*"

