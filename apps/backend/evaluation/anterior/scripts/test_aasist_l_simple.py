"""
Prueba simple para verificar si AASIST-L está disponible y funciona.
"""

import sys
from pathlib import Path

# Add src directory to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir / "src"))

from infrastructure.biometrics.model_manager import model_manager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_aasist_l():
    """Verificar disponibilidad y funcionamiento de AASIST-L."""
    
    print("="*80)
    print("PRUEBA DE AASIST-L")
    print("="*80)
    
    # Verificar configuración
    print("\n1. Verificando configuración en model_manager...")
    if "aasist" in model_manager.models:
        config = model_manager.models["aasist"]
        print(f"   ✅ Configuración encontrada:")
        print(f"      Nombre: {config.name}")
        print(f"      Source: {config.source}")
        print(f"      Versión: {config.version}")
        print(f"      Tamaño: {config.size_mb}MB")
        print(f"      Memoria estimada: {config.memory_usage_mb}MB")
    else:
        print("   ❌ Configuración no encontrada")
        return False
    
    # Verificar si está descargado
    print("\n2. Verificando si está descargado localmente...")
    is_available = model_manager.is_model_available("aasist")
    model_path = model_manager.get_model_path("aasist")
    
    if is_available:
        print(f"   ✅ Modelo disponible en: {model_path}")
    else:
        print(f"   ⚠️  Modelo no descargado. Ruta esperada: {model_path}")
        print("\n   ¿Descargar ahora? Esto puede tomar varios minutos...")
        print("   El modelo se descargará automáticamente en la primera ejecución.")
    
    # Intentar cargar el modelo
    print("\n3. Intentando cargar el modelo...")
    try:
        from speechbrain.inference.classifiers import EncoderClassifier
        
        print("   Cargando AASIST-L desde SpeechBrain...")
        classifier = EncoderClassifier.from_hparams(
            source=config.source,
            savedir=str(model_path),
            run_opts={"device": "cpu"}
        )
        
        print("   ✅ Modelo cargado exitosamente!")
        print(f"   ✅ Archivos guardados en: {model_path}")
        
        # Verificar que se puede usar
        print("\n4. Verificando funcionalidad básica...")
        import torch
        dummy_audio = torch.randn(1, 16000)  # 1 segundo de audio dummy
        
        try:
            scores, _, _ = classifier.classify_batch(dummy_audio)
            print(f"   ✅ Predicción exitosa! Score shape: {scores.shape}")
            print(f"      Score de prueba: {scores[0].item():.4f}")
            
            print("\n" + "="*80)
            print("✅ AASIST-L ESTÁ FUNCIONANDO CORRECTAMENTE")
            print("="*80)
            return True
            
        except Exception as e:
            print(f"   ❌ Error al hacer predicción: {e}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error al cargar modelo: {e}")
        print(f"\n   Detalles: {type(e).__name__}")
        
        if "speechbrain/aasist-l-wav2vec2-AASIST" in str(e):
            print("\n   ⚠️  El modelo AASIST-L no existe en SpeechBrain Hub.")
            print("   💡 Probablemente el nombre correcto es uno de estos:")
            print("      - speechbrain/aasist-wav2vec2-AASIST (base)")
            print("      - Otro nombre que necesitamos verificar")
            
        return False


if __name__ == "__main__":
    success = test_aasist_l()
    
    if not success:
        print("\n" + "="*80)
        print("SIGUIENTES PASOS")
        print("="*80)
        print("""
1. Verificar el nombre correcto del modelo AASIST-L en:
   https://huggingface.co/speechbrain

2. Si AASIST-L no está disponible en SpeechBrain Hub:
   - Usar AASIST base (ya funciona)
   - O descargar AASIST-L desde: https://github.com/clovaai/aasist
   
3. Para ver todos los modelos disponibles:
   https://huggingface.co/models?other=speechbrain
""")
