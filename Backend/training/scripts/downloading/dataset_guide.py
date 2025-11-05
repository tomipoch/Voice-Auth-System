#!/usr/bin/env python3
"""
Guía para registro y descarga de datasets académicos reales.
"""

def show_registration_info():
    """Muestra información sobre registro para datasets."""
    
    print("🎓 **DESCARGA DE DATASETS ACADÉMICOS - GUÍA OFICIAL**")
    print("=" * 70)
    print()
    
    print("📢 **VOXCELEB (Speaker Recognition)**")
    print("🌐 Página oficial: http://www.robots.ox.ac.uk/~vgg/data/voxceleb/")
    print("📝 Pasos:")
    print("   1. Ir a la página oficial")
    print("   2. Rellenar formulario de registro académico")
    print("   3. Proporcionar información institucional")
    print("   4. Recibir enlaces de descarga por email")
    print("📦 Archivos necesarios:")
    print("   - vox1_dev_wav.zip (Training set)")
    print("   - vox1_test_wav.zip (Test set)")
    print("   - vox1_meta.csv (Metadata)")
    print("💾 Tamaño total: ~25 GB")
    print()
    
    print("🛡️ **ASVSPOOF (Anti-Spoofing)**")
    print("🌐 Página oficial: https://www.asvspoof.org/")
    print("📝 Pasos:")
    print("   1. Ir a https://www.asvspoof.org/database")
    print("   2. Registrarse con datos académicos")
    print("   3. Aceptar términos de uso")
    print("   4. Descargar datasets de ASVspoof 2019 y 2021")
    print("📦 Archivos necesarios:")
    print("   - ASVspoof2019_LA_train.zip")
    print("   - ASVspoof2019_LA_dev.zip") 
    print("   - ASVspoof2019_LA_eval.zip")
    print("   - ASVspoof2021_LA_eval.zip")
    print("💾 Tamaño total: ~20 GB")
    print()
    
    print("📚 **LIBRISPEECH (ASR - Opcional)**")
    print("🌐 Página oficial: http://www.openslr.org/12/")
    print("📝 Disponible sin registro")
    print("📦 Archivos recomendados:")
    print("   - train-clean-100.tar.gz (6.3 GB)")
    print("   - dev-clean.tar.gz (337 MB)")
    print("   - test-clean.tar.gz (346 MB)")
    print()

def show_alternatives():
    """Muestra alternativas públicas."""
    
    print("🌐 **ALTERNATIVAS PÚBLICAS DISPONIBLES:**")
    print("=" * 50)
    
    print("1. 📚 **LibriSpeech (ASR)**")
    print("   - Disponible sin registro")
    print("   - http://www.openslr.org/12/")
    print("   - Útil para entrenar ASR ligero")
    
    print("\n2. 🎤 **Mozilla Common Voice**")
    print("   - Dataset público multilingüe")
    print("   - https://commonvoice.mozilla.org/")
    print("   - Incluye español")
    
    print("\n3. 🧪 **Datasets sintéticos mejorados**")
    print("   - Podemos crear datasets más realistas")
    print("   - Simular diferentes condiciones acústicas")
    print("   - Útil para desarrollo y pruebas")

def main():
    """Función principal."""
    
    show_registration_info()
    
    print("⚠️ **IMPORTANTE:**")
    print("- Los datasets requieren uso académico únicamente")
    print("- Proporciona email institucional (.edu, .ac.uk, etc.)")
    print("- Menciona tu afiliación universitaria")
    print("- El proceso puede tomar 1-3 días laborables")
    print()
    
    show_alternatives()
    
    print("\n🎯 **RECOMENDACIÓN INMEDIATA:**")
    print("1. 📝 Registrarse ahora en las páginas oficiales")
    print("2. 🧪 Continuar desarrollo con datos sintéticos")
    print("3. 🔄 Volver a intentar descarga en 2-3 días")
    print()
    print("🚀 **Mientras tanto, podemos:**")
    print("   - Crear datasets sintéticos más realistas")
    print("   - Descargar LibriSpeech (público)")
    print("   - Entrenar con datos actuales")

if __name__ == "__main__":
    main()