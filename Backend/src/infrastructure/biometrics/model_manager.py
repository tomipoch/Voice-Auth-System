"""Model manager for automatic downloading and caching of ML models."""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    """Configuration for a specific model."""
    name: str
    source: str  # HuggingFace or SpeechBrain identifier
    local_path: str
    model_type: str  # 'speaker', 'antispoofing', 'asr'
    version: str
    size_mb: Optional[int] = None
    description: str = ""


class ModelManager:
    """Manages automatic downloading and caching of ML models."""
    
    def __init__(self, models_dir: str = "models"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)
        
        # Model configurations
        self.models = {
            "ecapa_tdnn": ModelConfig(
                name="ECAPA-TDNN Speaker Verification",
                source="speechbrain/spkrec-ecapa-voxceleb",
                local_path="ecapa_tdnn",
                model_type="speaker",
                version="1.0.0",
                size_mb=45,
                description="ECAPA-TDNN trained on VoxCeleb for speaker verification"
            ),
            "rawnet2_antispoofing": ModelConfig(
                name="RawNet2 Anti-Spoofing",
                source="speechbrain/asr-wav2vec2-commonvoice-14-en",  # Placeholder
                local_path="rawnet2_antispoofing", 
                model_type="antispoofing",
                version="1.0.0",
                size_mb=30,
                description="RawNet2 for deepfake and replay attack detection"
            ),
            "wav2vec2_asr": ModelConfig(
                name="Wav2Vec2 ASR",
                source="facebook/wav2vec2-base-960h",
                local_path="wav2vec2_asr",
                model_type="asr",
                version="1.0.0", 
                size_mb=360,
                description="Wav2Vec2 for automatic speech recognition"
            )
        }
        
    def get_model_path(self, model_id: str) -> Path:
        """Get the local path for a model."""
        if model_id not in self.models:
            raise ValueError(f"Unknown model: {model_id}")
        
        config = self.models[model_id]
        return self.models_dir / config.local_path
    
    def is_model_available(self, model_id: str) -> bool:
        """Check if a model is downloaded and available locally."""
        try:
            model_path = self.get_model_path(model_id)
            return model_path.exists() and any(model_path.iterdir())
        except ValueError:
            return False
    
    def download_model(self, model_id: str, force: bool = False) -> bool:
        """Download a model if not already available."""
        if model_id not in self.models:
            logger.error(f"Unknown model: {model_id}")
            return False
        
        config = self.models[model_id]
        model_path = self.get_model_path(model_id)
        
        # Check if already downloaded
        if not force and self.is_model_available(model_id):
            logger.info(f"Model {config.name} already available at {model_path}")
            return True
        
        try:
            logger.info(f"Downloading {config.name} ({config.size_mb}MB)...")
            
            # Create directory
            model_path.mkdir(parents=True, exist_ok=True)
            
            # Download based on model type
            if config.model_type == "speaker":
                return self._download_speechbrain_model(config, model_path)
            elif config.model_type == "asr":
                return self._download_huggingface_model(config, model_path)
            elif config.model_type == "antispoofing":
                # For now, create a placeholder - will implement real anti-spoofing later
                return self._create_placeholder_model(config, model_path)
            else:
                logger.error(f"Unknown model type: {config.model_type}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to download model {config.name}: {e}")
            return False
    
    def _download_speechbrain_model(self, config: ModelConfig, model_path: Path) -> bool:
        """Download a SpeechBrain model."""
        try:
            from speechbrain.pretrained import EncoderClassifier
            
            logger.info(f"Downloading SpeechBrain model: {config.source}")
            
            # SpeechBrain automatically downloads to the specified directory
            _ = EncoderClassifier.from_hparams(
                source=config.source,
                savedir=str(model_path),
                run_opts={"device": "cpu"}  # Use CPU for download
            )
            
            logger.info(f"Successfully downloaded {config.name}")
            return True
            
        except ImportError:
            logger.error("SpeechBrain not available for downloading")
            return False
        except Exception as e:
            logger.error(f"Error downloading SpeechBrain model: {e}")
            return False
    
    def _download_huggingface_model(self, config: ModelConfig, model_path: Path) -> bool:
        """Download a HuggingFace model."""
        try:
            from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC
            
            logger.info(f"Downloading HuggingFace model: {config.source}")
            
            # Download processor and model
            processor = Wav2Vec2Processor.from_pretrained(config.source)
            model = Wav2Vec2ForCTC.from_pretrained(config.source)
            
            # Save locally
            processor.save_pretrained(str(model_path))
            model.save_pretrained(str(model_path))
            
            logger.info(f"Successfully downloaded {config.name}")
            return True
            
        except ImportError:
            logger.error("Transformers not available for downloading")
            return False
        except Exception as e:
            logger.error(f"Error downloading HuggingFace model: {e}")
            return False
    
    def _create_placeholder_model(self, config: ModelConfig, model_path: Path) -> bool:
        """Create a placeholder for models not yet implemented."""
        try:
            # Create a simple placeholder file
            placeholder_file = model_path / "placeholder.txt"
            with open(placeholder_file, "w") as f:
                f.write(f"Placeholder for {config.name}\n")
                f.write(f"Model type: {config.model_type}\n")
                f.write(f"Version: {config.version}\n")
                f.write("Real implementation coming soon...\n")
            
            logger.info(f"Created placeholder for {config.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating placeholder: {e}")
            return False
    
    def download_all_models(self) -> Dict[str, bool]:
        """Download all configured models."""
        results = {}
        for model_id in self.models:
            results[model_id] = self.download_model(model_id)
        return results
    
    def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """Get information about a model."""
        if model_id not in self.models:
            raise ValueError(f"Unknown model: {model_id}")
        
        config = self.models[model_id]
        return {
            "name": config.name,
            "source": config.source,
            "local_path": str(self.get_model_path(model_id)),
            "model_type": config.model_type,
            "version": config.version,
            "size_mb": config.size_mb,
            "description": config.description,
            "available": self.is_model_available(model_id)
        }
    
    def list_models(self) -> Dict[str, Dict[str, Any]]:
        """List all configured models and their status."""
        return {model_id: self.get_model_info(model_id) for model_id in self.models}


# Global model manager instance
model_manager = ModelManager()