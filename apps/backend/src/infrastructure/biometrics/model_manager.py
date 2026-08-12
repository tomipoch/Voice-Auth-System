"""Model manager for automatic downloading and caching of ML models with performance optimizations."""

import os
import logging
import threading
import time
from pathlib import Path
from typing import Dict, Any, Optional, Set
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

# Optional dependency for advanced memory monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

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
    priority: int = 1  # Higher priority models load first
    memory_usage_mb: Optional[int] = None  # Estimated memory usage


@dataclass
class ModelCache:
    """Model cache entry with performance tracking."""
    model_instance: Any
    last_accessed: float
    access_count: int
    memory_size_mb: float


class ModelManager:
    """
    Manages automatic downloading and caching of ML models with performance optimizations.
    
    Features:
    - Lazy loading: Models loaded only when needed
    - Memory management: Automatic cache cleanup based on memory pressure
    - Concurrent downloads: Multiple models can download simultaneously
    - Priority loading: High-priority models load first
    - Access tracking: Recently used models stay in cache longer
    """
    
    def __init__(self, models_dir: str = "models", max_cache_size_mb: int = 2048):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)
        
        # Performance optimization settings
        self.max_cache_size_mb = max_cache_size_mb
        self.cache_cleanup_interval = 300  # 5 minutes
        self.max_memory_usage_percent = 80  # Don't use more than 80% of system RAM
        
        # Runtime cache and state
        self._model_cache: Dict[str, ModelCache] = {}
        self._cache_lock = threading.RLock()
        self._download_executor = ThreadPoolExecutor(max_workers=3)
        self._currently_downloading: Set[str] = set()
        self._download_lock = threading.Lock()
        
        # Start cache cleanup thread
        self._start_cache_cleanup_thread()
        
        # Model configurations - Anteproyecto specifications with performance data
        self.models = {
            # Speaker Recognition Models (High priority - core functionality)
            "ecapa_tdnn": ModelConfig(
                name="ECAPA-TDNN Speaker Verification",
                source="speechbrain/spkrec-ecapa-voxceleb",
                local_path="speaker-recognition/ecapa_tdnn",
                model_type="speaker",
                version="1.0.0",
                size_mb=45,
                memory_usage_mb=200,
                priority=5,  # Highest priority
                description="ECAPA-TDNN trained on VoxCeleb for speaker verification"
            ),
            
            # Anti-Spoofing Models
            "aasist": ModelConfig(
                name="AASIST Anti-Spoofing",
                source="speechbrain/aasist-wav2vec2-AASIST",
                local_path="anti-spoofing/aasist",
                model_type="antispoofing",
                version="1.0.0",
                size_mb=50,
                memory_usage_mb=180,
                priority=4,  # High priority for security
                description="AASIST model for spoofing attack detection (ASVspoof 2019/2021)"
            ),
            "rawnet2": ModelConfig(
                name="RawNet2 Anti-Spoofing",
                source="speechbrain/spkrec-rawnet2-antispoofing",
                local_path="anti-spoofing/rawnet2",
                model_type="antispoofing",
                version="1.0.0",
                size_mb=30,
                memory_usage_mb=120,
                priority=4,  # High priority for security
                description="RawNet2 for deepfake and replay attack detection"
            ),

            
            # ASR Model for phrase verification
            "wav2vec2_asr_es": ModelConfig(
                name="Wav2Vec2 Spanish ASR",
                source="speechbrain/asr-wav2vec2-commonvoice-14-es",
                local_path="text-verification/lightweight_asr",
                model_type="asr",
                version="1.0.0",
                size_mb=120,
                memory_usage_mb=300,
                priority=2,
                description="Wav2Vec2-based Spanish ASR for phrase verification"
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
                return self._download_speechbrain_asr_model(config, model_path)
            elif config.model_type == "antispoofing":
                return self._download_speechbrain_model(config, model_path)
            else:
                logger.error(f"Unknown model type: {config.model_type}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to download model {config.name}: {e}")
            return False
    
    def _download_speechbrain_model(self, config: ModelConfig, model_path: Path) -> bool:
        """Download a SpeechBrain model."""
        try:
            from speechbrain.inference.speaker import EncoderClassifier
            
            logger.info(f"Downloading SpeechBrain model: {config.source}")
            
            # Check if model path already exists and has content to avoid re-downloading
            if model_path.exists() and any(model_path.iterdir()):
                # Check if it's a valid model directory
                hyperparams_file = model_path / "hyperparams.yaml"
                if hyperparams_file.exists():
                    logger.info(f"Model {config.name} already exists at {model_path}")
                    return True
            
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
            error_msg = str(e)
            # Check if it's a 401 or repository not found error
            if "401" in error_msg or "Repository Not Found" in error_msg or "Invalid username or password" in error_msg:
                logger.warning(f"Model {config.name} is not publicly available or requires authentication. Skipping download.")
                # Don't create partial files that would trigger reloads
                if model_path.exists():
                    try:
                        # Clean up any partial files
                        import shutil
                        if model_path.is_dir():
                            shutil.rmtree(model_path, ignore_errors=True)
                    except Exception:
                        pass
                return False
            logger.error(f"Error downloading SpeechBrain model: {e}")
            # Clean up partial files on error
            if model_path.exists():
                try:
                    import shutil
                    if model_path.is_dir():
                        shutil.rmtree(model_path, ignore_errors=True)
                except Exception:
                    pass
            return False
    
    def _download_speechbrain_asr_model(self, config: ModelConfig, model_path: Path) -> bool:
        """Download a SpeechBrain ASR model."""
        try:
            from speechbrain.inference.ASR import EncoderASR
            
            logger.info(f"Downloading SpeechBrain ASR model: {config.source}")
            
            # Check if model path already exists and has content to avoid re-downloading
            if model_path.exists() and any(model_path.iterdir()):
                # Check if it's a valid model directory
                hyperparams_file = model_path / "hyperparams.yaml"
                if hyperparams_file.exists():
                    logger.info(f"Model {config.name} already exists at {model_path}")
                    return True
            
            # SpeechBrain automatically downloads to the specified directory
            _ = EncoderASR.from_hparams(
                source=config.source,
                savedir=str(model_path),
                run_opts={"device": "cpu"}  # Use CPU for download
            )
            
            logger.info(f"Successfully downloaded {config.name}")
            return True
            
        except ImportError:
            logger.error("SpeechBrain not available for downloading ASR model")
            return False
        except Exception as e:
            error_msg = str(e)
            # Check if it's a 401 or repository not found error
            if "401" in error_msg or "Repository Not Found" in error_msg or "Invalid username or password" in error_msg:
                logger.warning(f"Model {config.name} is not publicly available or requires authentication. Skipping download.")
                # Don't create partial files that would trigger reloads
                if model_path.exists():
                    try:
                        # Clean up any partial files
                        import shutil
                        if model_path.is_dir():
                            shutil.rmtree(model_path, ignore_errors=True)
                    except Exception:
                        pass
                return False
            logger.error(f"Error downloading SpeechBrain ASR model: {e}")
            # Clean up partial files on error
            if model_path.exists():
                try:
                    import shutil
                    if model_path.is_dir():
                        shutil.rmtree(model_path, ignore_errors=True)
                except Exception:
                    pass
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
    
    # Performance optimization methods
    
    def get_cached_model(self, model_id: str) -> Optional[Any]:
        """Get a model from cache if available."""
        with self._cache_lock:
            if model_id in self._model_cache:
                cache_entry = self._model_cache[model_id]
                cache_entry.last_accessed = time.time()
                cache_entry.access_count += 1
                logger.debug(f"Model {model_id} retrieved from cache (access #{cache_entry.access_count})")
                return cache_entry.model_instance
        return None
    
    def cache_model(self, model_id: str, model_instance: Any) -> bool:
        """Cache a model instance with memory management."""
        if model_id not in self.models:
            return False
        
        config = self.models[model_id]
        estimated_size = config.memory_usage_mb or 100  # Default 100MB if unknown
        
        # Check if we have enough memory
        if not self._check_memory_available(estimated_size):
            logger.warning(f"Insufficient memory to cache {model_id}, cleaning up...")
            self._cleanup_cache()
            
            # Try again after cleanup
            if not self._check_memory_available(estimated_size):
                logger.warning(f"Still insufficient memory for {model_id}, skipping cache")
                return False
        
        with self._cache_lock:
            self._model_cache[model_id] = ModelCache(
                model_instance=model_instance,
                last_accessed=time.time(),
                access_count=1,
                memory_size_mb=estimated_size
            )
            logger.info(f"Cached model {model_id} ({estimated_size}MB)")
        
        return True
    
    def preload_models_by_priority(self, max_models: int = 3) -> Dict[str, bool]:
        """Preload models based on priority for faster access."""
        logger.info(f"Preloading up to {max_models} models by priority...")
        
        # Sort models by priority (highest first)
        sorted_models = sorted(
            self.models.items(),
            key=lambda x: x[1].priority,
            reverse=True
        )
        
        results = {}
        loaded_count = 0
        
        for model_id, config in sorted_models[:max_models]:
            if loaded_count >= max_models:
                break
            
            if not self.is_model_available(model_id):
                logger.info(f"Downloading high-priority model: {model_id}")
                success = self.download_model(model_id)
                results[model_id] = success
                if success:
                    loaded_count += 1
            else:
                results[model_id] = True
                loaded_count += 1
        
        logger.info(f"Preloaded {loaded_count} models successfully")
        return results
    
    def get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage statistics."""
        with self._cache_lock:
            total_cache_mb = sum(entry.memory_size_mb for entry in self._model_cache.values())
        
        if PSUTIL_AVAILABLE:
            try:
                system_memory = psutil.virtual_memory()
                return {
                    "cache_usage_mb": total_cache_mb,
                    "cache_limit_mb": self.max_cache_size_mb,
                    "system_total_mb": system_memory.total / (1024 * 1024),
                    "system_available_mb": system_memory.available / (1024 * 1024),
                    "system_usage_percent": system_memory.percent,
                    "cached_models": list(self._model_cache.keys()),
                    "psutil_available": True
                }
            except Exception as e:
                logger.warning(f"Error getting system memory info: {e}")
        
        # Fallback when psutil is not available
        return {
            "cache_usage_mb": total_cache_mb,
            "cache_limit_mb": self.max_cache_size_mb,
            "system_total_mb": 8192.0,  # Assume 8GB default
            "system_available_mb": 4096.0,  # Assume 4GB available
            "system_usage_percent": 50.0,  # Assume 50% usage
            "cached_models": list(self._model_cache.keys()),
            "psutil_available": False
        }
    
    def _check_memory_available(self, required_mb: float) -> bool:
        """Check if enough memory is available for caching."""
        memory_stats = self.get_memory_usage()
        
        # Check cache limit
        if memory_stats["cache_usage_mb"] + required_mb > self.max_cache_size_mb:
            return False
        
        # Check system memory
        if memory_stats["system_usage_percent"] > self.max_memory_usage_percent:
            return False
        
        return True
    
    def _cleanup_cache(self):
        """Clean up cache based on LRU policy."""
        with self._cache_lock:
            if not self._model_cache:
                return
            
            # Sort by last accessed time (oldest first)
            sorted_cache = sorted(
                self._model_cache.items(),
                key=lambda x: x[1].last_accessed
            )
            
            # Remove oldest 30% of cached models
            cleanup_count = max(1, len(sorted_cache) // 3)
            
            for i in range(cleanup_count):
                model_id, cache_entry = sorted_cache[i]
                del self._model_cache[model_id]
                logger.info(f"Removed {model_id} from cache (freed {cache_entry.memory_size_mb}MB)")
    
    def _start_cache_cleanup_thread(self):
        """Start background thread for periodic cache cleanup."""
        def cleanup_worker():
            while True:
                try:
                    time.sleep(self.cache_cleanup_interval)
                    
                    # Check memory pressure
                    memory_stats = self.get_memory_usage()
                    if memory_stats["system_usage_percent"] > self.max_memory_usage_percent:
                        logger.info("High memory usage detected, cleaning cache...")
                        self._cleanup_cache()
                    
                except Exception as e:
                    logger.error(f"Cache cleanup thread error: {e}")
        
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
        logger.info("Started cache cleanup background thread")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        with self._cache_lock:
            cache_stats = {}
            for model_id, cache_entry in self._model_cache.items():
                cache_stats[model_id] = {
                    "access_count": cache_entry.access_count,
                    "last_accessed": cache_entry.last_accessed,
                    "memory_mb": cache_entry.memory_size_mb
                }
        
        memory_stats = self.get_memory_usage()
        
        return {
            "cache_statistics": cache_stats,
            "memory_usage": memory_stats,
            "download_queue_size": len(self._currently_downloading),
            "total_models_configured": len(self.models),
            "models_downloaded": sum(1 for model_id in self.models if self.is_model_available(model_id)),
            "optimization_settings": {
                "max_cache_size_mb": self.max_cache_size_mb,
                "cleanup_interval_sec": self.cache_cleanup_interval,
                "max_memory_usage_percent": self.max_memory_usage_percent
            }
        }


# Global model manager instance with performance optimizations
model_manager = ModelManager()