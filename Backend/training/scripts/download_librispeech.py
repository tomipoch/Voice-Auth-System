#!/usr/bin/env python3
"""
Descargador para LibriSpeech - dataset público sin restricciones.
"""

import requests
import os
from pathlib import Path
from tqdm import tqdm
import tarfile

def download_librispeech():
    """Descarga LibriSpeech dataset público."""
    
    print("📚 **DESCARGANDO LIBRISPEECH (PÚBLICO)**")
    print("=" * 50)
    
    # URLs públicas de LibriSpeech
    librispeech_urls = {
        "train-clean-100": "http://www.openslr.org/resources/12/train-clean-100.tar.gz",
        "dev-clean": "http://www.openslr.org/resources/12/dev-clean.tar.gz", 
        "test-clean": "http://www.openslr.org/resources/12/test-clean.tar.gz"
    }
    
    sizes = {
        "train-clean-100": "6.3 GB",
        "dev-clean": "337 MB",
        "test-clean": "346 MB"
    }
    
    # Crear directorio
    output_dir = Path("../datasets/librispeech")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("📦 Archivos a descargar:")
    for name, size in sizes.items():
        print(f"   - {name}: {size}")
    
    confirm = input("\n¿Descargar LibriSpeech? (y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ Descarga cancelada")
        return
    
    # Descargar archivos
    for name, url in librispeech_urls.items():
        filename = output_dir / f"{name}.tar.gz"
        
        if filename.exists():
            print(f"⏭️  {name} ya existe, saltando...")
            continue
            
        print(f"⬇️  Descargando {name} ({sizes[name]})...")
        
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(filename, 'wb') as file, tqdm(
                desc=name,
                total=total_size,
                unit='iB',
                unit_scale=True,
            ) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    size = file.write(chunk)
                    pbar.update(size)
            
            print(f"✅ {name} descargado")
            
            # Extraer archivo
            print(f"📂 Extrayendo {name}...")
            with tarfile.open(filename, 'r:gz') as tar:
                tar.extractall(output_dir)
            print(f"✅ {name} extraído")
            
        except Exception as e:
            print(f"❌ Error descargando {name}: {e}")
    
    print(f"\n✅ **LIBRISPEECH DESCARGADO**")
    print(f"📁 Ubicación: {output_dir}")
    print("🔧 Siguiente paso: python preprocess_audio.py --dataset librispeech")

if __name__ == "__main__":
    download_librispeech()