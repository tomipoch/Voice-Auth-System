#!/usr/bin/env python3
"""
Guía actualizada para descargar datasets académicos.
Los datasets requieren registro previo en las páginas oficiales.
"""

import os
from pathlib import Path

def show_dataset_registration_info():
    """Muestra información sobre cómo registrarse para descargar datasets."""
    
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
    
    print("⚠️ **IMPORTANTE:**")
    print("- Los datasets requieren uso académico únicamente")
    print("- Proporciona email institucional (.edu, .ac.uk, etc.)")
    print("- Menciona tu afiliación universitaria")
    print("- El proceso puede tomar 1-3 días laborables")
    print()
    
    print("🚀 **MIENTRAS TANTO - ALTERNATIVAS:**")
    print("1. 🧪 Continúa con datasets sintéticos")
    print("2. 📁 Usa subsets públicos más pequeños")
    print("3. 🔬 Implementa con datos propios de audio")
    print()

def create_manual_download_script():
    """Crea script para cuando tengas los enlaces oficiales."""
    
    script_content = '''#!/usr/bin/env python3
"""
Script para descargar datasets después de obtener URLs oficiales.
Reemplaza las URLs con las que recibas por email.
"""

import requests
import os
from pathlib import Path
from tqdm import tqdm

def download_with_auth(url, filename, auth_token=None):
    """Descarga archivo con autenticación si es necesaria."""
    
    headers = {}
    if auth_token:
        headers['Authorization'] = f'Bearer {auth_token}'
    
    response = requests.get(url, stream=True, headers=headers)
    response.raise_for_status()
    
    total_size = int(response.headers.get('content-length', 0))
    
    with open(filename, 'wb') as file, tqdm(
        desc=filename,
        total=total_size,
        unit='iB',
        unit_scale=True,
    ) as pbar:
        for chunk in response.iter_content(chunk_size=8192):
            size = file.write(chunk)
            pbar.update(size)

def main():
    """Descarga con URLs oficiales."""
    
    # Crear directorio de datasets
    datasets_dir = Path("../datasets/official")
    datasets_dir.mkdir(parents=True, exist_ok=True)
    
    print("📥 **DESCARGA CON URLs OFICIALES**")
    print("=" * 50)
    
    # REEMPLAZA ESTAS URLs CON LAS QUE RECIBAS POR EMAIL
    voxceleb_urls = {
        "vox1_dev": "URL_QUE_RECIBISTE_POR_EMAIL_1",
        "vox1_test": "URL_QUE_RECIBISTE_POR_EMAIL_2", 
        "vox1_meta": "URL_QUE_RECIBISTE_POR_EMAIL_3"
    }
    
    asvspoof_urls = {
        "la_train": "URL_ASVSPOOF_TRAIN",
        "la_dev": "URL_ASVSPOOF_DEV",
        "la_eval": "URL_ASVSPOOF_EVAL"
    }
    
    # Descargar VoxCeleb (si tienes URLs)
    for name, url in voxceleb_urls.items():
        if url != "URL_QUE_RECIBISTE_POR_EMAIL_1":  # Si reemplazaste la URL
            filename = datasets_dir / f"{name}.zip"
            print(f"Descargando {name}...")
            try:
                download_with_auth(url, filename)
                print(f"✅ {name} descargado")
            except Exception as e:
                print(f"❌ Error descargando {name}: {e}")
    
    # Descargar ASVspoof (si tienes URLs)
    for name, url in asvspoof_urls.items():
        if url != "URL_ASVSPOOF_TRAIN":  # Si reemplazaste la URL
            filename = datasets_dir / f"asvspoof_{name}.zip"
            print(f"Descargando ASVspoof {name}...")
            try:
                download_with_auth(url, filename)
                print(f"✅ ASVspoof {name} descargado")
            except Exception as e:
                print(f"❌ Error descargando {name}: {e}")
    
    print("\\n✅ **DESCARGA COMPLETADA**")
    print("🔧 **Siguiente paso:** python preprocess_official_datasets.py")

if __name__ == "__main__":
    main()
    '''
    
    script_path = Path("download_official_datasets.py")
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    print(f"📝 Script creado: {script_path}")
    print("🔧 Edita las URLs cuando las recibas por email")

def suggest_public_alternatives():
    """Sugiere alternativas públicas disponibles."""
    
    print("\n🌐 **ALTERNATIVAS PÚBLICAS DISPONIBLES:**")
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
    
    print("\n4. 📊 **Subsets públicos**")
    print("   - Versiones reducidas de VoxCeleb")
    print("   - Algunos papers publican subsets")
    print("   - Buscar en GitHub repositorios académicos")

def main():
    """Función principal."""
    
    show_dataset_registration_info()
    create_manual_download_script()
    suggest_public_alternatives()
    
    print("\n🎯 **RECOMENDACIÓN INMEDIATA:**")
    print("1. 📝 Registrarse ahora en las páginas oficiales")
    print("2. 🧪 Continuar desarrollo con datos sintéticos")
    print("3. 🔄 Volver a intentar descarga en 2-3 días")
    print("\n¿Quieres que creemos datasets sintéticos más realistas mientras tanto?")

if __name__ == "__main__":
    main()
'''