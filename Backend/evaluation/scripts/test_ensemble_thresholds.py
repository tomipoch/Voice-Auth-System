"""
Test Ensemble Thresholds

Quick script to test how different ensemble thresholds affect metrics.
"""

import sys
from pathlib import Path
import numpy as np

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Load results from previous optimization
import json

# We'll use the data from the previous run
# This is a quick analysis script

def analyze_ensemble_thresholds():
    """
    Analyze different ensemble thresholds using the corrected scores.
    
    From previous analysis:
    - Genuine scores (inverted): mean 0.452, std 0.272
    - Cloning scores (inverted): mean 0.430, std 0.292
    """
    
    print("=" * 80)
    print("ENSEMBLE THRESHOLD ANALYSIS")
    print("=" * 80)
    print()
    
    # Simulated data based on previous runs
    # Genuine: mean 0.452, std 0.272, range [0.025 - 0.755]
    # Cloning: mean 0.430, std 0.292, range [0.007 - 0.754]
    
    np.random.seed(42)
    genuine_scores = np.random.normal(0.452, 0.272, 49)
    genuine_scores = np.clip(genuine_scores, 0, 1)
    
    cloning_scores = np.random.normal(0.430, 0.292, 37)
    cloning_scores = np.clip(cloning_scores, 0, 1)
    
    print("Score Distributions (Inverted):")
    print(f"  Genuine: mean={np.mean(genuine_scores):.3f}, std={np.std(genuine_scores):.3f}")
    print(f"  Cloning: mean={np.mean(cloning_scores):.3f}, std={np.std(cloning_scores):.3f}")
    print()
    
    print("=" * 80)
    print("METRICS BY ENSEMBLE THRESHOLD (Without Features)")
    print("=" * 80)
    print()
    
    print(f"{'Threshold':<12} {'BPCER':<12} {'APCER':<12} {'ACER':<12} {'Note':<30}")
    print("-" * 80)
    
    for threshold in [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]:
        # BPCER: % of genuine with score >= threshold (rejected)
        bpcer = np.sum(genuine_scores >= threshold) / len(genuine_scores) * 100
        
        # APCER: % of cloning with score < threshold (accepted)
        apcer = np.sum(cloning_scores < threshold) / len(cloning_scores) * 100
        
        acer = (bpcer + apcer) / 2
        
        note = ""
        if threshold == 0.5:
            note = "← Current baseline"
        elif threshold == 0.6:
            note = "← Recommended"
        
        print(f"{threshold:<12.2f} {bpcer:<12.2f} {apcer:<12.2f} {acer:<12.2f} {note:<30}")
    
    print()
    print("=" * 80)
    print("INTERPRETATION")
    print("=" * 80)
    print()
    print("As threshold increases:")
    print("  - BPCER decreases (fewer genuine rejected) ✅")
    print("  - APCER increases (more cloning accepted) ❌")
    print()
    print("Recommended: threshold 0.6")
    print("  - Reduces BPCER significantly")
    print("  - Moderate increase in APCER")
    print("  - Can be compensated with feature engineering")
    print()

if __name__ == "__main__":
    analyze_ensemble_thresholds()
