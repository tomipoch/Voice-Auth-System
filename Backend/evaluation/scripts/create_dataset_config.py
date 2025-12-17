"""
Create Dataset Config from Directory

Escanea una carpeta con audios organizados por speaker y
genera automáticamente el dataset_config.json.

Uso:
    python create_dataset_config.py --input evaluation/dataset/manual_recordings
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


def scan_directory_for_audios(base_dir: Path) -> tuple:
    """
    Escanea directorio y organiza audios por speaker.
    
    Estructura esperada:
        base_dir/
        ├── speaker_001/
        │   ├── enroll_01.wav
        │   ├── verify_01_phrase_1.wav
        │   └── ...
        └── speaker_002/
            └── ...
    
    Returns:
        (enrollment_config, genuine_config, impostor_config)
    """
    enrollment_config = {}
    genuine_config = {}
    impostor_config = {}
    
    # Buscar carpetas de speakers
    speaker_dirs = sorted([d for d in base_dir.iterdir() if d.is_dir() and d.name.startswith('speaker')])
    
    logger.info(f"Found {len(speaker_dirs)} speaker directories")
    
    for speaker_dir in speaker_dirs:
        speaker_id = speaker_dir.name
        
        # Buscar archivos de enrollment
        enroll_files = sorted(speaker_dir.glob("enroll_*.wav"))
        if enroll_files:
            enrollment_config[speaker_id] = [
                f"{speaker_id}/{f.name}" for f in enroll_files
            ]
        
        # Buscar archivos de verificación y otros tests
        verify_files = sorted(speaker_dir.glob("verify_*.wav"))
        test_files = sorted(speaker_dir.glob("test_*.wav"))
        
        all_genuine = verify_files + test_files
        if all_genuine:
            genuine_config[speaker_id] = [
                f"{speaker_id}/{f.name}" for f in all_genuine
            ]
        
        logger.info(f"  {speaker_id}: {len(enrollment_config.get(speaker_id, []))} enrollment, {len(genuine_config.get(speaker_id, []))} genuine")
    
    # Generar tests impostores (cross-speaker)
    speaker_ids = list(enrollment_config.keys())
    for i, speaker_id in enumerate(speaker_ids):
        impostor_config[speaker_id] = {}
        
        # Usar genuine tests de otros speakers como impostores
        for other_speaker in speaker_ids[i+1:i+4]:  # Max 3 impostores
            if other_speaker in genuine_config and genuine_config[other_speaker]:
                impostor_config[speaker_id][other_speaker] = genuine_config[other_speaker][:3]
    
    return enrollment_config, genuine_config, impostor_config


def create_config(input_dir: Path, output_file: Path = None):
    """
    Crea dataset_config.json desde directorio con audios.
    
    Args:
        input_dir: Directorio con speakers/
        output_file: Archivo de salida (default: input_dir/dataset_config.json)
    """
    if not input_dir.exists():
        raise FileNotFoundError(f"Directory not found: {input_dir}")
    
    logger.info(f"Scanning directory: {input_dir}")
    
    enrollment_config, genuine_config, impostor_config = scan_directory_for_audios(input_dir)
    
    # Crear configuración completa
    config = {
        "metadata": {
            "source_directory": str(input_dir),
            "total_speakers": len(enrollment_config),
            "total_enrollment_files": sum(len(files) for files in enrollment_config.values()),
            "total_genuine_files": sum(len(files) for files in genuine_config.values())
        },
        "enrollment": enrollment_config,
        "genuine": genuine_config,
        "impostor": impostor_config
    }
    
    # Guardar
    if output_file is None:
        output_file = input_dir / "dataset_config.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Config created successfully!")
    logger.info(f"{'='*60}")
    logger.info(f"Output file: {output_file}")
    logger.info(f"Speakers: {len(enrollment_config)}")
    logger.info(f"Enrollment files: {config['metadata']['total_enrollment_files']}")
    logger.info(f"Genuine test files: {config['metadata']['total_genuine_files']}")
    logger.info(f"{'='*60}\n")
    
    print(f"\n✅ Config created: {output_file}")
    print(f"📊 {len(enrollment_config)} speakers")
    print(f"📁 {config['metadata']['total_enrollment_files']} enrollment files")
    print(f"🎯 {config['metadata']['total_genuine_files']} genuine test files")
    print(f"\n🚀 Run evaluation with:")
    print(f"   python evaluation/scripts/evaluate_speaker_verification.py \\")
    print(f"       --dataset {input_dir} \\")
    print(f"       --config dataset_config.json \\")
    print(f"       --name manual_dataset_v1")


def main():
    parser = argparse.ArgumentParser(description="Create dataset config from directory")
    parser.add_argument("--input", type=str, required=True,
                        help="Input directory with speaker folders")
    parser.add_argument("--output", type=str, default=None,
                        help="Output config file (default: input_dir/dataset_config.json)")
    parser.add_argument("--verbose", action="store_true")
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(levelname)s: %(message)s'
    )
    
    input_dir = Path(args.input)
    output_file = Path(args.output) if args.output else None
    
    try:
        create_config(input_dir, output_file)
    except Exception as e:
        logger.error(f"Failed to create config: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
