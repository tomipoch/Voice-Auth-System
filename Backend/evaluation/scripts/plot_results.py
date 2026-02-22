"""
Plot Results - Visualization Module

Generates visualizations for evaluation results:
- ROC curves
- Score distributions
- Model comparisons
- Metrics tables
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
from pathlib import Path
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class ResultsVisualizer:
    """Generate visualizations for evaluation results."""
    
    def __init__(self, output_dir: Path = None):
        """
        Initialize visualizer.
        
        Args:
            output_dir: Directory for saving plots. Defaults to evaluation/results/plots/
        """
        if output_dir is None:
            self.output_dir = Path(__file__).parent / "results" / "plots"
        else:
            self.output_dir = Path(output_dir)
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"ResultsVisualizer initialized, output: {self.output_dir}")
    
    def plot_roc_curve(
        self,
        far_values: np.ndarray,
        tpr_values: np.ndarray,
        title: str = "ROC Curve",
        filename: str = "roc_curve.png",
        eer_point: Optional[tuple] = None
    ) -> Path:
        """
        Plot ROC curve (FAR vs TPR).
        
        Args:
            far_values: False Acceptance Rate values
            tpr_values: True Positive Rate values (1 - FRR)
            title: Plot title
            filename: Output filename
            eer_point: Optional (FAR, TPR) point to mark EER
            
        Returns:
            Path to saved plot
        """
        plt.figure(figsize=(10, 8))
        plt.plot(far_values, tpr_values, 'b-', linewidth=2, label='ROC Curve')
        
        # Add EER point if provided
        if eer_point:
            plt.plot(eer_point[0], eer_point[1], 'ro', markersize=10, 
                    label=f'EER ({eer_point[0]:.3f}, {eer_point[1]:.3f})')
        
        # Diagonal line (random classifier)
        plt.plot([0, 1], [0, 1], 'k--', linewidth=1, alpha=0.3, label='Random')
        
        plt.xlabel('False Acceptance Rate (FAR)', fontsize=12)
        plt.ylabel('True Positive Rate (1 - FRR)', fontsize=12)
        plt.title(title, fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3)
        plt.legend(fontsize=10)
        plt.xlim([0, 1])
        plt.ylim([0, 1])
        plt.tight_layout()
        
        output_path = self.output_dir / filename
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"ROC curve saved to: {output_path}")
        return output_path
    
    def plot_score_distributions(
        self,
        genuine_scores: np.ndarray,
        impostor_scores: np.ndarray,
        title: str = "Score Distributions",
        filename: str = "score_distributions.png",
        threshold: Optional[float] = None
    ) -> Path:
        """
        Plot distribution of genuine vs impostor scores.
        
        Args:
            genuine_scores: Scores from genuine attempts
            impostor_scores: Scores from impostor attempts
            title: Plot title
            filename: Output filename
            threshold: Optional threshold line to draw
            
        Returns:
            Path to saved plot
        """
        plt.figure(figsize=(12, 6))
        
        # Plot histograms
        bins = np.linspace(0, 1, 50)
        plt.hist(genuine_scores, bins=bins, alpha=0.5, color='green', 
                label=f'Genuine (n={len(genuine_scores)})', density=True)
        plt.hist(impostor_scores, bins=bins, alpha=0.5, color='red', 
                label=f'Impostor (n={len(impostor_scores)})', density=True)
        
        # Add threshold line
        if threshold:
            plt.axvline(x=threshold, color='blue', linestyle='--', linewidth=2,
                       label=f'Threshold = {threshold:.3f}')
        
        plt.xlabel('Similarity Score', fontsize=12)
        plt.ylabel('Density', fontsize=12)
        plt.title(title, fontsize=14, fontweight='bold')
        plt.legend(fontsize=10)
        plt.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()
        
        output_path = self.output_dir / filename
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Score distributions saved to: {output_path}")
        return output_path
    
    def plot_model_comparison(
        self,
        model_names: List[str],
        model_eers: List[float],
        title: str = "Model Comparison - EER",
        filename: str = "model_comparison.png"
    ) -> Path:
        """
        Plot comparison of multiple models.
        
        Args:
            model_names: List of model names
            model_eers: List of EER values for each model
            title: Plot title
            filename: Output filename
            
        Returns:
            Path to saved plot
        """
        plt.figure(figsize=(10, 6))
        
        colors = plt.cm.viridis(np.linspace(0, 0.9, len(model_names)))
        bars = plt.bar(model_names, model_eers, color=colors, alpha=0.8)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.3f}',
                    ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        plt.ylabel('Equal Error Rate (EER)', fontsize=12)
        plt.title(title, fontsize=14, fontweight='bold')
        plt.ylim([0, max(model_eers) * 1.2])
        plt.grid(True, alpha=0.3, axis='y')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        output_path = self.output_dir / filename
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Model comparison saved to: {output_path}")
        return output_path
    
    def create_metrics_table(
        self,
        metrics_dict: Dict,
        title: str = "Evaluation Metrics",
        filename: str = "metrics_table.png"
    ) -> Path:
        """
        Create a visual table of metrics.
        
        Args:
            metrics_dict: Dictionary of metrics
            title: Table title
            filename: Output filename
            
        Returns:
            Path to saved image
        """
        fig, ax = plt.subplots(figsize=(8, len(metrics_dict) * 0.5 + 1))
        ax.axis('tight')
        ax.axis('off')
        
        # Prepare data for table
        table_data = []
        for key, value in metrics_dict.items():
            if isinstance(value, float):
                formatted_value = f"{value:.4f}"
            else:
                formatted_value = str(value)
            table_data.append([key.replace('_', ' ').title(), formatted_value])
        
        table = ax.table(cellText=table_data, colLabels=['Metric', 'Value'],
                        cellLoc='left', loc='center',
                        colWidths=[0.6, 0.4])
        
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 2)
        
        # Style header
        for i in range(2):
            table[(0, i)].set_facecolor('#4CAF50')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        # Alternate row colors
        for i in range(1, len(table_data) + 1):
            if i % 2 == 0:
                for j in range(2):
                    table[(i, j)].set_facecolor('#f0f0f0')
        
        plt.title(title, fontsize=14, fontweight='bold', pad=20)
        plt.tight_layout()
        
        output_path = self.output_dir / filename
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Metrics table saved to: {output_path}")
        return output_path
    
    def visualize_experiment(self, experiment_filepath: Path) -> List[Path]:
        """
        Create all visualizations for an experiment.
        
        Args:
            experiment_filepath: Path to experiment JSON file
            
        Returns:
            List of paths to generated plots
        """
        with open(experiment_filepath, 'r') as f:
            data = json.load(f)
        
        experiment_id = data['metadata']['experiment_id']
        experiment_type = data['metadata']['experiment_type']
        
        generated_plots = []
        
        # Extract scores based on experiment type
        if experiment_type == 'speaker_verification':
            # Extract genuine and impostor scores
            results = data['test_results']
            genuine_scores = [r['similarity_score'] for r in results if r['test_type'] == 'genuine']
            impostor_scores = [r['similarity_score'] for r in results if r['test_type'] == 'impostor']
            
            if genuine_scores and impostor_scores:
                # Score distributions
                dist_plot = self.plot_score_distributions(
                    np.array(genuine_scores),
                    np.array(impostor_scores),
                    title=f"Score Distributions - {experiment_id}",
                    filename=f"{experiment_id}_distributions.png"
                )
                generated_plots.append(dist_plot)
        
        elif experiment_type == 'anti_spoofing':
            # Similar visualization for anti-spoofing
            results = data['test_results']
            genuine_scores = [1 - r['spoof_probability'] for r in results if r['test_type'] == 'genuine']
            spoofed_scores = [1 - r['spoof_probability'] for r in results if r['test_type'] == 'spoof']
            
            if genuine_scores and spoofed_scores:
                dist_plot = self.plot_score_distributions(
                    np.array(genuine_scores),
                    np.array(spoofed_scores),
                    title=f"Anti-Spoofing Score Distributions - {experiment_id}",
                    filename=f"{experiment_id}_distributions.png"
                )
                generated_plots.append(dist_plot)
        
        # Metrics table
        if data.get('metrics'):
            metrics_plot = self.create_metrics_table(
                data['metrics'],
                title=f"Metrics - {experiment_id}",
                filename=f"{experiment_id}_metrics.png"
            )
            generated_plots.append(metrics_plot)
        
        logger.info(f"Generated {len(generated_plots)} plots for {experiment_id}")
        return generated_plots


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    visualizer = ResultsVisualizer()
    
    # Simulate data
    np.random.seed(42)
    genuine = np.random.beta(8, 2, 100)
    impostor = np.random.beta(2, 5, 150)
    
    # Create visualizations
    visualizer.plot_score_distributions(genuine, impostor, threshold=0.65)
    
    # Mock ROC curve
    thresholds = np.linspace(0, 1, 100)
    far = 1 - thresholds
    tpr = thresholds
    visualizer.plot_roc_curve(far, tpr, eer_point=(0.04, 0.96))
    
    # Model comparison
    visualizer.plot_model_comparison(
        ['AASIST', 'RawNet2', 'ResNet', 'Ensemble'],
        [0.05, 0.07, 0.06, 0.03]
    )
    
    # Metrics table
    metrics = {
        'EER': 0.04,
        'FAR_at_EER': 0.04,
        'FRR_at_EER': 0.04,
        'Genuine_Mean': 0.806,
        'Impostor_Mean': 0.286
    }
    visualizer.create_metrics_table(metrics)
    
    print(f"\nPlots saved to: {visualizer.output_dir}")
