"""
Verificar que AASIST-L se cargue correctamente desde archivos locales.
"""

import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir / "src"))

import torch
from infrastructure.biometrics.local_antispoof_models import (
    LocalAASISTModel,
    build_local_model_paths
)
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def verify_aasist_l():
    """Verificar que AASIST-L se cargue desde los archivos locales."""
    
    print("="*80)
    print("VERIFICACIÓN DE CARGA DE AASIST-L LOCAL")
    print("="*80)
    
    # Verificar archivos
    print("\n1. Verificando archivos locales...")
    local_paths = build_local_model_paths()
    aasist_dir = local_paths.aasist_dir
    
    print(f"   Directorio AASIST: {aasist_dir}")
    
    files_to_check = [
        ("AASIST-L.pth", "Checkpoint AASIST-L"),
        ("AASIST-L.conf", "Configuración AASIST-L"),
        ("AASIST.py", "Código del modelo"),
    ]
    
    all_found = True
    for filename, description in files_to_check:
        filepath = aasist_dir / filename
        if filepath.exists():
            size_mb = filepath.stat().st_size / (1024*1024)
            print(f"   ✅ {description}: {filepath.name} ({size_mb:.1f}MB)")
        else:
            print(f"   ❌ {description}: {filename} NO ENCONTRADO")
            all_found = False
    
    if not all_found:
        print("\n⚠️  Faltan archivos necesarios para AASIST-L")
        return False
    
    # Cargar modelo
    print("\n2. Intentando cargar AASIST-L...")
    try:
        device = torch.device("cpu")
        model = LocalAASISTModel(device=device, paths=local_paths)
        
        if not model.available:
            print("   ❌ Modelo no se pudo cargar (available=False)")
            return False
        
        print(f"   ✅ Modelo {model._model_name} cargado exitosamente")
        print(f"   📏 Target length: {model._target_len}")
        
        # Probar predicción
        print("\n3. Probando predicción con audio dummy...")
        dummy_audio = torch.randn(1, 16000)  # 1 segundo
        
        score = model.predict_spoof_probability(dummy_audio, 16000)
        
        if score is not None:
            print(f"   ✅ Predicción exitosa!")
            print(f"   📊 Score de prueba: {score:.4f}")
            print(f"      (0.0 = genuino, 1.0 = spoofed)")
            
            print("\n" + "="*80)
            print("✅ AASIST-L SE CARGÓ Y FUNCIONA CORRECTAMENTE")
            print("="*80)
            return True
        else:
            print("   ❌ La predicción retornó None")
            return False
            
    except Exception as e:
        print(f"   ❌ Error al cargar modelo: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = verify_aasist_l()
    
    if success:
        print("\n✅ El sistema está listo para usar AASIST-L")
        print("   Los siguientes componentes usarán automáticamente AASIST-L:")
        print("   - SpoofDetectorAdapter")
        print("   - Scripts de evaluación")
        print("   - API de verificación biométrica")
    else:
        print("\n⚠️  El sistema usará el modelo AASIST base o fallback de SpeechBrain")
