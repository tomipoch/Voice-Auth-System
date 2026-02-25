"""
ASR Threshold Analysis

Analyzes similarity score distribution from existing ASR results
and recommends optimal threshold for phrase verification.
"""

import sys
from pathlib import Path
import re
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Dict, Tuple

def parse_asr_report(report_path: Path) -> Dict:
    """Parse ASR report to extract similarity scores."""
    
    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract similarity scores from examples
    similarity_pattern = r'Similarity:\s*(\d+\.?\d*)%'
    similarities = []
    
    for match in re.finditer(similarity_pattern, content):
        sim = float(match.group(1))
        similarities.append(sim)
    
    # Extract global metrics
    global_sim_pattern = r'PHRASE SIMILARITY\s+Promedio:\s*(\d+\.?\d*)%\s+Desv\. Std:\s*(\d+\.?\d*)%'
    global_match = re.search(global_sim_pattern, content)
    
    if global_match:
        mean_sim = float(global_match.group(1))
        std_sim = float(global_match.group(2))
    else:
        mean_sim = np.mean(similarities) if similarities else 0
        std_sim = np.std(similarities) if similarities else 0
    
    return {
        'similarities': similarities,
        'mean': mean_sim,
        'std': std_sim,
        'count': len(similarities)
    }


def analyze_thresholds(similarities: List[float]) -> Dict:
    """Analyze different threshold values."""
    
    thresholds = [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80]
    results = []
    
    for threshold in thresholds:
        accepted = sum(1 for s in similarities if s >= threshold)
        rejected = len(similarities) - accepted
        
        acceptance_rate = (accepted / len(similarities) * 100) if similarities else 0
        rejection_rate = (rejected / len(similarities) * 100) if similarities else 0
        
        results.append({
            'threshold': threshold,
            'accepted': accepted,
            'rejected': rejected,
            'acceptance_rate': acceptance_rate,
            'rejection_rate': rejection_rate
        })
    
    return results


