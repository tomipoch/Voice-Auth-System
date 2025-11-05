#!/usr/bin/env python3
"""
Script para descargar y configurar datasets académicos para entrenamiento de modelos biométricos.

Datasets soportados:
- VoxCeleb1: Para entrenamiento de ECAPA-TDNN y x-vector
- VoxCeleb2: Extensión del dataset para más diversidad
- ASVspoof 2019: Para modelos anti-spoofing (AASIST, RawNet2)
- ASVspoof 2021: Datos más recientes de spoofing
"""

import os
import sys
import requests
import hashlib
import zipfile
import tarfile
from pathlib import Path
from typing import Dict, Optional, Tuple
import logging
from tqdm import tqdm

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatasetDownloader:
    """Maneja la descarga y verificación de datasets académicos."""
    
    def __init__(self, base_path: str = "./datasets"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # URLs y checksums de datasets
        self.datasets_info = {
            "voxceleb1": {
                "urls": {
                    "dev": "https://thor.robots.ox.ac.uk/~vgg/data/voxceleb/vox1a/vox1_dev_wav.zip",
                    "test": "https://thor.robots.ox.ac.uk/~vgg/data/voxceleb/vox1a/vox1_test_wav.zip",
                    "meta": "https://thor.robots.ox.ac.uk/~vgg/data/voxceleb/meta/vox1_meta.csv"
                },
                "description": "VoxCeleb1 dataset for speaker recognition",
                "size_gb": 25,
                "samples": 153516
            },
            "voxceleb2": {
                "urls": {
                    "dev": "https://thor.robots.ox.ac.uk/~vgg/data/voxceleb/vox2a/vox2_dev_aac.zip",
                    "test": "https://thor.robots.ox.ac.uk/~vgg/data/voxceleb/vox2a/vox2_test_aac.zip",
                    "meta": "https://thor.robots.ox.ac.uk/~vgg/data/voxceleb/meta/vox2_meta.csv"
                },
                "description": "VoxCeleb2 extended dataset",
                "size_gb": 87,
                "samples": 1092009
            },
            "asvspoof2019": {
                "urls": {
                    "la_train": "https://datashare.ed.ac.uk/bitstream/handle/10283/3336/LA.zip",
                    "la_dev": "https://datashare.ed.ac.uk/bitstream/handle/10283/3336/LA.zip",
                    "pa_train": "https://datashare.ed.ac.uk/bitstream/handle/10283/3336/PA.zip"
                },
                "description": "ASVspoof 2019 for anti-spoofing training",
                "size_gb": 12,
                "samples": 54000
            },
            "asvspoof2021": {
                "urls": {
                    "la_eval": "https://zenodo.org/record/4837263/files/ASVspoof2021_LA_eval.tar.bz2",
                    "df_eval": "https://zenodo.org/record/4837263/files/ASVspoof2021_DF_eval.tar.bz2"
                },
                "description": "ASVspoof 2021 evaluation sets",
                "size_gb": 8,
                "samples": 200000
            }
        }
    
    def download_file(self, url: str, destination: Path, chunk_size: int = 8192) -> bool:
        """Descarga un archivo con barra de progreso."""
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(destination, 'wb') as file, tqdm(
                desc=destination.name,
                total=total_size,
                unit='iB',
                unit_scale=True,
                unit_divisor=1024,
            ) as pbar:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    size = file.write(chunk)
                    pbar.update(size)
            
            logger.info(f"Downloaded: {destination}")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading {url}: {e}")
            return False
    
    def verify_checksum(self, file_path: Path, expected_hash: str) -> bool:
        """Verifica la integridad del archivo descargado."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        calculated_hash = sha256_hash.hexdigest()
        return calculated_hash == expected_hash
    
    def extract_archive(self, archive_path: Path, extract_to: Path) -> bool:
        """Extrae archivos comprimidos."""
        try:
            extract_to.mkdir(parents=True, exist_ok=True)
            
            if archive_path.suffix == '.zip':
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_to)
            elif archive_path.suffix in ['.tar', '.bz2', '.gz']:
                with tarfile.open(archive_path, 'r:*') as tar_ref:
                    tar_ref.extractall(extract_to)
            else:
                logger.error(f"Unsupported archive format: {archive_path.suffix}")
                return False
            
            logger.info(f"Extracted: {archive_path} -> {extract_to}")
            return True
            
        except Exception as e:
            logger.error(f"Error extracting {archive_path}: {e}")
            return False
    
    def download_dataset(self, dataset_name: str, subset: Optional[str] = None) -> bool:
        """Descarga un dataset específico."""
        if dataset_name not in self.datasets_info:
            logger.error(f"Unknown dataset: {dataset_name}")
            return False
        
        dataset_info = self.datasets_info[dataset_name]
        dataset_path = self.base_path / dataset_name
        dataset_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Downloading {dataset_name}: {dataset_info['description']}")
        logger.info(f"Expected size: ~{dataset_info['size_gb']} GB")
        
        success = True
        for name, url in dataset_info["urls"].items():
            if subset and name != subset:
                continue
                
            filename = url.split('/')[-1]
            file_path = dataset_path / filename
            
            # Skip if already downloaded
            if file_path.exists():
                logger.info(f"File already exists: {file_path}")
                continue
            
            if not self.download_file(url, file_path):
                success = False
                continue
            
            # Extract if it's an archive
            if filename.endswith(('.zip', '.tar', '.bz2', '.gz')):
                extract_path = dataset_path / name
                if not self.extract_archive(file_path, extract_path):
                    success = False
        
        return success
    
    def list_available_datasets(self):
        """Lista todos los datasets disponibles."""
        print("\n📊 **DATASETS DISPONIBLES PARA ENTRENAMIENTO:**")
        print("=" * 60)
        
        for name, info in self.datasets_info.items():
            print(f"\n🎯 **{name.upper()}**")
            print(f"   Descripción: {info['description']}")
            print(f"   Tamaño: ~{info['size_gb']} GB")
            print(f"   Muestras: {info['samples']:,}")
            print(f"   Subsets disponibles: {', '.join(info['urls'].keys())}")
    
    def check_dataset_status(self, dataset_name: str) -> Dict[str, bool]:
        """Verifica el estado de descarga de un dataset."""
        if dataset_name not in self.datasets_info:
            return {}
        
        dataset_path = self.base_path / dataset_name
        status = {}
        
        for subset_name in self.datasets_info[dataset_name]["urls"].keys():
            subset_path = dataset_path / subset_name
            status[subset_name] = subset_path.exists() and any(subset_path.iterdir())
        
        return status
    
    def get_dataset_stats(self, dataset_name: str) -> Dict:
        """Obtiene estadísticas del dataset descargado."""
        dataset_path = self.base_path / dataset_name
        if not dataset_path.exists():
            return {"status": "not_downloaded"}
        
        stats = {
            "status": "downloaded",
            "size_mb": sum(f.stat().st_size for f in dataset_path.rglob('*') if f.is_file()) / (1024*1024),
            "files_count": len(list(dataset_path.rglob('*.wav'))) + len(list(dataset_path.rglob('*.flac'))),
            "path": str(dataset_path)
        }
        
        return stats

def main():
    """Función principal para descarga interactiva."""
    downloader = DatasetDownloader()
    
    print("🎵 **DESCARGADOR DE DATASETS BIOMÉTRICOS** 🎵")
    downloader.list_available_datasets()
    
    _show_menu_options()
    
    while True:
        choice = input("\nSelecciona una opción (0-6): ").strip()
        
        if choice == "0":
            break
        else:
            _handle_menu_choice(choice, downloader)

def _show_menu_options():
    """Muestra las opciones del menú principal."""
    print("\n📋 **OPCIONES:**")
    print("1. Descargar VoxCeleb1 (recomendado para empezar)")
    print("2. Descargar VoxCeleb2 (dataset extendido)")
    print("3. Descargar ASVspoof 2019 (anti-spoofing)")
    print("4. Descargar ASVspoof 2021 (anti-spoofing reciente)")
    print("5. Descargar todos los datasets")
    print("6. Verificar estado de datasets")
    print("0. Salir")

def _handle_menu_choice(choice: str, downloader: DatasetDownloader):
    """Maneja la opción seleccionada del menú."""
    choice_handlers = {
        "1": lambda: downloader.download_dataset("voxceleb1"),
        "2": lambda: downloader.download_dataset("voxceleb2"),
        "3": lambda: downloader.download_dataset("asvspoof2019"),
        "4": lambda: downloader.download_dataset("asvspoof2021"),
        "5": lambda: _handle_download_all(downloader),
        "6": lambda: _handle_check_status(downloader)
    }
    
    handler = choice_handlers.get(choice)
    if handler:
        handler()
    else:
        print("Opción inválida")

def _handle_download_all(downloader: DatasetDownloader):
    """Maneja la descarga de todos los datasets."""
    print("⚠️  ADVERTENCIA: Esto descargará ~132 GB de datos")
    confirm = input("¿Continuar? (y/N): ").strip().lower()
    if confirm == 'y':
        for dataset in downloader.datasets_info.keys():
            downloader.download_dataset(dataset)

def _handle_check_status(downloader: DatasetDownloader):
    """Maneja la verificación del estado de datasets."""
    print("\n📊 **ESTADO DE DATASETS:**")
    for dataset in downloader.datasets_info.keys():
        _ = downloader.check_dataset_status(dataset)
        stats = downloader.get_dataset_stats(dataset)
        print(f"\n{dataset.upper()}:")
        print(f"  Estado: {stats.get('status', 'unknown')}")
        if stats.get('status') == 'downloaded':
            print(f"  Tamaño: {stats['size_mb']:.1f} MB")
            print(f"  Archivos de audio: {stats['files_count']}")

if __name__ == "__main__":
    main()