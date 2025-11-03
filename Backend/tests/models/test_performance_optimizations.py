#!/usr/bin/env python3
"""
Test script for model manager performance optimizations.
Tests caching, memory management, and priority loading features.
"""

import sys
import os
import time
import logging
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_model_manager_initialization():
    """Test optimized model manager initialization."""
    logger.info("Testing optimized model manager initialization...")
    
    try:
        from infrastructure.biometrics.model_manager import ModelManager
        
        # Create manager with custom settings
        manager = ModelManager(max_cache_size_mb=1024)
        
        logger.info(f"✓ Model manager initialized with cache limit: {manager.max_cache_size_mb}MB")
        logger.info(f"✓ Models directory: {manager.models_dir}")
        logger.info(f"✓ Total configured models: {len(manager.models)}")
        
        # Test model priority configuration
        models_by_priority = {}
        for model_id, config in manager.models.items():
            priority = config.priority
            if priority not in models_by_priority:
                models_by_priority[priority] = []
            models_by_priority[priority].append((model_id, config.name))
        
        logger.info("✓ Models organized by priority:")
        for priority in sorted(models_by_priority.keys(), reverse=True):
            models = models_by_priority[priority]
            logger.info(f"  Priority {priority}: {[m[0] for m in models]}")
        
        return manager
        
    except Exception as e:
        logger.error(f"✗ Model manager initialization failed: {e}")
        raise

def test_memory_monitoring(manager):
    """Test memory monitoring capabilities."""
    logger.info("Testing memory monitoring...")
    
    try:
        # Get memory usage statistics
        memory_stats = manager.get_memory_usage()
        
        logger.info("✓ Memory usage statistics:")
        logger.info(f"  - Cache usage: {memory_stats['cache_usage_mb']:.1f}MB")
        logger.info(f"  - Cache limit: {memory_stats['cache_limit_mb']}MB")
        logger.info(f"  - System total: {memory_stats['system_total_mb']:.1f}MB")
        logger.info(f"  - System available: {memory_stats['system_available_mb']:.1f}MB")
        logger.info(f"  - System usage: {memory_stats['system_usage_percent']:.1f}%")
        logger.info(f"  - Cached models: {memory_stats['cached_models']}")
        
        # Verify memory stats structure
        required_fields = ["cache_usage_mb", "cache_limit_mb", "system_total_mb", 
                          "system_available_mb", "system_usage_percent", "cached_models"]
        for field in required_fields:
            assert field in memory_stats, f"Missing memory stat field: {field}"
        
        # Verify reasonable values
        assert 0 <= memory_stats["system_usage_percent"] <= 100, "Invalid system usage percentage"
        assert memory_stats["system_total_mb"] > 0, "System total memory should be positive"
        assert memory_stats["cache_usage_mb"] >= 0, "Cache usage should be non-negative"
        
        logger.info("✓ Memory monitoring working correctly")
        
    except Exception as e:
        logger.error(f"✗ Memory monitoring failed: {e}")
        raise

def test_model_caching(manager):
    """Test model caching functionality."""
    logger.info("Testing model caching...")
    
    try:
        test_model_id = "ecapa_tdnn"
        
        # Test cache miss
        cached_model = manager.get_cached_model(test_model_id)
        assert cached_model is None, "Cache should be empty initially"
        logger.info("✓ Cache miss handled correctly")
        
        # Test caching a mock model
        mock_model = {"type": "mock_ecapa_tdnn", "loaded": True}
        success = manager.cache_model(test_model_id, mock_model)
        assert success, "Model caching should succeed"
        logger.info("✓ Model cached successfully")
        
        # Test cache hit
        cached_model = manager.get_cached_model(test_model_id)
        assert cached_model is not None, "Model should be in cache"
        assert cached_model["type"] == "mock_ecapa_tdnn", "Cached model should match original"
        logger.info("✓ Cache hit working correctly")
        
        # Test cache statistics
        memory_stats = manager.get_memory_usage()
        assert test_model_id in memory_stats["cached_models"], "Model should appear in cached models list"
        logger.info(f"✓ Cache contains: {memory_stats['cached_models']}")
        
        # Test invalid model caching
        invalid_success = manager.cache_model("invalid_model", mock_model)
        assert not invalid_success, "Invalid model caching should fail"
        logger.info("✓ Invalid model caching correctly rejected")
        
        logger.info("✓ Model caching functionality working correctly")
        
    except Exception as e:
        logger.error(f"✗ Model caching failed: {e}")
        raise

def test_priority_loading(manager):
    """Test priority-based model loading."""
    logger.info("Testing priority-based model loading...")
    
    try:
        # Test preloading with priority
        results = manager.preload_models_by_priority(max_models=2)
        
        logger.info("✓ Priority loading results:")
        for model_id, success in results.items():
            config = manager.models[model_id]
            logger.info(f"  - {model_id} (priority {config.priority}): {'✓' if success else '✗'}")
        
        # Verify that highest priority models were selected
        loaded_models = list(results.keys())
        
        # Check that we got the highest priority models
        if len(loaded_models) >= 2:
            # Should include highest priority models
            max_priority = max(config.priority for config in manager.models.values())
            high_priority_loaded = any(manager.models[model_id].priority == max_priority 
                                     for model_id in loaded_models)
            assert high_priority_loaded, "Should include highest priority model"
            logger.info("✓ Highest priority models were selected")
        
        logger.info("✓ Priority loading working correctly")
        
    except Exception as e:
        logger.error(f"✗ Priority loading failed: {e}")
        raise

