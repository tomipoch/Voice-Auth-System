"""
Evaluation Logger

Logger para sesiones de evaluación del sistema biométrico.
Registra eventos de enrollment y verification para análisis posterior.

Uso:
    from evaluation.evaluation_logger import evaluation_logger
    
    # Iniciar sesión de evaluación
    session_id = evaluation_logger.start_session("test_session")
    
    # Los eventos se registran automáticamente
    
    # Detener sesión
    evaluation_logger.stop_session()
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any
from threading import Lock
import json

logger = logging.getLogger(__name__)


class EvaluationLogger:
    """
    Singleton logger para sesiones de evaluación.
    
    Registra eventos de enrollment y verification con sus resultados
    para análisis de rendimiento del sistema biométrico.
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
        
        self.logs_dir = Path(__file__).parent / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        self.enabled = False
        self.current_session_id: Optional[str] = None
        self.active_sessions: Dict[str, dict] = {}
        
        self._initialized = True
        logger.info("EvaluationLogger initialized")
    
    def start_session(self, session_name: str) -> str:
        """
        Inicia una sesión de evaluación.
        
        Args:
            session_name: Nombre de la sesión
            
        Returns:
            Session ID
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_id = f"{session_name}_{timestamp}"
        
        self.current_session_id = session_id
        self.active_sessions[session_id] = {
            "name": session_name,
            "started_at": datetime.now().isoformat(),
            "events": [],
            "stats": {
                "enrollments": 0,
                "verifications": 0,
                "successful_verifications": 0,
                "failed_verifications": 0
            }
        }
        self.enabled = True
        
        logger.info(f"Started evaluation session: {session_id}")
        return session_id
    
    def stop_session(self, session_id: Optional[str] = None) -> Optional[str]:
        """
        Detiene una sesión de evaluación.
        
        Args:
            session_id: ID de sesión (opcional, usa la actual si no se especifica)
            
        Returns:
            ID de la sesión detenida o None
        """
        target_id = session_id or self.current_session_id
        
        if target_id and target_id in self.active_sessions:
            self.active_sessions[target_id]["stopped_at"] = datetime.now().isoformat()
            
            # Auto-export
            self.export_session(target_id)
            
            if target_id == self.current_session_id:
                self.current_session_id = None
                self.enabled = False
            
            logger.info(f"Stopped evaluation session: {target_id}")
            return target_id
        
        return None
    
    def log_event(self, event_type: str, data: Dict[str, Any]):
        """
        Registra un evento en la sesión actual.
        
        Args:
            event_type: Tipo de evento (enrollment, verification, etc.)
            data: Datos del evento
        """
        if not self.enabled or not self.current_session_id:
            return
        
        session = self.active_sessions.get(self.current_session_id)
        if not session:
            return
        
        event = {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        session["events"].append(event)
        
        # Update stats
        if event_type == "enrollment":
            session["stats"]["enrollments"] += 1
        elif event_type == "verification":
            session["stats"]["verifications"] += 1
            if data.get("is_verified"):
                session["stats"]["successful_verifications"] += 1
            else:
                session["stats"]["failed_verifications"] += 1
    
    def export_session(self, session_id: str) -> Optional[Path]:
        """
        Exporta los datos de una sesión a JSON.
        
        Args:
            session_id: ID de la sesión
            
        Returns:
            Path al archivo exportado o None
        """
        if session_id not in self.active_sessions:
            return None
        
        filepath = self.logs_dir / f"{session_id}.json"
        
        try:
            with open(filepath, "w") as f:
                json.dump(self.active_sessions[session_id], f, indent=2)
            logger.info(f"Exported session to: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Failed to export session: {e}")
            return None
    
    def list_sessions(self) -> List[str]:
        """Lista todas las sesiones activas."""
        return list(self.active_sessions.keys())
    
    def get_session_summary(self, session_id: str) -> Optional[Dict]:
        """
        Obtiene resumen de una sesión.
        
        Args:
            session_id: ID de la sesión
            
        Returns:
            Diccionario con estadísticas o None
        """
        session = self.active_sessions.get(session_id)
        if not session:
            return None
        
        return {
            "name": session["name"],
            "started_at": session["started_at"],
            "stopped_at": session.get("stopped_at"),
            "event_count": len(session["events"]),
            "stats": session["stats"]
        }


# Global singleton instance
evaluation_logger = EvaluationLogger()


if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.INFO)
    
    # Start session
    session_id = evaluation_logger.start_session("test_session")
    print(f"Started: {session_id}")
    
    # Log events
    evaluation_logger.log_event("enrollment", {"user_id": "user_001", "samples": 3})
    evaluation_logger.log_event("verification", {"user_id": "user_001", "is_verified": True, "score": 0.85})
    evaluation_logger.log_event("verification", {"user_id": "user_001", "is_verified": False, "score": 0.45})
    
    # Summary
    summary = evaluation_logger.get_session_summary(session_id)
    print(f"\nSummary: {summary}")
    
    # Stop
    evaluation_logger.stop_session()
    print(f"\nSession stopped and exported")
