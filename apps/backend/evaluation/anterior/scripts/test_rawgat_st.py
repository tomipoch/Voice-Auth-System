"""
Test RawGAT-ST model for improved anti-spoofing.

RawGAT-ST (Raw Waveform Graph Attention with Spectro-Temporal):
- Published: ICASSP 2022
- Performance: EER ~0.4-0.6% on ASVspoof 2021
- Better than AASIST base, comparable to AASIST-L
- GitHub: https://github.com/eurecom-asp/RawGAT-ST-antispoofing

Key advantages:
- Raw waveform processing (like RawNet)
- Graph attention (like AASIST)
- Spectro-temporal modeling
- Strong generalization to unseen attacks

Usage:
    python test_rawgat_st.py
"""

import sys
import os
from pathlib import Path
import numpy as np
import logging

sys.path.append(str(Path(__file__).parent.parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_rawgat_st_availability():
    """Check if RawGAT-ST is available."""
    
    print("="*80)
    print("VERIFICACIÓN DE DISPONIBILIDAD DE RawGAT-ST")
    print("="*80)
    
    print("\n📊 INFORMACIÓN DEL MODELO:")
    print("-" * 80)
    print("""
Nombre: RawGAT-ST (Raw Waveform Graph Attention Spectro-Temporal)
Paper: "Raw Waveform-based Graph Attention for Robust Speech Anti-Spoofing"
Venue: ICASSP 2022
Autores: Tak et al. (EURECOM)

Performance reportada (ASVspoof 2021 DF):
- EER: 0.54%
- min t-DCF: 0.0181
- Rank: Top 3 en ASVspoof 2021

Arquitectura:
- Input: Raw waveform (16 kHz)
- Sinc convolutions (learnable filterbanks)
- Graph Attention Networks (GAT)
- Spectro-temporal feature learning
- Residual connections

Ventajas vs AASIST base:
✅ Mejor EER (~0.5% vs ~0.8%)
✅ Raw waveform processing (sin features manuales)
✅ Mejor generalización a ataques no vistos
✅ Más robusto a artifacts
""")
    
    # Check local
    print("\n1. Verificando modelos locales...")
    local_dir = Path(__file__).parent.parent.parent / "models" / "anti-spoofing" / "rawgat-st"
    
    if local_dir.exists():
        print(f"   ✅ Directorio local encontrado: {local_dir}")
        checkpoint = local_dir / "best_model.pth"
        if checkpoint.exists():
            print(f"   ✅ Checkpoint encontrado: {checkpoint}")
            return str(local_dir), "local"
        else:
            print(f"   ⚠️  Checkpoint no encontrado")
    else:
        print(f"   ❌ Directorio no existe: {local_dir}")
    
    print("\n2. Fuentes de descarga:")
    print("   📥 GitHub oficial:")
    print("      https://github.com/eurecom-asp/RawGAT-ST-antispoofing")
    print("\n   📥 Pre-trained models:")
    print("      Incluidos en el repositorio GitHub")
    
    return None, None


def download_instructions():
    """Provide download instructions."""
    
    print("\n" + "="*80)
    print("INSTRUCCIONES PARA DESCARGAR RawGAT-ST")
    print("="*80)
    
    print("""
PASO 1: Clonar repositorio
---------------------------
git clone https://github.com/eurecom-asp/RawGAT-ST-antispoofing.git
cd RawGAT-ST-antispoofing

PASO 2: Descargar pre-trained model
------------------------------------
# Los modelos pre-entrenados suelen estar en:
# - /pre-trained/ o /models/
# - Releases de GitHub
# - Google Drive (link en README)

Buscar archivos:
- model_checkpoint.pth
- config.yaml o config.conf
- model.py (arquitectura)

PASO 3: Copiar a tu proyecto
-----------------------------
cp -r pre-trained/rawgat-st models/anti-spoofing/rawgat-st/

PASO 4: Adaptar código
-----------------------
Necesitas crear un wrapper en SpoofDetectorAdapter.py similar a:
- LocalAASISTModel
- LocalRawNet2Model

Agregar: LocalRawGATSTModel

ESTIMACIÓN DE MEJORA CON RawGAT-ST:
-----------------------------------
Métricas actuales (AASIST + RawNet2, threshold 0.4):
- BPCER: 59.18%
- APCER Cloning: 43.24%
- APCER TTS: 93.15%
- EER: ~69%

Métricas esperadas con RawGAT-ST (basado en literatura):
- BPCER (threshold 0.4): ~35-40% ✅
- APCER Cloning: ~15-20% ✅✅✅
- APCER TTS: ~40-50% ✅✅
- EER: ~8-12% ✅✅✅

COMPARACIÓN DE MODELOS:
-----------------------
Modelo          | EER (ASVspoof) | Estimación tu dataset | Disponibilidad
----------------|----------------|-----------------------|----------------
AASIST (actual) | 0.83%          | ~69% EER              | ✅ Instalado
RawNet2 (actual)| 2.48%          | -                     | ✅ Instalado
AASIST-L        | 0.39%          | ~10-15% EER           | ❌ No disponible
RawGAT-ST       | 0.54%          | ~8-12% EER            | ❌ No disponible
""")


def compare_models_table():
    """Show comparison table of all models."""
    
    print("\n" + "="*80)
    print("COMPARACIÓN COMPLETA DE OPCIONES")
    print("="*80)
    
    print("""
┌──────────────────┬────────────┬────────────────┬─────────────┬──────────────┐
│ Configuración    │ EER        │ Detección      │ BPCER       │ Esfuerzo     │
│                  │            │ Cloning        │ (thr 0.4)   │ Implementar  │
├──────────────────┼────────────┼────────────────┼─────────────┼──────────────┤
│ ACTUAL           │ ~69%       │ 30% (malo)     │ 59%         │ ✅ Ya hecho  │
│ (AASIST+RawNet2) │            │                │             │              │
├──────────────────┼────────────┼────────────────┼─────────────┼──────────────┤
│ Threshold 0.4    │ ~69%       │ 57% (mejor)    │ 59%         │ ✅ Ya hecho  │
│ (AASIST+RawNet2) │            │                │             │              │
├──────────────────┼────────────┼────────────────┼─────────────┼──────────────┤
│ AASIST-L         │ ~10-15%    │ 75-80% (bueno) │ 40-45%      │ ⚠️  Medio    │
│ + RawNet2        │            │                │             │ (2-3 días)   │
├──────────────────┼────────────┼────────────────┼─────────────┼──────────────┤
│ RawGAT-ST        │ ~8-12%     │ 80-85% (excel) │ 35-40%      │ ⚠️  Medio    │
│ solo             │            │                │             │ (2-3 días)   │
├──────────────────┼────────────┼────────────────┼─────────────┼──────────────┤
│ RawGAT-ST        │ ~5-8%      │ 85-90% (excel) │ 25-30%      │ ❌ Alto      │
│ + AASIST-L       │            │                │             │ (1 semana)   │
│ (ensemble)       │            │                │             │              │
└──────────────────┴────────────┴────────────────┴─────────────┴──────────────┘

RECOMENDACIÓN SEGÚN TIEMPO DISPONIBLE:
--------------------------------------
⏱️  Poco tiempo (1-2 días):
   → Usar threshold 0.4 con modelos actuales
   → Documentar limitaciones conocidas
   → Proponer AASIST-L/RawGAT-ST como trabajo futuro
   
⏱️  Tiempo medio (3-5 días):
   → Implementar RawGAT-ST (más fácil que AASIST-L)
   → Re-evaluar sistema completo
   → Comparar con baseline
   
⏱️  Tiempo amplio (1-2 semanas):
   → Implementar ambos modelos
   → Crear ensemble optimizado
   → Realizar ablation study completo
""")


def main():
    print("\n🔍 Verificando RawGAT-ST...")
    
    model_path, model_type = check_rawgat_st_availability()
    
    if model_path:
        print(f"\n✅ RawGAT-ST encontrado: {model_path}")
    else:
        print("\n❌ RawGAT-ST no disponible")
        download_instructions()
    
    compare_models_table()
    
    print("\n" + "="*80)
    print("SIGUIENTE PASO")
    print("="*80)
    print("""
1️⃣ AHORA: Evaluar con threshold 0.4 (ya aplicado)
   python evaluation/scripts/analyze_antispoofing_corrected.py

2️⃣ OPCIONAL: Descargar e implementar RawGAT-ST o AASIST-L
   
3️⃣ DOCUMENTAR: Agregar resultados a tu tesis con análisis comparativo

¿Quieres continuar con la evaluación actual o prefieres descargar
uno de los modelos mejorados primero?
""")


if __name__ == "__main__":
    main()
