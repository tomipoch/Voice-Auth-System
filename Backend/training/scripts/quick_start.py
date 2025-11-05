#!/usr/bin/env python3
"""
Script de inicio rápido para el sistema de entrenamiento de modelos biométricos.
Guía interactiva para nuevos usuarios.
"""

import os
import sys
from pathlib import Path

def show_welcome():
    """Muestra bienvenida y opciones disponibles."""
    
    print("🎯 **SISTEMA DE ENTRENAMIENTO - MODELOS BIOMÉTRICOS**")
    print("=" * 60)
    print("Bienvenido al sistema de entrenamiento para modelos de voz biométricos")
    print("Este script te guiará para empezar rápidamente.")
    print()

def check_environment():
    """Verifica el entorno de trabajo."""
    
    print("🔍 **VERIFICANDO ENTORNO...**")
    
    # Verificar estructura de directorios
    required_dirs = [
        "../configs",
        "../datasets", 
        "../models",
        "../evaluation",
        "data_generation",
        "downloading", 
        "utils"
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            missing_dirs.append(dir_path)
    
    if missing_dirs:
        print(f"❌ Directorios faltantes: {missing_dirs}")
        return False
    
    # Verificar archivos clave
    key_files = [
        "../configs/training_config.yaml",
        "train_models.py",
        "data_generation/create_enhanced_dataset.py",
        "utils/test_training_pipeline.py"
    ]
    
    missing_files = []
    for file_path in key_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Archivos faltantes: {missing_files}")
        return False
    
    print("✅ Estructura de directorios correcta")
    
    # Verificar dependencias Python
    try:
        import speechbrain
        import torch
        import torchaudio
        import librosa
        print("✅ Dependencias principales instaladas")
    except ImportError as e:
        print(f"❌ Dependencia faltante: {e}")
        print("💡 Ejecuta: pip install -r ../../training_requirements.txt")
        return False
    
    return True

def show_quick_start_options():
    """Muestra opciones de inicio rápido."""
    
    print("\n🚀 **OPCIONES DE INICIO RÁPIDO:**")
    print("=" * 40)
    
    print("1. 🧪 **DESARROLLO/PRUEBAS** (Recomendado para empezar)")
    print("   - Crear dataset sintético mejorado")
    print("   - Verificar pipeline de entrenamiento") 
    print("   - Entrenar modelo con datos sintéticos")
    print("   - Tiempo: ~15-30 minutos")
    print()
    
    print("2. 📚 **DATASET PÚBLICO** (LibriSpeech)")
    print("   - Descargar LibriSpeech (6.9 GB)")
    print("   - Entrenar modelo ASR real")
    print("   - Sin registro requerido")
    print("   - Tiempo: ~2-4 horas")
    print()
    
    print("3. 🎓 **DATASETS ACADÉMICOS** (Para investigación)")
    print("   - Registrarse en VoxCeleb y ASVspoof")
    print("   - Descargar datasets oficiales (~45 GB)")
    print("   - Entrenar modelos según anteproyecto")
    print("   - Tiempo: 2-3 días para registro + descarga")
    print()
    
    print("4. ⚙️ **CONFIGURACIÓN PERSONALIZADA**")
    print("   - Modificar configuraciones manualmente")
    print("   - Usar datasets propios")
    print("   - Control total del proceso")
    print()

def execute_option(choice):
    """Ejecuta la opción seleccionada."""
    
    option_handlers = {
        "1": _handle_development_option,
        "2": _handle_librispeech_option,
        "3": _handle_academic_datasets_option,
        "4": _handle_custom_configuration_option
    }
    
    handler = option_handlers.get(choice)
    if handler:
        handler()
    else:
        print("❌ Opción inválida")

def _handle_development_option():
    """Maneja la opción de desarrollo/pruebas."""
    print("\n🧪 **INICIANDO DESARROLLO/PRUEBAS**")
    print("=" * 40)
    
    steps = [
        ("Crear dataset sintético", "python data_generation/create_enhanced_dataset.py"),
        ("Verificar pipeline", "python utils/test_training_pipeline.py"),
        ("Entrenar modelo ECAPA-TDNN", "python train_models.py --model ecapa_tdnn --config ../configs/training_config.yaml --output ../models")
    ]
    
    for i, (desc, cmd) in enumerate(steps, 1):
        print(f"\n📋 **Paso {i}: {desc}**")
        print(f"🔧 Comando: {cmd}")
        
        if i == 1:  # Solo ejecutar automáticamente el primer paso
            _execute_if_confirmed(cmd)
        else:
            print("💡 Ejecuta este comando cuando el anterior termine")

def _handle_librispeech_option():
    """Maneja la opción de descarga de LibriSpeech."""
    print("\n📚 **INICIANDO DESCARGA LIBRISPEECH**")
    print("🔧 Comando: python downloading/download_librispeech.py")
    
    confirm = input("¿Descargar LibriSpeech ahora? (6.9 GB) (y/N): ").strip().lower()
    if confirm == 'y':
        os.system("python downloading/download_librispeech.py")

def _handle_academic_datasets_option():
    """Maneja la opción de datasets académicos."""
    print("\n🎓 **INFORMACIÓN DATASETS ACADÉMICOS**")
    print("🔧 Comando: python downloading/dataset_guide.py")
    os.system("python downloading/dataset_guide.py")

def _handle_custom_configuration_option():
    """Maneja la opción de configuración personalizada."""
    print("\n⚙️ **CONFIGURACIÓN PERSONALIZADA**")
    print("📁 Archivo de configuración: ../configs/training_config.yaml")
    print("📋 Scripts principales:")
    print("   - train_models.py (entrenamiento)")
    print("   - utils/preprocess_audio.py (preprocesamiento)")
    print("   - ../evaluation/evaluate_models.py (evaluación)")

def _execute_if_confirmed(command):
    """Ejecuta comando si el usuario confirma."""
    confirm = input("¿Ejecutar automáticamente? (y/N): ").strip().lower()
    if confirm == 'y':
        os.system(command)
        print("✅ Completado")

def main():
    """Función principal."""
    
    show_welcome()
    
    if not check_environment():
        print("\n🚨 **ACCIÓN REQUERIDA:**")
        print("Corrige los problemas arriba antes de continuar")
        return
    
    show_quick_start_options()
    
    while True:
        choice = input("\nSelecciona una opción (1-4) o 'q' para salir: ").strip()
        
        if choice.lower() == 'q':
            break
        elif choice in ['1', '2', '3', '4']:
            execute_option(choice)
            break
        else:
            print("❌ Opción inválida")
    
    print("\n🎉 **¡Listo para entrenar modelos biométricos!**")
    print("📚 Consulta README.md para más información")

if __name__ == "__main__":
    main()