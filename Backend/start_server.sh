#!/bin/bash

# Script para iniciar el servidor de desarrollo
cd "$(dirname "$0")"
source venv/bin/activate
uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
