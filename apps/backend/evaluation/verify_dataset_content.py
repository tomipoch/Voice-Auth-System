"""
Verificador de Contenido del Dataset

Este script transcribe los audios de recordings y attacks para verificar
si los ataques TTS están diciendo las mismas frases que los recordings genuinos.

Uso:
    python verify_dataset_content.py
"""

import sys
import logging
from pathlib import Path
from typing import Dict, List, Tuple
import json
from datetime import datetime
import torch
import torchaudio

logger = logging.getLogger(__name__)


class DatasetVerifier:
    """Verificador de contenido del dataset."""
    
    def __init__(self, dataset_base: Path, models_dir: Path):
        self.dataset_base = dataset_base
        self.models_dir = models_dir
        
        # Cargar modelo ASR directamente desde local
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._load_asr_model()
        self.target_sample_rate = 16000
        
        # Rutas
        self.recordings_dir = dataset_base / "recordings" / "auto_recordings_20251218"
        self.attacks_dir = dataset_base / "attacks"
        self.cloning_dir = dataset_base / "cloning"
        
        # Usuarios
        self.users = [
            "anachamorromunoz",
            "ft_fernandotomas",
            "piapobletech",
            "rapomo3"
        ]
    
    def _load_asr_model(self):
        """Cargar modelo ASR desde directorio local."""
        try:
            from speechbrain.inference.ASR import EncoderASR
            
            asr_path = self.models_dir / "text-verification" / "lightweight_asr"
            
            logger.info(f"Cargando modelo ASR desde: {asr_path}")
            
            if not asr_path.exists():
                raise FileNotFoundError(f"Modelo ASR no encontrado en {asr_path}")
            
            # Cargar desde directorio local, sin descargar
            self.asr_model = EncoderASR.from_hparams(
                source=str(asr_path),
                savedir=str(asr_path),
                run_opts={"device": str(self.device)}
            )
            
            logger.info("Modelo ASR cargado exitosamente desde directorio local")
            
        except Exception as e:
            logger.error(f"Error cargando modelo ASR: {e}")
            raise
    
    def load_audio(self, audio_path: Path) -> torch.Tensor:
        """Cargar archivo de audio y convertir a tensor."""
        waveform, sample_rate = torchaudio.load(str(audio_path))
        
        # Convertir a mono si es stereo
        if waveform.shape[0] > 1:
            waveform = torch.mean(waveform, dim=0, keepdim=True)
        
        # Resamplear si es necesario
        if sample_rate != self.target_sample_rate:
            resampler = torchaudio.transforms.Resample(sample_rate, self.target_sample_rate)
            waveform = resampler(waveform)
        
        return waveform.squeeze(0)
    
    def transcribe_audio(self, audio_path: Path) -> str:
        """Transcribir un audio."""
        try:
            logger.debug(f"  Cargando audio: {audio_path.name}")
            waveform = self.load_audio(audio_path)
            
            logger.debug(f"  Waveform shape: {waveform.shape}, device: {self.device}")
            
            # Mover waveform al dispositivo correcto
            waveform = waveform.to(self.device)
            
            # Preparar batch
            batch = waveform.unsqueeze(0)
            wav_lens = torch.tensor([1.0]).to(self.device)
            
            logger.debug("  Transcribiendo con modelo ASR...")
            transcription = self.asr_model.transcribe_batch(batch, wav_lens)
            
            # transcribe_batch devuelve una lista de listas de tokens
            # Necesitamos unir los tokens en un string
            if transcription and len(transcription) > 0:
                tokens = transcription[0]
                if isinstance(tokens, list):
                    result = ' '.join(tokens).strip()
                else:
                    result = str(tokens).strip()
            else:
                result = ""
            
            logger.debug(f"  -> Resultado: '{result}'")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error transcribiendo {audio_path.name}: {e}", exc_info=True)
            return ""
    
    def transcribe_user_recordings(self, user: str) -> Dict[str, str]:
        """
        Transcribir todas las grabaciones de un usuario.
        
        Returns:
            Dict con formato {nombre_archivo: transcripcion}
        """
        logger.info(f"Transcribiendo recordings de {user}...")
        
        user_dir = self.recordings_dir / user
        if not user_dir.exists():
            logger.warning(f"No existe directorio: {user_dir}")
            return {}
        
        transcriptions = {}
        
        # Transcribir enrollment
        enrollment_files = sorted(user_dir.glob(f"{user}_enrollment_*.wav"))
        for audio_file in enrollment_files:
            logger.info(f"  Transcribiendo {audio_file.name}...")
            transcription = self.transcribe_audio(audio_file)
            transcriptions[audio_file.name] = transcription
        
        # Transcribir verification
        verification_files = sorted(user_dir.glob(f"{user}_verification_*.wav"))
        for audio_file in verification_files:
            logger.info(f"  Transcribiendo {audio_file.name}...")
            transcription = self.transcribe_audio(audio_file)
            transcriptions[audio_file.name] = transcription
        
        logger.info(f"  Total transcripciones: {len(transcriptions)}")
        return transcriptions
    
    def count_user_attacks(self, user: str) -> int:
        """
        Contar ataques TTS de un usuario (no se transcriben).
        
        Returns:
            Número de ataques TTS
        """
        logger.info(f"Contando ataques TTS de {user}...")
        
        user_dir = self.attacks_dir / user
        if not user_dir.exists():
            logger.warning(f"No existe directorio: {user_dir}")
            return 0
        
        attack_files = list(user_dir.glob(f"{user}_tts_attack_*.wav"))
        count = len(attack_files)
        
        logger.info(f"  Total ataques TTS: {count}")
        return count
    
    def transcribe_user_cloning(self, user: str) -> Dict[str, str]:
        """
        Transcribir todos los ataques de cloning de un usuario.
        
        Returns:
            Dict con formato {nombre_archivo: transcripcion}
        """
        logger.info(f"Transcribiendo ataques de cloning de {user}...")
        
        user_dir = self.cloning_dir / user
        if not user_dir.exists():
            logger.warning(f"No existe directorio: {user_dir}")
            return {}
        
        transcriptions = {}
        cloning_files = sorted(user_dir.glob("*.wav"))
        
        for audio_file in cloning_files:
            logger.info(f"  Transcribiendo {audio_file.name}...")
            transcription = self.transcribe_audio(audio_file)
            transcriptions[audio_file.name] = transcription
        
        logger.info(f"  Total transcripciones: {len(transcriptions)}")
        return transcriptions
    
    def analyze_recordings(self, recordings: Dict[str, str], num_attacks: int) -> Dict:
        """
        Analizar las grabaciones y extraer frases únicas.
        
        Returns:
            Dict con análisis de las grabaciones
        """
        # Extraer frases únicas de recordings
        unique_phrases = list(set(recordings.values()))
        
        # Contar cuántas veces aparece cada frase
        phrase_counts = {}
        for phrase in recordings.values():
            phrase_counts[phrase] = phrase_counts.get(phrase, 0) + 1
        
        return {
            'total_recordings': len(recordings),
            'total_attacks': num_attacks,
            'unique_phrases_count': len(unique_phrases),
            'unique_phrases': unique_phrases,
            'phrase_counts': phrase_counts,
            'needs_regeneration': True  # Siempre necesitaremos regenerar ataques TTS con las frases correctas
        }
    
    def generate_report(self, all_results: Dict, output_path: Path) -> None:
        """Generar reporte de verificación."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=" * 100 + "\n")
            f.write("REPORTE DE FRASES PARA REGENERAR ATAQUES TTS\n")
            f.write("=" * 100 + "\n\n")
            
            f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("OBJETIVO: Identificar las frases que deben usarse para regenerar los ataques TTS\n")
            f.write("Los ataques TTS deben decir las MISMAS frases que los recordings genuinos.\n\n")
            
            # Resumen por usuario
            for user, results in all_results.items():
                f.write("=" * 100 + "\n")
                f.write(f"USUARIO: {user}\n")
                f.write("=" * 100 + "\n\n")
                
                analysis = results['analysis']
                recordings = results['recordings']
                
                f.write("ESTADÍSTICAS:\n")
                f.write("-" * 100 + "\n")
                f.write(f"Total recordings:           {analysis['total_recordings']}\n")
                f.write(f"Total ataques TTS actuales: {analysis['total_attacks']}\n")
                f.write(f"Frases únicas encontradas:  {analysis['unique_phrases_count']}\n\n")
                
                # Frases únicas encontradas
                f.write("FRASES ÚNICAS EN RECORDINGS (usar para TTS):\n")
                f.write("-" * 100 + "\n")
                for i, phrase in enumerate(analysis['unique_phrases'], 1):
                    count = analysis['phrase_counts'][phrase]
                    f.write(f"{i}. \"{phrase}\" (aparece {count} veces)\n")
                f.write("\n")
                
                # Detalle de cada recording
                f.write("DETALLE DE RECORDINGS:\n")
                f.write("-" * 100 + "\n")
                for filename, transcription in sorted(recordings.items()):
                    f.write(f"{filename}\n")
                    f.write(f"  -> \"{transcription}\"\n\n")
                
                # Análisis de cloning (si existe)
                if 'cloning' in results and results['cloning']:
                    f.write("ATAQUES DE CLONING:\n")
                    f.write("-" * 100 + "\n")
                    for filename, transcription in sorted(results['cloning'].items()):
                        f.write(f"{filename}\n")
                        f.write(f"  -> \"{transcription}\"\n\n")
                
                f.write("\n")
            
            # Resumen global
            f.write("=" * 100 + "\n")
            f.write("RESUMEN GLOBAL Y RECOMENDACIONES\n")
            f.write("=" * 100 + "\n\n")
            
            total_recordings = sum(r['analysis']['total_recordings'] for r in all_results.values())
            total_attacks = sum(r['analysis']['total_attacks'] for r in all_results.values())
            total_unique_phrases = sum(r['analysis']['unique_phrases_count'] for r in all_results.values())
            
            f.write(f"Total recordings en dataset:     {total_recordings}\n")
            f.write(f"Total ataques TTS actuales:      {total_attacks}\n")
            f.write(f"Total frases únicas identificadas: {total_unique_phrases}\n\n")
            
            f.write("PLAN DE ACCIÓN:\n")
            f.write("-" * 100 + "\n")
            f.write("1. REGENERAR ATAQUES TTS:\n")
            f.write("   - Eliminar los 15 archivos TTS actuales de cada usuario\n")
            f.write("   - Generar nuevos ataques TTS usando las frases únicas identificadas arriba\n")
            f.write("   - Cada frase debe usarse aproximadamente el mismo número de veces\n")
            f.write(f"   - Total a generar: {total_attacks} ataques TTS ({total_attacks // 4} por usuario)\n\n")
            
            f.write("2. DISTRIBUCIÓN SUGERIDA:\n")
            for user, results in all_results.items():
                analysis = results['analysis']
                attacks_per_phrase = analysis['total_attacks'] // analysis['unique_phrases_count']
                f.write(f"   {user}:\n")
                for i, phrase in enumerate(analysis['unique_phrases'], 1):
                    f.write(f"     - Frase {i}: {attacks_per_phrase} ataques TTS\n")
                f.write("\n")
            
            f.write("3. VALIDACIÓN POSTERIOR:\n")
            f.write("   - Volver a ejecutar este script después de regenerar\n")
            f.write("   - Verificar que todos los ataques TTS transcriben correctamente\n")
        
        logger.info(f"Reporte generado: {output_path}")
        
        # Guardar JSON
        json_path = output_path.with_suffix('.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        logger.info(f"JSON generado: {json_path}")


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 100)
    print("VERIFICACIÓN DE CONTENIDO DEL DATASET")
    print("=" * 100)
    print()
    
    # Configuración
    project_root = Path(__file__).parent.parent.parent.parent
    dataset_base = project_root / "infra" / "evaluation" / "dataset"
    models_dir = project_root / "apps" / "backend" / "models"
    
    if not dataset_base.exists():
        print(f"❌ Error: Dataset no encontrado en {dataset_base}")
        sys.exit(1)
    
    if not models_dir.exists():
        print(f"❌ Error: Directorio de modelos no encontrado en {models_dir}")
        sys.exit(1)
    
    # Inicializar verificador
    verifier = DatasetVerifier(dataset_base, models_dir)
    
    # Verificar todos los usuarios
    all_results = {}
    
    for user in verifier.users:
        print(f"\n{'='*100}")
        print(f"Procesando usuario: {user}")
        print(f"{'='*100}\n")
        
        # Transcribir solo recordings (genuinos)
        recordings = verifier.transcribe_user_recordings(user)
        
        # Contar ataques TTS (no transcribir)
        num_attacks = verifier.count_user_attacks(user)
        
        # Transcribir cloning (si existe)
        cloning = verifier.transcribe_user_cloning(user)
        
        # Analizar
        analysis = verifier.analyze_recordings(recordings, num_attacks)
        
        all_results[user] = {
            'recordings': recordings,
            'num_attacks': num_attacks,
            'cloning': cloning,
            'analysis': analysis
        }
        
        # Mostrar resumen
        print(f"\n📊 Resumen para {user}:")
        print(f"  Recordings transcritos: {len(recordings)}")
        print(f"  Ataques TTS (sin transcribir): {num_attacks}")
        print(f"  Frases únicas encontradas: {analysis['unique_phrases_count']}")
        if cloning:
            print(f"  Cloning attacks transcritos: {len(cloning)}")
    
    # Generar reporte
    output_path = Path(__file__).parent / "results" / "dataset_verification_report.txt"
    verifier.generate_report(all_results, output_path)
    
    print(f"\n{'='*100}")
    print("VERIFICACIÓN COMPLETA")
    print(f"{'='*100}")
    print(f"\nReporte: {output_path}")
    print(f"JSON: {output_path.with_suffix('.json')}")


if __name__ == "__main__":
    main()