def test_performance_statistics(manager):
    """Test comprehensive performance statistics."""
    logger.info("Testing performance statistics...")
    
    try:
        # Get performance stats
        perf_stats = manager.get_performance_stats()
        
        logger.info("✓ Performance statistics:")
        
        # Cache statistics
        cache_stats = perf_stats["cache_statistics"]
        logger.info(f"  - Cached models: {len(cache_stats)}")
        for model_id, stats in cache_stats.items():
            logger.info(f"    * {model_id}: {stats['access_count']} accesses, {stats['memory_mb']:.1f}MB")
        
        # Memory usage
        memory_usage = perf_stats["memory_usage"]
        logger.info(f"  - Cache usage: {memory_usage['cache_usage_mb']:.1f}MB")
        logger.info(f"  - System usage: {memory_usage['system_usage_percent']:.1f}%")
        
        # Model statistics
        logger.info(f"  - Total models configured: {perf_stats['total_models_configured']}")
        logger.info(f"  - Models downloaded: {perf_stats['models_downloaded']}")
        logger.info(f"  - Download queue size: {perf_stats['download_queue_size']}")
        
        # Optimization settings
        opt_settings = perf_stats["optimization_settings"]
        logger.info("  - Optimization settings:")
        logger.info(f"    * Max cache size: {opt_settings['max_cache_size_mb']}MB")
        logger.info(f"    * Cleanup interval: {opt_settings['cleanup_interval_sec']}s")
        logger.info(f"    * Max memory usage: {opt_settings['max_memory_usage_percent']}%")
        
        # Verify statistics structure
        required_sections = ["cache_statistics", "memory_usage", "download_queue_size", 
                           "total_models_configured", "models_downloaded", "optimization_settings"]
        for section in required_sections:
            assert section in perf_stats, f"Missing performance stat section: {section}"
        
        logger.info("✓ Performance statistics working correctly")
        
    except Exception as e:
        logger.error(f"✗ Performance statistics failed: {e}")
        raise

def test_cache_cleanup(manager):
    """Test cache cleanup functionality."""
    logger.info("Testing cache cleanup...")
    
    try:
        # Add multiple models to cache
        test_models = ["ecapa_tdnn", "x_vector", "aasist"]
        mock_models = []
        
        for i, model_id in enumerate(test_models):
            mock_model = {"type": f"mock_{model_id}", "id": i}
            success = manager.cache_model(model_id, mock_model)
            if success:
                mock_models.append(model_id)
                # Simulate different access times
                time.sleep(0.1)
                if i < len(test_models) - 1:  # Don't access the last one
                    manager.get_cached_model(model_id)
        
        logger.info(f"✓ Cached {len(mock_models)} models for cleanup test")
        
        # Check cache before cleanup
        memory_stats_before = manager.get_memory_usage()
        cached_before = len(memory_stats_before["cached_models"])
        logger.info(f"✓ Models in cache before cleanup: {cached_before}")
        
        # Force cache cleanup
        manager._cleanup_cache()
        
        # Check cache after cleanup
        memory_stats_after = manager.get_memory_usage()
        cached_after = len(memory_stats_after["cached_models"])
        logger.info(f"✓ Models in cache after cleanup: {cached_after}")
        
        # Verify cleanup worked (should have fewer models)
        if cached_before > 1:
            assert cached_after < cached_before, "Cache cleanup should remove some models"
            logger.info("✓ Cache cleanup successfully removed models")
        
        logger.info("✓ Cache cleanup working correctly")
        
    except Exception as e:
        logger.error(f"✗ Cache cleanup failed: {e}")
        raise

def main():
    """Main test function."""
    logger.info("=" * 60)
    logger.info("Model Manager Performance Optimization Test")
    logger.info("Testing caching, memory management, and priority loading")
    logger.info("=" * 60)
    
    try:
        # Test initialization with optimizations
        manager = test_model_manager_initialization()
        
        # Test memory monitoring
        test_memory_monitoring(manager)
        
        # Test model caching
        test_model_caching(manager)
        
        # Test priority loading
        test_priority_loading(manager)
        
        # Test performance statistics
        test_performance_statistics(manager)
        
        # Test cache cleanup
        test_cache_cleanup(manager)
        
        logger.info("=" * 60)
        logger.info("✅ ALL PERFORMANCE TESTS PASSED!")
        logger.info("Model manager optimizations working correctly:")
        logger.info("- Memory monitoring and management")
        logger.info("- Model caching with LRU cleanup")
        logger.info("- Priority-based model loading")
        logger.info("- Comprehensive performance statistics")
        logger.info("- Background cache cleanup")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error("=" * 60)
        logger.error("❌ PERFORMANCE TESTS FAILED!")
        logger.error(f"Error: {e}")
        logger.error("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    main()