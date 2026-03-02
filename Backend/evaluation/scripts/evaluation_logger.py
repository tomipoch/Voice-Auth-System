"""
Evaluation Logger

Automatic data capture system for manual frontend evaluation.
Logs all enrollment and verification operations when evaluation mode is active.

Usage:
    from evaluation.evaluation_logger import evaluation_logger
    
    # Start evaluation session
    session_id = evaluation_logger.start_session("my_evaluation")
    
    # Log operations (done automatically via service hooks)
    evaluation_logger.log_enrollment(user_id, embedding, metadata)
    evaluation_logger.log_verification_attempt(user_id, similarity, spoof_prob, decision)
    
    # Export data
    filepath = evaluation_logger.export_session(session_id)
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from threading import Lock
import numpy as np

logger = logging.getLogger(__name__)


class EvaluationSession:
    """Represents an active evaluation session."""
    
    def __init__(self, session_id: str, session_name: str):
        self.session_id = session_id
        self.session_name = session_name
        self.started_at = datetime.now().isoformat()
        self.enrollments: List[Dict] = []
        self.verification_attempts: List[Dict] = []
        self._lock = Lock()
    
    def add_enrollment(self, enrollment_data: Dict):
        """Thread-safe enrollment logging."""
        with self._lock:
            self.enrollments.append(enrollment_data)
    
    def add_verification(self, verification_data: Dict):
        """Thread-safe verification logging."""
        with self._lock:
            self.verification_attempts.append(verification_data)
    
    def to_dict(self) -> Dict:
        """Convert session to dictionary."""
        with self._lock:
            return {
                "session_id": self.session_id,
                "session_name": self.session_name,
                "started_at": self.started_at,
                "enrollments": self.enrollments.copy(),
                "verification_attempts": self.verification_attempts.copy(),
                "stats": {
                    "total_enrollments": len(self.enrollments),
                    "total_verifications": len(self.verification_attempts)
                }
            }


class EvaluationLogger:
    """
    Singleton logger for evaluation data capture.
    
    Automatically captures enrollment and verification data when
    evaluation mode is enabled.
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
        
        self.results_dir = Path(__file__).parent / "results"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        self.active_sessions: Dict[str, EvaluationSession] = {}
        self.current_session_id: Optional[str] = None
        self.enabled = False
        
        self._initialized = True
        logger.info("EvaluationLogger initialized")
    
    def start_session(self, session_name: str) -> str:
        """
        Start a new evaluation session.
        
        Args:
            session_name: Descriptive name for the session
            
        Returns:
            Session ID
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_id = f"{session_name}_{timestamp}"
        
        session = EvaluationSession(session_id, session_name)
        self.active_sessions[session_id] = session
        self.current_session_id = session_id
        self.enabled = True
        
        logger.info(f"Started evaluation session: {session_id}")
        return session_id
    
    def stop_session(self, session_id: Optional[str] = None) ->Optional[str]:
        """
        Stop an evaluation session.
        
        Args:
            session_id: Session to stop. If None, stops current session.
            
        Returns:
            Stopped session ID or None
        """
        if session_id is None:
            session_id = self.current_session_id
        
        if session_id and session_id in self.active_sessions:
            if session_id == self.current_session_id:
                self.current_session_id = None
                self.enabled = False
            
            logger.info(f"Stopped evaluation session: {session_id}")
            return session_id
        
        return None
    
    def log_enrollment(
        self,
        user_id: str,
        embedding: np.ndarray,
        audio_metadata: Optional[Dict] = None
    ):
        """
        Log an enrollment operation.
        
        Args:
            user_id: User being enrolled
            embedding: Voice embedding
            audio_metadata: Optional audio metadata (duration, format, etc.)
        """
        if not self.enabled or not self.current_session_id:
            return
        
        session = self.active_sessions.get(self.current_session_id)
        if not session:
            return
        
        enrollment_data = {
            "enrollment_id": f"enroll_{len(session.enrollments) + 1:04d}",
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "embedding_shape": list(embedding.shape) if hasattr(embedding, 'shape') else None,
            "embedding_norm": float(np.linalg.norm(embedding)) if hasattr(embedding, 'shape') else None,
            "audio_metadata": audio_metadata or {}
        }
        
        session.add_enrollment(enrollment_data)
        logger.debug(f"Logged enrollment: {user_id}")
    
    def log_verification_attempt(
        self,
        user_id: str,
        similarity_score: float,
        spoof_probability: Optional[float],
        system_decision: str,
        threshold_used: float,
        challenge_id: Optional[str] = None,
        phrase_match_score: Optional[float] = None,
        additional_data: Optional[Dict] = None
    ):
        """
        Log a verification attempt.
        
        Args:
            user_id: User attempting verification
            similarity_score: Speaker similarity score
            spoof_probability: Anti-spoofing score
            system_decision: "accepted" or "rejected"
            threshold_used: Threshold used for decision
            challenge_id: Optional challenge ID
            phrase_match_score: Optional phrase matching score
            additional_data: Any additional metadata
        """
        if not self.enabled or not self.current_session_id:
            return
        
        session = self.active_sessions.get(self.current_session_id)
        if not session:
            return
        
        attempt_id = f"v{len(session.verification_attempts) + 1:04d}"
        
        verification_data = {
            "attempt_id": attempt_id,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "similarity_score": float(similarity_score),
            "spoof_probability": float(spoof_probability) if spoof_probability is not None else None,
            "phrase_match_score": float(phrase_match_score) if phrase_match_score is not None else None,
            "system_decision": system_decision,
            "threshold_used": float(threshold_used),
            "challenge_id": challenge_id,
            # Fields for manual annotation
            "manual_annotation": None,  # User will annotate: "genuine" or "impostor"
            "is_genuine": None,  # User will mark: true or false
            "notes": "",
            **(additional_data or {})
        }
        
        session.add_verification(verification_data)
        logger.debug(f"Logged verification: {user_id} -> {system_decision}")
    
    def export_session(self, session_id: Optional[str] = None) -> Optional[Path]:
        """
        Export session data to JSON file.
        
        Args:
            session_id: Session to export. If None, exports current session.
            
        Returns:
            Path to exported file or None
        """
        if session_id is None:
            session_id = self.current_session_id
        
        if not session_id or session_id not in self.active_sessions:
            logger.warning(f"Session not found: {session_id}")
            return None
        
        session = self.active_sessions[session_id]
        session_data = session.to_dict()
        
        # Save to file
        filepath = self.results_dir / f"{session_id}.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported session to: {filepath}")
        logger.info(f"  Enrollments: {len(session.enrollments)}")
        logger.info(f"  Verifications: {len(session.verification_attempts)}")
        
        return filepath
    
    def list_sessions(self) -> List[str]:
        """List all active session IDs."""
        return list(self.active_sessions.keys())
    
    def get_session_summary(self, session_id: Optional[str] = None) -> Optional[Dict]:
        """
        Get summary of a session.
        
        Args:
            session_id: Session ID or None for current
            
        Returns:
            Summary dictionary or None
        """
        if session_id is None:
            session_id = self.current_session_id
        
        if not session_id or session_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[session_id]
        return session.to_dict()["stats"]


# Global singleton instance
evaluation_logger = EvaluationLogger()


# Convenience functions for easier imports
def start_evaluation_session(session_name: str) -> str:
    """Start a new evaluation session."""
    return evaluation_logger.start_session(session_name)


def stop_evaluation_session(session_id: Optional[str] = None):
    """Stop an evaluation session."""
    return evaluation_logger.stop_session(session_id)


def export_evaluation_session(session_id: Optional[str] = None) -> Optional[Path]:
    """Export session data to file."""
    return evaluation_logger.export_session(session_id)


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Start session
    session_id = evaluation_logger.start_session("test_eval")
    print(f"Started session: {session_id}")
    
    # Simulate some enrollments
    for i in range(3):
        evaluation_logger.log_enrollment(
            user_id=f"user_{i+1:03d}",
            embedding=np.random.rand(192),
            audio_metadata={"duration_ms": 3500}
        )
    
    # Simulate some verifications
    for i in range(10):
        is_genuine = i % 2 == 0
        evaluation_logger.log_verification_attempt(
            user_id=f"user_{(i % 3) + 1:03d}",
            similarity_score=np.random.uniform(0.7, 0.95) if is_genuine else np.random.uniform(0.3, 0.6),
            spoof_probability=np.random.uniform(0.01, 0.1),
            system_decision="accepted" if is_genuine else "rejected",
            threshold_used=0.70
        )
    
    # Export
    filepath = evaluation_logger.export_session()
    print(f"\nExported to: {filepath}")
    
    # Show summary
    summary = evaluation_logger.get_session_summary()
    print(f"Summary: {summary}")
