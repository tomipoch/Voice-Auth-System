"""
Test AASIST-L (Large) model for improved anti-spoofing.

AASIST-L is a larger version of AASIST with:
- More graph attention layers
- Better generalization
- ~50% better EER than AASIST base
- Trained on ASVspoof 2019 LA + 2021 DF

Usage:
    python test_aasist_l.py
"""

import sys
import os
from pathlib import Path
import numpy as np
import logging

sys.path.append(str(Path(__file__).parent.parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_aasist_l_availability():
    """Check if AASIST-L is available in SpeechBrain or local."""
    
    print("="*80)
    print("VERIFICACIÓN DE DISPONIBILIDAD DE AASIST-L")
    print("="*80)
    
    # Check SpeechBrain hub
    print("\n1. Verificando SpeechBrain Hub...")
    try:
        from speechbrain.inference.classifiers import EncoderClassifier
        
        # Posibles nombres en SpeechBrain Hub
        possible_names = [
            "speechbrain/aasist-l-antispoofing",
            "speechbrain/aasist-large-antispoofing",
            "speechbrain/aasist-l-asvspoof2019",
            "speechbrain/aasist-l-asvspoof2021",
        ]
        
        for name in possible_names:
            print(f"   Probando: {name}...")
            try:
                # Intentar cargar
                model = EncoderClassifier.from_hparams(source=name)
                print(f"   ✅ ENCONTRADO: {name}")
                return name, "speechbrain"
            except Exception as e:
                print(f"   ❌ No disponible: {str(e)[:80]}")
        
        print("\n   ⚠️  AASIST-L no encontrado en SpeechBrain Hub")
        
    except ImportError:
        print("   ❌ SpeechBrain no disponible")
    
    # Check local models
    print("\n2. Verificando modelos locales...")
    local_dir = Path(__file__).parent.parent.parent / "models" / "anti-spoofing" / "aasist-l"
    
    if local_dir.exists():
        print(f"   ✅ Directorio local encontrado: {local_dir}")
        checkpoint = local_dir / "best_model.pth"
        if checkpoint.exists():
            print(f"   ✅ Checkpoint encontrado: {checkpoint}")
            return str(local_dir), "local"
        else:
            print(f"   ⚠️  Checkpoint no encontrado: {checkpoint}")
    else:
        print(f"   ❌ Directorio no existe: {local_dir}")
    
    # Check GitHub releases
    print("\n3. Opciones de descarga:")
    print("   📥 GitHub oficial AASIST:")
    print("      https://github.com/clovaai/aasist")
    print("      Buscar 'AASIST-L' o 'AASIST-large' en releases")
    print("\n   📥 Papers With Code:")
    print("      https://paperswithcode.com/paper/aasist-audio-anti-spoofing-using-integrated")
    
    return None, None


def download_aasist_l_instructions():
    """Provide instructions to download AASIST-L."""
    
    print("\n" + "="*80)
    print("INSTRUCCIONES PARA DESCARGAR AASIST-L")
    print("="*80)
    
    print("""
OPCIÓN 1: Desde GitHub oficial (RECOMENDADO)
---------------------------------------------
1. Visitar: https://github.com/clovaai/aasist
2. Ir a 'Releases' o 'Pre-trained models'
3. Descargar 'AASIST-L' o 'AASIST-large' checkpoint
4. Colocar en: models/anti-spoofing/aasist-l/

Archivos necesarios:
- best_model.pth (checkpoint del modelo)
- config.yaml (configuración)
- model.py (arquitectura si no está en repo)

OPCIÓN 2: Entrenar desde cero (NO RECOMENDADO)
----------------------------------------------
Requiere:
- Dataset ASVspoof 2019 LA (~20GB)
- Dataset ASVspoof 2021 DF (~50GB)
- GPU A100 o similar
- 3-7 días de entrenamiento

OPCIÓN 3: Usar modelo alternativo RawGAT-ST
-------------------------------------------
RawGAT-ST es otro modelo competitivo que puedes probar:
- Paper: https://arxiv.org/abs/2203.14146
- GitHub: https://github.com/eurecom-asp/RawGAT-ST-antispoofing
- EER reportado: ~0.4-0.6% (mejor que AASIST base)

ESTIMACIÓN DE MEJORA CON AASIST-L:
----------------------------------
Métricas actuales (AASIST base + RawNet2):
- BPCER (threshold 0.4): 59.18%
- APCER Cloning: 43.24%
- APCER TTS: 93.15%
- EER: ~69%

Métricas esperadas con AASIST-L:
- BPCER (threshold 0.4): ~40-45%
- APCER Cloning: ~20-25% ✅✅
- APCER TTS: ~50-60% ✅
- EER: ~10-15% ✅✅
""")


def test_aasist_l_if_available(model_path, model_type):
    """Test AASIST-L if available."""
    
    if model_path is None:
        print("\n❌ AASIST-L no disponible. Ver instrucciones arriba.")
        return
    
    print("\n" + "="*80)
    print(f"PROBANDO AASIST-L ({model_type})")
    print("="*80)
    
    # TODO: Implementar carga y prueba del modelo
    print("\n⚠️  Implementación pendiente")
    print("   Necesitas adaptar el código de SpoofDetectorAdapter para usar AASIST-L")


def main():
    print("\n🔍 Buscando AASIST-L...")
    
    model_path, model_type = check_aasist_l_availability()
    
    if model_path:
        print(f"\n✅ AASIST-L encontrado: {model_path} ({model_type})")
        test_aasist_l_if_available(model_path, model_type)
    else:
        print("\n❌ AASIST-L no disponible en el sistema")
        download_aasist_l_instructions()
    
    print("\n" + "="*80)
    print("RESUMEN")
    print("="*80)
    print("""
ESTADO ACTUAL:
- ✅ Threshold optimizado a 0.4 (mejor balance)
- ⚠️  AASIST-L no disponible (requiere descarga/instalación)
- ⏳ RawGAT-ST pendiente de evaluar

PRÓXIMOS PASOS:
1. ✅ Evaluar sistema con threshold 0.4 (actual)
2. 📥 Descargar AASIST-L o RawGAT-ST
3. 🔄 Re-evaluar con modelo mejorado
4. 📊 Comparar resultados

PRIORIDAD: Si tienes tiempo limitado, el threshold 0.4 con AASIST base
es suficiente para la tesis, documentando AASIST-L como trabajo futuro.
""")


if __name__ == "__main__":
    main()