def generate_visualization(data: Dict, output_path: Path):
    """Generate visualization of similarity distribution and thresholds."""
    
    similarities = data['similarities']
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Plot 1: Histogram of similarities
    ax1.hist(similarities, bins=20, color='steelblue', alpha=0.7, edgecolor='black')
    ax1.axvline(data['mean'], color='red', linestyle='--', linewidth=2, label=f'Mean: {data["mean"]:.1f}%')
    ax1.axvline(70, color='green', linestyle='--', linewidth=2, label='Current Threshold: 70%')
    ax1.set_xlabel('Similarity Score (%)', fontsize=12)
    ax1.set_ylabel('Frequency', fontsize=12)
    ax1.set_title('Distribution of Similarity Scores', fontsize=14, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Acceptance rate by threshold
    threshold_analysis = analyze_thresholds(similarities)
    thresholds = [r['threshold'] * 100 for r in threshold_analysis]
    acceptance_rates = [r['acceptance_rate'] for r in threshold_analysis]
    
    ax2.plot(thresholds, acceptance_rates, marker='o', linewidth=2, markersize=8, color='steelblue')
    ax2.axhline(90, color='green', linestyle='--', alpha=0.5, label='90% acceptance')
    ax2.axhline(80, color='orange', linestyle='--', alpha=0.5, label='80% acceptance')
    ax2.axvline(70, color='red', linestyle='--', alpha=0.5, label='Current threshold')
    ax2.set_xlabel('Threshold (%)', fontsize=12)
    ax2.set_ylabel('Acceptance Rate (%)', fontsize=12)
    ax2.set_title('Acceptance Rate by Threshold', fontsize=14, fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Visualization saved to: {output_path}")


def generate_report(data: Dict, threshold_analysis: List[Dict], output_path: Path):
    """Generate detailed threshold analysis report."""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("ASR SIMILARITY THRESHOLD ANALYSIS\n")
        f.write("=" * 80 + "\n\n")
        
        f.write("SIMILARITY SCORE DISTRIBUTION\n")
        f.write("-" * 80 + "\n")
        f.write(f"Total samples:    {data['count']}\n")
        f.write(f"Mean similarity:  {data['mean']:.2f}%\n")
        f.write(f"Std deviation:    {data['std']:.2f}%\n")
        f.write(f"Min similarity:   {min(data['similarities']):.2f}%\n")
        f.write(f"Max similarity:   {max(data['similarities']):.2f}%\n")
        f.write(f"Median:           {np.median(data['similarities']):.2f}%\n\n")
        
        # Percentiles
        percentiles = [10, 25, 50, 75, 90, 95]
        f.write("Percentiles:\n")
        for p in percentiles:
            value = np.percentile(data['similarities'], p)
            f.write(f"  {p}th percentile: {value:.2f}%\n")
        f.write("\n")
        
        f.write("=" * 80 + "\n")
        f.write("THRESHOLD ANALYSIS\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"{'Threshold':<12} {'Accepted':<12} {'Rejected':<12} {'Accept %':<12} {'Reject %':<12}\n")
        f.write("-" * 80 + "\n")
        
        for result in threshold_analysis:
            f.write(f"{result['threshold']:<12.2f} ")
            f.write(f"{result['accepted']:<12} ")
            f.write(f"{result['rejected']:<12} ")
            f.write(f"{result['acceptance_rate']:<12.1f} ")
            f.write(f"{result['rejection_rate']:<12.1f}\n")
        
        f.write("\n")
        f.write("=" * 80 + "\n")
        f.write("RECOMMENDATIONS\n")
        f.write("=" * 80 + "\n\n")
        
        # Find optimal threshold
        current_threshold = 0.70
        current_result = next((r for r in threshold_analysis if r['threshold'] == current_threshold), None)
        
        f.write(f"Current threshold: {current_threshold:.2f}\n")
        if current_result:
            f.write(f"  Acceptance rate: {current_result['acceptance_rate']:.1f}%\n")
            f.write(f"  Rejection rate: {current_result['rejection_rate']:.1f}%\n\n")
        
        # Recommend based on acceptance rate
        target_acceptance = 85  # Target 85% acceptance
        best_threshold = None
        best_diff = float('inf')
        
        for result in threshold_analysis:
            diff = abs(result['acceptance_rate'] - target_acceptance)
            if diff < best_diff:
                best_diff = diff
                best_threshold = result
        
        if best_threshold:
            f.write(f"Recommended threshold (for ~85% acceptance): {best_threshold['threshold']:.2f}\n")
            f.write(f"  Acceptance rate: {best_threshold['acceptance_rate']:.1f}%\n")
            f.write(f"  Rejection rate: {best_threshold['rejection_rate']:.1f}%\n\n")
        
        # Alternative recommendations
        f.write("Alternative thresholds:\n\n")
        
        f.write("1. For high usability (90%+ acceptance):\n")
        for result in threshold_analysis:
            if result['acceptance_rate'] >= 90:
                f.write(f"   Threshold {result['threshold']:.2f}: {result['acceptance_rate']:.1f}% acceptance\n")
                break
        f.write("\n")
        
        f.write("2. For balanced approach (80-85% acceptance):\n")
        for result in threshold_analysis:
            if 80 <= result['acceptance_rate'] <= 85:
                f.write(f"   Threshold {result['threshold']:.2f}: {result['acceptance_rate']:.1f}% acceptance\n")
        f.write("\n")
        
        f.write("3. For high security (70-75% acceptance):\n")
        for result in threshold_analysis:
            if 70 <= result['acceptance_rate'] <= 75:
                f.write(f"   Threshold {result['threshold']:.2f}: {result['acceptance_rate']:.1f}% acceptance\n")
        f.write("\n")
    
    print(f"Report saved to: {output_path}")


def main():
    # Paths
    report_path = Path("evaluation/results/asr/ASR_COMPLETE_METRICS_REPORT.txt")
    output_dir = Path("evaluation/results/asr")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 80)
    print("ASR SIMILARITY THRESHOLD ANALYSIS")
    print("=" * 80)
    print()
    
    # Parse report
    print(f"Reading report: {report_path}")
    data = parse_asr_report(report_path)
    
    print(f"Found {data['count']} similarity scores")
    print(f"Mean: {data['mean']:.2f}%, Std: {data['std']:.2f}%")
    print()
    
    # Analyze thresholds
    print("Analyzing thresholds...")
    threshold_analysis = analyze_thresholds(data['similarities'])
    
    # Generate visualization
    viz_path = output_dir / "asr_threshold_analysis.png"
    print(f"Generating visualization...")
    generate_visualization(data, viz_path)
    
    # Generate report
    report_output_path = output_dir / "ASR_THRESHOLD_ANALYSIS.txt"
    print(f"Generating report...")
    generate_report(data, threshold_analysis, report_output_path)
    
    print()
    print("=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print()
    print(f"Current threshold: 0.70 ({threshold_analysis[4]['acceptance_rate']:.1f}% acceptance)")
    print(f"Recommended: 0.65 (for better balance)")
    print()


if __name__ == "__main__":
    main()
