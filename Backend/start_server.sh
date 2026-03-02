#!/bin/bash

# Script para iniciar el servidor de desarrollo
cd "$(dirname "$0")"
source venv/bin/activate

# Ignorar directorios de modelos para evitar reinicios en bucle
uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload --reload-exclude "models/*" --reload-exclude "*.ckpt" --reload-exclude "*.pth" --reload-exclude "evaluation/*"
