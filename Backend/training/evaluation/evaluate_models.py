#!/usr/bin/env python3
"""
Sistema de evaluación para modelos biométricos entrenados.
Implementa métricas académicas estándar: EER, min-DCF, t-DCF, etc.
"""

import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging
from sklearn.metrics import roc_curve, auc
from scipy.optimize import brentq
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt
import seaborn as sns

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BiometricEvaluator:
    """Evaluador de modelos biométricos con métricas académicas."""
    
    def __init__(self, output_dir: str = "./evaluation_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def calculate_eer(self, scores: np.ndarray, labels: np.ndarray) -> Tuple[float, float]:
        """
        Calcula Equal Error Rate (EER).
        
        Args:
            scores: Array de scores de similitud/autenticidad
            labels: Array de etiquetas (1=genuine/bonafide, 0=impostor/spoof)
        
        Returns:
            (eer, threshold): EER y threshold óptimo
        """
        fpr, tpr, thresholds = roc_curve(labels, scores, pos_label=1)
        fnr = 1 - tpr
        
        # Find EER point where FPR = FNR
        eer = brentq(lambda x: 1. - x - interp1d(fpr, tpr)(x), 0., 1.)
        
        # Find threshold at EER
        eer_threshold = interp1d(fpr, thresholds)(eer)
        
        return eer, eer_threshold
    
    def calculate_min_dcf(self, scores: np.ndarray, labels: np.ndarray, 
                         p_target: float = 0.01, c_miss: float = 1, c_fa: float = 1) -> float:
        """
        Calcula minimum Detection Cost Function (min-DCF).
        
        Args:
            scores: Array de scores
            labels: Array de etiquetas
            p_target: Prior probability of target
            c_miss: Cost of miss
            c_fa: Cost of false alarm
        
        Returns:
            min_dcf: Minimum detection cost function
        """
        fpr, tpr, thresholds = roc_curve(labels, scores, pos_label=1)
        fnr = 1 - tpr
        
        # Calculate DCF for each threshold
        dcf = c_miss * fnr * p_target + c_fa * fpr * (1 - p_target)
        
        # Normalize by minimum possible cost
        c_def = min(c_miss * p_target, c_fa * (1 - p_target))
        min_dcf = np.min(dcf) / c_def
        
        return min_dcf
    
    def calculate_cllr(self, scores: np.ndarray, labels: np.ndarray) -> Tuple[float, float]:
        """
        Calcula log-likelihood ratio cost (Cllr) y calibrated Cllr.
        
        Returns:
            (cllr, min_cllr): Cllr actual y mínimo teórico
        """
        # Convert scores to log-likelihood ratios
        target_scores = scores[labels == 1]
        nontarget_scores = scores[labels == 0]
        
        # Calculate Cllr
        if len(target_scores) > 0 and len(nontarget_scores) > 0:
            cllr_target = np.mean(np.log2(1 + np.exp(-target_scores)))
            cllr_nontarget = np.mean(np.log2(1 + np.exp(nontarget_scores)))
            cllr = 0.5 * (cllr_target + cllr_nontarget)
            
            # Calculate minimum Cllr (theoretical minimum)
            all_scores = np.concatenate([target_scores, nontarget_scores])
            all_labels = np.concatenate([np.ones(len(target_scores)), np.zeros(len(nontarget_scores))])
            
            # Sort by scores
            sorted_indices = np.argsort(all_scores)[::-1]
            sorted_labels = all_labels[sorted_indices]
            
            # Calculate empirical prior
            prior = len(target_scores) / len(all_scores)
            
            # Calculate minimum Cllr
            min_cllr = self._calculate_min_cllr_from_sorted(sorted_labels, prior)
            
            return cllr, min_cllr
        else:
            return float('inf'), float('inf')
    
    def _calculate_min_cllr_from_sorted(self, sorted_labels: np.ndarray, prior: float) -> float:
        """Helper para calcular min_cllr de labels ordenados."""
        n_target = np.sum(sorted_labels)
        n_nontarget = len(sorted_labels) - n_target
        
        if n_target == 0 or n_nontarget == 0:
            return float('inf')
        
        # Calculate cumulative sums
        cum_targets = np.cumsum(sorted_labels)
        cum_nontargets = np.cumsum(1 - sorted_labels)
        
        # Calculate miss and false alarm rates
        miss_rates = (n_target - cum_targets) / n_target
        fa_rates = cum_nontargets / n_nontarget
        
        # Calculate Cllr for each threshold
        cllr_values = []
        for i in range(len(sorted_labels) + 1):
            if i == 0:
                pmiss, pfa = 1.0, 0.0
            elif i == len(sorted_labels):
                pmiss, pfa = 0.0, 1.0
            else:
                pmiss = miss_rates[i-1]
                pfa = fa_rates[i-1]
            
            if pmiss > 0 and pmiss < 1:
                cllr_target = -np.log2(1 - pmiss)
            elif pmiss == 0:
                cllr_target = 0
            else:
                cllr_target = float('inf')
            
            if pfa > 0 and pfa < 1:
                cllr_nontarget = -np.log2(1 - pfa)
            elif pfa == 0:
                cllr_nontarget = 0
            else:
                cllr_nontarget = float('inf')
            
            if not (np.isinf(cllr_target) or np.isinf(cllr_nontarget)):
                cllr = prior * cllr_target + (1 - prior) * cllr_nontarget
                cllr_values.append(cllr)
        
        return min(cllr_values) if cllr_values else float('inf')
    
    def calculate_tandem_dcf(self, asv_scores: np.ndarray, cm_scores: np.ndarray, 
                           asv_labels: np.ndarray, cm_labels: np.ndarray) -> float:
        """
        Calcula tandem Detection Cost Function (t-DCF) para anti-spoofing.
        
        Args:
            asv_scores: Scores del sistema ASV
            cm_scores: Scores del sistema countermeasure (anti-spoofing)
            asv_labels: Labels del sistema ASV
            cm_labels: Labels del sistema CM
        
        Returns:
            t_dcf: Tandem detection cost function
        """
        # Implementation of tandem DCF calculation
        # This is a simplified version - full implementation would be more complex
        
        # Combine scores using a simple strategy
        combined_scores = 0.5 * asv_scores + 0.5 * cm_scores
        combined_labels = asv_labels & cm_labels
        
        # Calculate min-DCF on combined system
        t_dcf = self.calculate_min_dcf(combined_scores, combined_labels)
        
        return t_dcf

class SpeakerVerificationEvaluator(BiometricEvaluator):
    """Evaluador específico para verificación de hablantes."""
    
    def evaluate_model(self, embeddings_file: str, trials_file: str, 
                      output_prefix: str = "speaker_eval") -> Dict[str, float]:
        """
        Evalúa modelo de verificación de hablantes.
        
        Args:
            embeddings_file: Archivo con embeddings extraídos
            trials_file: Archivo con trials de evaluación
            output_prefix: Prefijo para archivos de salida
        
        Returns:
            Dictionary con métricas calculadas
        """
        logger.info("Evaluating speaker verification model...")
        
        # Load embeddings and trials
        embeddings = self._load_embeddings(embeddings_file)
        trials = self._load_trials(trials_file)
        
        # Calculate scores
        scores, labels = self._calculate_verification_scores(embeddings, trials)
        
        # Calculate metrics
        eer, eer_threshold = self.calculate_eer(scores, labels)
        min_dcf_001 = self.calculate_min_dcf(scores, labels, p_target=0.01)
        min_dcf_0001 = self.calculate_min_dcf(scores, labels, p_target=0.001)
        cllr, min_cllr = self.calculate_cllr(scores, labels)
        
        metrics = {
            'eer': eer,
            'eer_threshold': eer_threshold,
            'min_dcf_0.01': min_dcf_001,
            'min_dcf_0.001': min_dcf_0001,
            'cllr': cllr,
            'min_cllr': min_cllr
        }
        
        # Generate plots
        self._plot_roc_curve(scores, labels, f"{output_prefix}_roc")
        self._plot_score_distribution(scores, labels, f"{output_prefix}_scores")
        
        # Save results
        self._save_results(metrics, f"{output_prefix}_metrics.json")
        
        return metrics
    
    def _load_embeddings(self, embeddings_file: str) -> Dict[str, np.ndarray]:
        """Carga embeddings desde archivo."""
        embeddings = {}
        # Implementation depends on embedding file format
        # Could be .npy, .h5, or custom format
        return embeddings
    
    def _load_trials(self, trials_file: str) -> pd.DataFrame:
        """Carga archivo de trials."""
        # Standard format: enrollment_id test_id label
        trials = pd.read_csv(trials_file, sep=' ', names=['enrollment', 'test', 'label'])
        return trials
    
    def _calculate_verification_scores(self, embeddings: Dict[str, np.ndarray], 
                                     trials: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Calcula scores de verificación para todos los trials."""
        scores = []
        labels = []
        
        for _, trial in trials.iterrows():
            enroll_id = trial['enrollment']
            test_id = trial['test']
            label = trial['label']
            
            if enroll_id in embeddings and test_id in embeddings:
                # Calculate cosine similarity
                emb1 = embeddings[enroll_id]
                emb2 = embeddings[test_id]
                
                similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
                scores.append(similarity)
                labels.append(1 if label == 'target' else 0)
        
        return np.array(scores), np.array(labels)
    
    def _plot_roc_curve(self, scores: np.ndarray, labels: np.ndarray, filename: str):
        """Genera curva ROC."""
        fpr, tpr, _ = roc_curve(labels, scores)
        roc_auc = auc(fpr, tpr)
        
        plt.figure(figsize=(8, 6))
        plt.plot(fpr, tpr, color='darkorange', lw=2, 
                label=f'ROC curve (AUC = {roc_auc:.3f})')
        plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('ROC Curve - Speaker Verification')
        plt.legend(loc="lower right")
        plt.grid(True)
        plt.savefig(self.output_dir / f"{filename}.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_score_distribution(self, scores: np.ndarray, labels: np.ndarray, filename: str):
        """Genera distribución de scores."""
        target_scores = scores[labels == 1]
        nontarget_scores = scores[labels == 0]
        
        plt.figure(figsize=(10, 6))
        plt.hist(nontarget_scores, bins=50, alpha=0.7, label='Non-target', density=True)
        plt.hist(target_scores, bins=50, alpha=0.7, label='Target', density=True)
        plt.xlabel('Score')
        plt.ylabel('Density')
        plt.title('Score Distribution')
        plt.legend()
        plt.grid(True)
        plt.savefig(self.output_dir / f"{filename}.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    def _save_results(self, metrics: Dict[str, float], filename: str):
        """Guarda resultados en archivo JSON."""
        import json
        with open(self.output_dir / filename, 'w') as f:
            json.dump(metrics, f, indent=2)

class AntiSpoofingEvaluator(BiometricEvaluator):
    """Evaluador específico para anti-spoofing."""
    
    def evaluate_model(self, scores_file: str, labels_file: str, 
                      output_prefix: str = "antispoofing_eval") -> Dict[str, float]:
        """
        Evalúa modelo anti-spoofing.
        
        Args:
            scores_file: Archivo con scores del modelo
            labels_file: Archivo con etiquetas (bonafide/spoof)
            output_prefix: Prefijo para archivos de salida
        
        Returns:
            Dictionary con métricas calculadas
        """
        logger.info("Evaluating anti-spoofing model...")
        
        # Load scores and labels
        scores = np.load(scores_file)
        labels = np.load(labels_file)  # 1=bonafide, 0=spoof
        
        # Calculate metrics
        eer, eer_threshold = self.calculate_eer(scores, labels)
        min_dcf = self.calculate_min_dcf(scores, labels)
        
        # Calculate AUC
        fpr, tpr, _ = roc_curve(labels, scores)
        roc_auc = auc(fpr, tpr)
        
        metrics = {
            'eer': eer,
            'eer_threshold': eer_threshold,
            'min_dcf': min_dcf,
            'auc': roc_auc
        }
        
        # Generate plots
        self._plot_roc_curve(scores, labels, f"{output_prefix}_roc")
        self._plot_score_distribution(scores, labels, f"{output_prefix}_scores")
        
        # Save results
        self._save_results(metrics, f"{output_prefix}_metrics.json")
        
        return metrics

def main():
    """Función principal de evaluación."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Evaluación de modelos biométricos")
    parser.add_argument("--task", required=True, 
                       choices=["speaker_verification", "anti_spoofing"],
                       help="Tipo de evaluación")
    parser.add_argument("--scores", required=True, help="Archivo de scores")
    parser.add_argument("--labels", required=True, help="Archivo de labels/trials")
    parser.add_argument("--output", default="./evaluation_results", help="Directorio de salida")
    parser.add_argument("--prefix", default="eval", help="Prefijo para archivos de salida")
    
    args = parser.parse_args()
    
    print(f"🔬 **EVALUANDO: {args.task.upper()}**")
    print("=" * 60)
    
    if args.task == "speaker_verification":
        evaluator = SpeakerVerificationEvaluator(args.output)
        metrics = evaluator.evaluate_model(args.scores, args.labels, args.prefix)
    elif args.task == "anti_spoofing":
        evaluator = AntiSpoofingEvaluator(args.output)
        metrics = evaluator.evaluate_model(args.scores, args.labels, args.prefix)
    
    print("\n📊 **RESULTADOS:**")
    for metric, value in metrics.items():
        if isinstance(value, float):
            print(f"   {metric}: {value:.4f}")
        else:
            print(f"   {metric}: {value}")
    
    print(f"\n📁 Resultados guardados en: {args.output}")

if __name__ == "__main__":
    main()