"""
Export Dataset from Database - OPTIMIZED VERSION

Extrae enrollments Y verificaciones desde la base de datos.
Maximiza aprovechamiento de datos: 3 enrollment + 9 verification audios.

Uso:
    python export_dataset_from_db.py --output evaluation/dataset/from_frontend_full
"""

import sys
import asyncio
import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict
import logging

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)


async def export_dataset_from_database(output_dir: Path, user_ids: List[str] = None):
    """
    Exporta dataset completo desde la base de datos.
    INCLUYE enrollment samples Y verification attempts.
    
    Args:
        output_dir: Directorio de salida
        user_ids: Lista de user_ids a exportar (None = todos)
    """
    from src.infrastructure.config.dependencies import get_db_pool
    from src.infrastructure.persistence.PostgresVoiceSignatureRepository import PostgresVoiceSignatureRepository
    from src.infrastructure.persistence.PostgresUserRepository import PostgresUserRepository
    
    # Crear directorios
    speakers_dir = output_dir / "speakers"
    speakers_dir.mkdir(parents=True, exist_ok=True)
    
    # Conectar a base de datos
    pool = await get_db_pool()
   voice_repo = PostgresVoiceSignatureRepository(pool)
    user_repo = PostgresUserRepository(pool)
    
    # Obtener usuarios
    if user_ids:
        users = []
        for user_id_str in user_ids:
            from uuid import UUID
            user = await user_repo.get_user_by_id(UUID(user_id_str))
            if user:
                users.append(user)
    else:
        # Obtener todos los usuarios con voiceprint
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT DISTINCT u.id, u.email
                FROM users u
                INNER JOIN voice_signatures vs ON vs.user_id = u.id
                ORDER BY u.created_at
            """)
            users = [{"id": row["id"], "email": row["email"]} for row in rows]
    
    logger.info(f"Found {len(users)} users with voiceprints")
    
    if len(users) == 0:
        print("❌ No users with voiceprints found!")
        print("💡 Tip: Register users via frontend and do enrollment first")
        return
    
    enrollment_config = {}
    genuine_config = {}
    impostor_config = {}
    
    total_enrollment = 0
    total_verification = 0
    
    for idx, user in enumerate(users, 1):
        user_id = user["id"] if isinstance(user, dict) else user.id
        email = user["email"] if isinstance(user, dict) else user.email
        
        speaker_id = f"speaker_{idx:03d}"
        speaker_dir = speakers_dir / speaker_id
        speaker_dir.mkdir(exist_ok=True)
        
        logger.info(f"Processing {speaker_id} ({email})...")
        
        # ===== ENROLLMENT SAMPLES (3 audios) =====
        async with pool.acquire() as conn:
            enrollment_samples = await conn.fetch("""
                SELECT id, embedding, created_at, snr_db, duration_sec
                FROM enrollment_samples
                WHERE user_id = $1
                ORDER BY created_at
                LIMIT 10
            """, user_id)
        
        if not enrollment_samples:
            logger.warning(f"  No enrollment samples found for {email}")
            continue
        
        # Usar primeros 3 para enrollment
        enrollment_paths = []
        for i, sample in enumerate(enrollment_samples[:3], 1):
            sample_file = speaker_dir / f"enroll_{i:02d}.json"
            sample_data = {
                "type": "enrollment",
                "sample_id": str(sample["id"]),
                "embedding_shape": [192],
                "snr_db": float(sample["snr_db"]) if sample["snr_db"] else None,
                "duration_sec": float(sample["duration_sec"]) if sample["duration_sec"] else None,
                "timestamp": sample["created_at"].isoformat()
            }
            with open(sample_file, 'w') as f:
                json.dump(sample_data, f, indent=2)
            
            enrollment_paths.append(f"speakers/{speaker_id}/enroll_{i:02d}.json")
            total_enrollment += 1
        
        enrollment_config[speaker_id] = enrollment_paths
        
        # ===== VERIFICATION ATTEMPTS (2-3 verificaciones × 3 audios cada una) =====
        # Buscar en audit_log las verificaciones multi-phrase completadas
        async with pool.acquire() as conn:
            verifications = await conn.fetch("""
                SELECT 
                    entity_id,
                    metadata,
                    timestamp,
                    success
                FROM audit_log
                WHERE actor = 'user'
                  AND action = 'VERIFICATION'
                  AND entity_type = 'multi_verification_complete'
                  AND metadata::jsonb->>'user_id' = $1
                ORDER BY timestamp DESC
                LIMIT 5
            """, str(user_id))
        
        genuine_paths = []
        verification_count = 0
        
        for ver_idx, verification in enumerate(verifications, 1):
            # Parsear metadata
            metadata = verification["metadata"]
            if isinstance(metadata, str):
                metadata = json.loads(metadata)
            
            # Cada verificación multi-phrase tiene 3 resultados (1 por frase)
            results = metadata.get("results", [])
            
            if len(results) < 3:
                continue  # Skip verificaciones incompletas
            
            verification_count += 1
            
            # Guardar cada uno de los 3 audios de esta verificación
            for phrase_idx, result in enumerate(results[:3], 1):
                sample_file = speaker_dir / f"verify_{ver_idx:02d}_phrase_{phrase_idx}.json"
                sample_data = {
                    "type": "verification",
                    "verification_id": str(verification["entity_id"]),
                    "verification_number": ver_idx,
                    "phrase_number": phrase_idx,
                    "similarity_score": result.get("similarity_score"),
                    "final_score": result.get("final_score"),
                    "asr_confidence": result.get("asr_confidence"),
                    "genuineness_score": result.get("genuineness_score"),
                    "timestamp": verification["timestamp"].isoformat(),
                    "was_accepted": verification["success"]
                }
                with open(sample_file, 'w') as f:
                    json.dump(sample_data, f, indent=2)
                
                genuine_paths.append(f"speakers/{speaker_id}/verify_{ver_idx:02d}_phrase_{phrase_idx}.json")
                total_verification += 1
        
        # También usar samples de enrollment restantes como genuine si no hay suficientes verificaciones
        if verification_count < 2:
            for i, sample in enumerate(enrollment_samples[3:6], 1):
                sample_file = speaker_dir / f"test_genuine_{i:02d}.json"
                sample_data = {
                    "type": "enrollment_extra",
                    "sample_id": str(sample["id"]),
                    "embedding_shape": [192],
                    "timestamp": sample["created_at"].isoformat()
                }
                with open(sample_file, 'w') as f:
                    json.dump(sample_data, f, indent=2)
                
                genuine_paths.append(f"speakers/{speaker_id}/test_genuine_{i:02d}.json")
        
        if genuine_paths:
            genuine_config[speaker_id] = genuine_paths
        
        logger.info(f"  ✓ {len(enrollment_paths)} enrollment + {len(genuine_paths)} genuine tests ({verification_count} verifications)")
    
    # Generar configuraciones de impostor (cross-speaker tests)
    speaker_ids = list(enrollment_config.keys())
    for i, speaker_id in enumerate(speaker_ids):
        impostor_config[speaker_id] = {}
        
        # Usar samples de otros speakers como impostores
        for other_speaker in speaker_ids[i+1:i+4]:  # Max 3 impostores por speaker
            if other_speaker in genuine_config and genuine_config[other_speaker]:
                # Usar algunos genuine tests del otro usuario como impostor attempts
                impostor_config[speaker_id][other_speaker] = genuine_config[other_speaker][:3]
    
    # Guardar configuración
    config = {
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "total_speakers": len(enrollment_config),
            "total_enrollment_samples": total_enrollment,
            "total_verification_samples": total_verification,
            "total_samples": total_enrollment + total_verification
        },
        "enrollment": enrollment_config,
        "genuine": genuine_config,
        "impostor": impostor_config
    }
    
    config_file = output_dir / "dataset_config.json"
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Dataset exported successfully!")
    logger.info(f"{'='*60}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Speakers: {len(enrollment_config)}")
    logger.info(f"Enrollment samples: {total_enrollment}")
    logger.info(f"Verification samples: {total_verification}")
    logger.info(f"Total samples: {total_enrollment + total_verification}")
    logger.info(f"Config file: {config_file}")
    logger.info(f"{'='*60}\n")
    
    print(f"\n✅ Dataset exported to: {output_dir}")
    print(f"📊 {len(enrollment_config)} speakers")
    print(f"📝 {total_enrollment} enrollment samples (3 per speaker)")
    print(f"🎯 {total_verification} verification samples (from multi-phrase verifications)")
    print(f"💾 Total: {total_enrollment + total_verification} samples")
    print(f"📄 Config: {config_file}")
    print(f"\n💡 Tip: With {len(enrollment_config)} speakers and ~{total_verification // max(len(enrollment_config), 1)} verifications/speaker")
    print(f"   you have {total_enrollment + total_verification} samples for evaluation!")
    print(f"\n🚀 Run evaluation with:")
    print(f"   python evaluation/scripts/evaluate_speaker_verification.py \\")
    print(f"       --dataset {output_dir} \\")
    print(f"       --config dataset_config.json \\")
    print(f"       --name from_frontend_full")


def main():
    parser = argparse.ArgumentParser(description="Export dataset from database (enrollment + verifications)")
    parser.add_argument("--output", type=str, default="evaluation/dataset/from_frontend",
                        help="Output directory for dataset")
    parser.add_argument("--users", type=str, nargs="+",
                        help="Specific user IDs to export (optional)")
    parser.add_argument("--verbose", action="store_true")
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    output_dir = Path(args.output)
    
    try:
        asyncio.run(export_dataset_from_database(output_dir, args.users))
    except Exception as e:
        logger.error(f"Export failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
