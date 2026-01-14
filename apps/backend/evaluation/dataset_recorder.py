"""
Dataset Audio Recorder

Guarda audios originales cuando el modo de grabación de dataset está activo.
Se integra con enrollment y verification para capturar audios automáticamente.

Uso:
    from evaluation.dataset_recorder import dataset_recorder
    
    # Activar grabación
    dataset_recorder.start_recording("mini_dataset_v1")
    
    # Los audios se guardan automáticamente durante enrollment/verification
    
    # Detener grabación
    dataset_recorder.stop_recording()
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
from threading import Lock
import wave
import numpy as np

logger = logging.getLogger(__name__)


class DatasetRecorder:
    """
    Singleton recorder para guardar audios durante evaluación.
    
    Cuando está activo, guarda automáticamente los audios de
    enrollment y verification en estructura de dataset.
    """
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.base_dir = Path(__file__).parent / "dataset" / "recordings"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        self.enabled = False
        self.current_session = None
        self.session_dir = None
        self.user_counters = {}  # user_id -> {"enrollment": count, "verification": count}
        
        self._initialized = True
        logger.info("DatasetRecorder initialized")
    
    def start_recording(self, session_name: str) -> str:
        """
        Inicia grabación de dataset.
        
        Args:
            session_name: Nombre de la sesión de grabación
            
        Returns:
            Session ID
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_id = f"{session_name}_{timestamp}"
        
        self.current_session = session_id
        self.session_dir = self.base_dir / session_id
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
        self.enabled = True
        self.user_counters = {}
        
        logger.info(f"Started dataset recording: {session_id}")
        logger.info(f"Audios will be saved to: {self.session_dir}")
        
        return session_id
    
    def stop_recording(self) -> Optional[Path]:
        """Detiene grabación de dataset."""
        if not self.enabled:
            return None
        
        session_dir = self.session_dir
        self.enabled = False
        self.current_session = None
        self.session_dir = None
        
        logger.info(f"Stopped dataset recording")
        return session_dir
    
    def _get_user_dir(self, user_id: str, user_email: Optional[str] = None) -> tuple:
        """
        Obtiene directorio del usuario y nombre base, creándolo si no existe.
        
        Returns:
            (user_dir, username_base)
        """
        if user_id not in self.user_counters:
            # Crear nombre legible desde email o usar speaker_XXX
            if user_email:
                # Usar parte antes del @ como nombre
                username = user_email.split('@')[0].replace('.', '_').replace('-', '_')
            else:
                # Fallback a speaker número
                username = f"speaker_{len(self.user_counters) + 1:03d}"
            
            self.user_counters[user_id] = {
                "username": username,
                "email": user_email,
                "enrollment": 0,
                "verification": 0
            }
        
        username = self.user_counters[user_id]["username"]
        user_dir = self.session_dir / username
        user_dir.mkdir(exist_ok=True)
        
        return user_dir, username
    
    def save_enrollment_audio(
        self,
        user_id: str,
        audio_data: bytes,
        user_email: Optional[str] = None,
        sample_number: Optional[int] = None
    ) -> Optional[Path]:
        """
        Guarda audio de enrollment.
        
        Args:
            user_id: ID del usuario
            audio_data: Datos de audio (WAV bytes)
            user_email: Email del usuario (para nombre de carpeta)
            sample_number: Número de sample (opcional, se auto-incrementa)
            
        Returns:
            Path al archivo guardado o None si recording está desactivado
        """
        if not self.enabled:
            return None
        
        try:
            user_dir, username = self._get_user_dir(user_id, user_email)
            
            # Auto-incrementar contador
            self.user_counters[user_id]["enrollment"] += 1
            num = sample_number or self.user_counters[user_id]["enrollment"]
            
            # Guardar archivo con nombre legible
            filename = f"{username}_enrollment_{num:02d}.wav"
            filepath = user_dir / filename
            
            with open(filepath, 'wb') as f:
                f.write(audio_data)
            
            logger.debug(f"Saved enrollment audio: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to save enrollment audio: {e}")
            return None
    
    def save_verification_audio(
        self,
        user_id: str,
        audio_data: bytes,
        user_email: Optional[str] = None,
        verification_number: Optional[int] = None,
        phrase_number: Optional[int] = None
    ) -> Optional[Path]:
        """
        Guarda audio de verification.
        
        Args:
            user_id: ID del usuario
            audio_data: Datos de audio (WAV bytes)
            user_email: Email del usuario (para nombre de carpeta)
            verification_number: Número de verificación
            phrase_number: Número de frase dentro de la verificación
            
        Returns:
            Path al archivo guardado o None si recording está desactivado
        """
        if not self.enabled:
            return None
        
        try:
            user_dir, username = self._get_user_dir(user_id, user_email)
            
            # Auto-incrementar contador
            self.user_counters[user_id]["verification"] += 1
            
            # Determinar nombre de archivo con username
            if verification_number and phrase_number:
                filename = f"{username}_verification_{verification_number:02d}_phrase_{phrase_number}.wav"
            else:
                num = self.user_counters[user_id]["verification"]
                filename = f"{username}_verification_{num:02d}.wav"
            
            filepath = user_dir / filename
            
            with open(filepath, 'wb') as f:
                f.write(audio_data)
            
            logger.debug(f"Saved verification audio: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to save verification audio: {e}")
            return None
    
    def get_session_summary(self) -> dict:
        """Obtiene resumen de la sesión actual."""
        if not self.enabled:
            return {"enabled": False}
        
        total_enrollment = sum(c["enrollment"] for c in self.user_counters.values())
        total_verification = sum(c["verification"] for c in self.user_counters.values())
        
        return {
            "enabled": True,
            "session_id": self.current_session,
            "session_dir": str(self.session_dir),
            "total_users": len(self.user_counters),
            "total_enrollment_audios": total_enrollment,
            "total_verification_audios": total_verification,
            "users": {
                user_id: {
                    "username": info["username"],
                    "email": info.get("email", "N/A"),
                    "enrollment_count": info["enrollment"],
                    "verification_count": info["verification"]
                }
                for user_id, info in self.user_counters.items()
            }
        }


# Global singleton instance
dataset_recorder = DatasetRecorder()


# Convenience functions
def start_dataset_recording(session_name: str) -> str:
    """Inicia grabación de dataset."""
    return dataset_recorder.start_recording(session_name)


def stop_dataset_recording() -> Optional[Path]:
    """Detiene grabación de dataset."""
    return dataset_recorder.stop_recording()


if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.INFO)
    
    # Start recording
    session_id = dataset_recorder.start_recording("test_session")
    print(f"Started: {session_id}")
    
    # Simulate saving audios
    dummy_audio = b"RIFF" + b"\x00" * 1000  # Dummy WAV
    
    dataset_recorder.save_enrollment_audio("user_001", dummy_audio)
    dataset_recorder.save_enrollment_audio("user_001", dummy_audio)
    dataset_recorder.save_verification_audio("user_001", dummy_audio, 1, 1)
    
    # Summary
    summary = dataset_recorder.get_session_summary()
    print(f"\nSummary: {summary}")
    
    # Stop
    stopped_dir = dataset_recorder.stop_recording()
    print(f"\nStopped: {stopped_dir}")
