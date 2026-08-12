"""
Generate Complete System Visualizations

Creates updated visualizations for the complete biometric system
showing final metrics and scenario analysis.
"""

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['figure.figsize'] = (14, 10)
plt.rcParams['font.size'] = 10

def create_system_metrics_visualization():
    """Create comprehensive system metrics visualization."""
    
    fig = plt.figure(figsize=(16, 12))
    
    # Module metrics
    modules = ['Speaker\nRecognition', 'Anti-Spoofing', 'ASR']
    
    # Individual module metrics
    far_values = [0.90, 0, 0]  # AS and ASR don't have FAR
    frr_values = [16.22, 42.00, 0]  # BPCER for AS, 0 for ASR
    eer_values = [6.31, 0, 0]  # Only SR has EER
    
    # System metrics
    system_far = 0.34
    system_frr_no_retry = 69.23
    system_frr_with_retry = 51.41
    
    # Scenario acceptance rates
    scenarios = ['Genuine\nUser', 'Impostor\n(no attack)', 'TTS\nAttack', 'Voice\nCloning']
    acceptance_rates = [48.59, 0.52, 0.03, 7.57]
    rejection_rates = [51.41, 99.48, 99.97, 92.43]
    
    # Plot 1: Individual Module Metrics
    ax1 = plt.subplot(2, 3, 1)
    x = np.arange(len(modules))
    width = 0.25
    
    bars1 = ax1.bar(x - width, far_values, width, label='FAR (%)', color='#e74c3c', alpha=0.8)
    bars2 = ax1.bar(x, frr_values, width, label='FRR/BPCER (%)', color='#3498db', alpha=0.8)
    bars3 = ax1.bar(x + width, eer_values, width, label='EER (%)', color='#2ecc71', alpha=0.8)
    
    ax1.set_xlabel('Module', fontweight='bold')
    ax1.set_ylabel('Error Rate (%)', fontweight='bold')
    ax1.set_title('Individual Module Metrics', fontsize=14, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(modules)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Add value labels
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax1.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.1f}%',
                        ha='center', va='bottom', fontsize=8)
    
    # Plot 2: System-Level FAR/FRR
    ax2 = plt.subplot(2, 3, 2)
    configs = ['System\n(no retries)', 'System\n(2 retries)']
    far_sys = [system_far, system_far]
    frr_sys = [system_frr_no_retry, system_frr_with_retry]
    
    x2 = np.arange(len(configs))
    width2 = 0.35
    
    bars1 = ax2.bar(x2 - width2/2, far_sys, width2, label='FAR', color='#e74c3c', alpha=0.8)
    bars2 = ax2.bar(x2 + width2/2, frr_sys, width2, label='FRR', color='#3498db', alpha=0.8)
    
    ax2.set_ylabel('Error Rate (%)', fontweight='bold')
    ax2.set_title('System-Level Metrics', fontsize=14, fontweight='bold')
    ax2.set_xticks(x2)
    ax2.set_xticklabels(configs)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.axhline(y=1, color='green', linestyle='--', alpha=0.5, label='FAR < 1% target')
    
    # Add value labels
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.2f}%',
                    ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # Plot 3: Scenario Analysis
    ax3 = plt.subplot(2, 3, 3)
    x3 = np.arange(len(scenarios))
    
    bars1 = ax3.bar(x3, acceptance_rates, color='#2ecc71', alpha=0.8, label='Acceptance')
    bars2 = ax3.bar(x3, rejection_rates, bottom=acceptance_rates, color='#e74c3c', alpha=0.8, label='Rejection')
    
    ax3.set_ylabel('Rate (%)', fontweight='bold')
    ax3.set_title('Scenario Analysis (with retries)', fontsize=14, fontweight='bold')
    ax3.set_xticks(x3)
    ax3.set_xticklabels(scenarios, rotation=0)
    ax3.legend()
    ax3.set_ylim([0, 105])
    ax3.grid(True, alpha=0.3, axis='y')
    
    # Add percentage labels
    for i, (acc, rej) in enumerate(zip(acceptance_rates, rejection_rates)):
        if acc > 2:
            ax3.text(i, acc/2, f'{acc:.1f}%', ha='center', va='center', 
                    fontweight='bold', color='white')
        if rej > 2:
            ax3.text(i, acc + rej/2, f'{rej:.1f}%', ha='center', va='center',
                    fontweight='bold', color='white')
    
    # Plot 4: Module Contribution to System FRR
    ax4 = plt.subplot(2, 3, 4)
    
    # Calculate contribution
    sr_contribution = 16.22
    as_contribution = 42.00
    asr_contribution = 0
    
    contributions = [sr_contribution, as_contribution, asr_contribution]
    colors_contrib = ['#3498db', '#e67e22', '#9b59b6']
    
    wedges, texts, autotexts = ax4.pie(contributions, labels=modules, autopct='%1.1f%%',
                                        colors=colors_contrib, startangle=90)
    ax4.set_title('Module Contribution to FRR', fontsize=14, fontweight='bold')
    
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
    
    # Plot 5: Attack Detection Rates
    ax5 = plt.subplot(2, 3, 5)
    
    attack_types = ['TTS', 'Voice\nCloning']
    detection_rates = [97, 62]
    miss_rates = [3, 38]
    
    x5 = np.arange(len(attack_types))
    width5 = 0.6
    
    bars1 = ax5.bar(x5, detection_rates, width5, label='Detected', color='#2ecc71', alpha=0.8)
    bars2 = ax5.bar(x5, miss_rates, width5, bottom=detection_rates, label='Missed', color='#e74c3c', alpha=0.8)
    
    ax5.set_ylabel('Rate (%)', fontweight='bold')
    ax5.set_title('Attack Detection Performance', fontsize=14, fontweight='bold')
    ax5.set_xticks(x5)
    ax5.set_xticklabels(attack_types)
    ax5.legend()
    ax5.set_ylim([0, 105])
    ax5.grid(True, alpha=0.3, axis='y')
    
    # Add percentage labels
    for i, (det, miss) in enumerate(zip(detection_rates, miss_rates)):
        ax5.text(i, det/2, f'{det}%', ha='center', va='center',
                fontweight='bold', color='white', fontsize=12)
        ax5.text(i, det + miss/2, f'{miss}%', ha='center', va='center',
                fontweight='bold', color='white', fontsize=12)
    
    # Plot 6: Processing Time
    ax6 = plt.subplot(2, 3, 6)
    
    time_components = ['SR', 'AS', 'ASR', 'Total\n(avg)', 'Total\n(worst)']
    times = [500, 1000, 773, 4546, 6819]
    colors_time = ['#3498db', '#e67e22', '#9b59b6', '#2ecc71', '#e74c3c']
    
    bars = ax6.bar(time_components, times, color=colors_time, alpha=0.8)
    ax6.set_ylabel('Time (ms)', fontweight='bold')
    ax6.set_title('Processing Time Breakdown', fontsize=14, fontweight='bold')
    ax6.grid(True, alpha=0.3, axis='y')
    
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax6.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}ms',
                ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # Add time in seconds for totals
    ax6.text(3, times[3] + 200, f'({times[3]/1000:.2f}s)', ha='center', fontsize=8, style='italic')
    ax6.text(4, times[4] + 200, f'({times[4]/1000:.2f}s)', ha='center', fontsize=8, style='italic')
    
    plt.tight_layout()
    
    # Save
    output_path = Path('evaluation/plots/system_comparison/complete_system_metrics_updated.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_path}")
    
    plt.close()


def create_cascade_flow_visualization():
    """Create cascade flow visualization."""
    
    fig, ax = plt.subplots(figsize=(14, 10))
    ax.axis('off')
    
    # Title
    fig.suptitle('Complete Biometric System - Cascade Flow', 
                 fontsize=18, fontweight='bold', y=0.98)
    
    # Module boxes
    modules_data = [
        {
            'name': 'Module 1: Speaker Recognition',
            'y': 0.75,
            'metrics': [
                'Threshold: 0.65',
                'FAR: 0.90%',
                'FRR: 16.22%',
                'EER: 6.31%'
            ],
            'color': '#3498db'
        },
        {
            'name': 'Module 2: Anti-Spoofing',
            'y': 0.50,
            'metrics': [
                'Threshold: 0.50 + Features',
                'BPCER: 42% (with retries)',
                'APCER (TTS): 3%',
                'APCER (Cloning): 37.84%'
            ],
            'color': '#e67e22'
        },
        {
            'name': 'Module 3: ASR',
            'y': 0.25,
            'metrics': [
                'Threshold: 0.70',
                'Similarity: 64.42%',
                'Acceptance: 100%',
                'Processing: 773ms'
            ],
            'color': '#9b59b6'
        }
    ]
    
    # Draw modules
    for module in modules_data:
        # Box
        rect = plt.Rectangle((0.15, module['y'] - 0.08), 0.7, 0.15,
                            facecolor=module['color'], alpha=0.2,
                            edgecolor=module['color'], linewidth=2)
        ax.add_patch(rect)
        
        # Title
        ax.text(0.5, module['y'] + 0.05, module['name'],
               ha='center', va='center', fontsize=14, fontweight='bold',
               color=module['color'])
        
        # Metrics
        y_offset = module['y'] - 0.01
        for metric in module['metrics']:
            ax.text(0.5, y_offset, metric,
                   ha='center', va='center', fontsize=10)
            y_offset -= 0.025
        
        # Arrow to next module (except last)
        if module != modules_data[-1]:
            ax.annotate('', xy=(0.5, module['y'] - 0.08), 
                       xytext=(0.5, module['y'] - 0.17),
                       arrowprops=dict(arrowstyle='->', lw=2, color='black'))
            ax.text(0.52, module['y'] - 0.125, 'PASS', fontsize=9, style='italic')
    
    # System result box
    result_y = 0.05
    rect_result = plt.Rectangle((0.15, result_y - 0.03), 0.7, 0.06,
                                facecolor='#2ecc71', alpha=0.3,
                                edgecolor='#2ecc71', linewidth=3)
    ax.add_patch(rect_result)
    
    ax.text(0.5, result_y + 0.015, 'System Result: FAR 0.34% | FRR 51.41% (with retries)',
           ha='center', va='center', fontsize=12, fontweight='bold',
           color='#2ecc71')
    
    # Arrow to result
    ax.annotate('', xy=(0.5, result_y + 0.03), 
               xytext=(0.5, 0.17),
               arrowprops=dict(arrowstyle='->', lw=2, color='black'))
    
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    
    # Save
    output_path = Path('evaluation/plots/system_comparison/cascade_flow_diagram.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_path}")
    
    plt.close()


def main():
    print("=" * 80)
    print("GENERATING COMPLETE SYSTEM VISUALIZATIONS")
    print("=" * 80)
    print()
    
    print("Creating system metrics visualization...")
    create_system_metrics_visualization()
    
    print("Creating cascade flow diagram...")
    create_cascade_flow_visualization()
    
    print()
    print("=" * 80)
    print("COMPLETE")
    print("=" * 80)
    print()
    print("Generated files:")
    print("  1. complete_system_metrics_updated.png")
    print("  2. cascade_flow_diagram.png")
    print()


if __name__ == "__main__":
    main()
