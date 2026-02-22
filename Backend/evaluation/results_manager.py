"""
Results Manager

Handles saving, loading, and exporting evaluation results in structured formats.
Supports versioning and metadata tracking for reproducibility.
"""

import json
import csv
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class ExperimentMetadata:
    """Metadata for an evaluation experiment."""
    experiment_id: str
    experiment_type: str  # "speaker_verification", "anti_spoofing", "full_system", "asr"
    timestamp: str
    dataset: str
    description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TestResult:
    """Single test result with scores and labels."""
    test_id: str
    test_type: str  # "genuine", "impostor", "spoof"
    user_id: Optional[str] = None
    similarity_score: Optional[float] = None
    spoof_probability: Optional[float] = None
    phrase_match_score: Optional[float] = None
    label: Optional[str] = None  # Ground truth
    system_decision: Optional[str] = None  # "accepted" or "rejected"
    timestamp: Optional[str] = None
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


class ResultsManager:
    """
    Manages storage and retrieval of evaluation results.
    """
    
    def __init__(self, results_dir: Path = None):
        """
        Initialize results manager.
        
        Args:
            results_dir: Directory for storing results. Defaults to evaluation/results/
        """
        if results_dir is None:
            # Default to evaluation/results relative to this file
            self.results_dir = Path(__file__).parent / "results"
        else:
            self.results_dir = Path(results_dir)
        
        # Create results directory if it doesn't exist
        self.results_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"ResultsManager initialized with directory: {self.results_dir}")
    
    def save_experiment(
        self,
        metadata: ExperimentMetadata,
        test_results: List[TestResult],
        metrics: Optional[Dict[str, Any]] = None
    ) -> Path:
        """
        Save complete experiment results to JSON file.
        
        Args:
            metadata: Experiment metadata
            test_results: List of test results
            metrics: Optional calculated metrics (FAR, FRR, EER, etc.)
            
        Returns:
            Path to saved file
        """
        experiment_data = {
            "metadata": metadata.to_dict(),
            "test_results": [r.to_dict() for r in test_results],
            "metrics": metrics or {},
            "result_count": len(test_results)
        }
        
        # Generate filename
        filename = f"{metadata.experiment_id}_{metadata.timestamp}.json"
        filepath = self.results_dir / filename
        
        # Save to JSON
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(experiment_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved experiment results to {filepath}")
        return filepath
    
    def load_experiment(self, experiment_id: str, timestamp: Optional[str] = None) -> Dict[str, Any]:
        """
        Load experiment results from file.
        
        Args:
            experiment_id: ID of experiment to load
            timestamp: Optional timestamp. If not provided, loads most recent.
            
        Returns:
            Dictionary with experiment data
        """
        if timestamp:
            filename = f"{experiment_id}_{timestamp}.json"
            filepath = self.results_dir / filename
        else:
            # Find most recent file for this experiment_id
            pattern = f"{experiment_id}_*.json"
            files = sorted(self.results_dir.glob(pattern), reverse=True)
            if not files:
                raise FileNotFoundError(f"No results found for experiment: {experiment_id}")
            filepath = files[0]
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"Loaded experiment from {filepath}")
        return data
    
    def export_to_csv(self, experiment_id: str, timestamp: Optional[str] = None) -> Path:
        """
        Export test results to CSV format for analysis in Excel/R/Python.
        
        Args:
            experiment_id: ID of experiment to export
            timestamp: Optional specific timestamp
            
        Returns:
            Path to CSV file
        """
        data = self.load_experiment(experiment_id, timestamp)
        test_results = data["test_results"]
        
        if not test_results:
            raise ValueError("No test results to export")
        
        # Generate CSV filename
        csv_filename = f"{experiment_id}_{data['metadata']['timestamp']}.csv"
        csv_path = self.results_dir / csv_filename
        
        # Get all unique keys from test results
        all_keys = set()
        for result in test_results:
            all_keys.update(result.keys())
        
        fieldnames = sorted(all_keys)
        
        # Write CSV
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(test_results)
        
        logger.info(f"Exported {len(test_results)} results to {csv_path}")
        return csv_path
    
    def get_experiment_summary(self, experiment_id: str) -> Dict[str, Any]:
        """
        Get summary statistics for an experiment.
        
        Args:
            experiment_id: ID of experiment
            
        Returns:
            Dictionary with summary information
        """
        data = self.load_experiment(experiment_id)
        results = data["test_results"]
        
        # Count by type
        type_counts = {}
        for result in results:
            test_type = result.get("test_type", "unknown")
            type_counts[test_type] = type_counts.get(test_type, 0) + 1
        
        # Extract scores
        similarities = [r["similarity_score"] for r in results if "similarity_score" in r]
        spoof_probs = [r["spoof_probability"] for r in results if "spoof_probability" in r]
        
        import numpy as np
        
        summary = {
            "experiment_id": experiment_id,
            "timestamp": data["metadata"]["timestamp"],
            "total_tests": len(results),
            "test_type_counts": type_counts,
            "metrics": data.get("metrics", {}),
        }
        
        if similarities:
            summary["similarity_stats"] = {
                "mean": float(np.mean(similarities)),
                "std": float(np.std(similarities)),
                "min": float(np.min(similarities)),
                "max": float(np.max(similarities)),
            }
        
        if spoof_probs:
            summary["spoof_stats"] = {
                "mean": float(np.mean(spoof_probs)),
                "std": float(np.std(spoof_probs)),
                "min": float(np.min(spoof_probs)),
                "max": float(np.max(spoof_probs)),
            }
        
        return summary
    
    def list_experiments(self, experiment_type: Optional[str] = None) -> List[Dict[str, str]]:
        """
        List all available experiments.
        
        Args:
            experiment_type: Optional filter by type
            
        Returns:
            List of experiment info dicts
        """
        experiments = []
        
        for filepath in sorted(self.results_dir.glob("*.json")):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    metadata = data.get("metadata", {})
                    
                    if experiment_type and metadata.get("experiment_type") != experiment_type:
                        continue
                    
                    experiments.append({
                        "experiment_id": metadata.get("experiment_id", "unknown"),
                        "type": metadata.get("experiment_type", "unknown"),
                        "timestamp": metadata.get("timestamp", "unknown"),
                        "dataset": metadata.get("dataset", "unknown"),
                        "filepath": str(filepath)
                    })
            except Exception as e:
                logger.warning(f"Failed to read {filepath}: {e}")
        
        return experiments
    
    def merge_experiments(
        self,
        experiment_ids: List[str],
        merged_id: str,
        description: str = "Merged experiment"
    ) -> Path:
        """
        Merge multiple experiments into one.
        
        Useful for combining results from multiple evaluation sessions.
        
        Args:
            experiment_ids: List of experiment IDs to merge
            merged_id: ID for merged experiment
            description: Description of merged experiment
            
        Returns:
            Path to merged results file
        """
        all_results = []
        datasets = []
        
        for exp_id in experiment_ids:
            data = self.load_experiment(exp_id)
            all_results.extend(data["test_results"])
            datasets.append(data["metadata"]["dataset"])
        
        # Create merged metadata
        merged_metadata = ExperimentMetadata(
            experiment_id=merged_id,
            experiment_type="merged",
            timestamp=datetime.now().strftime("%Y%m%d_%H%M%S"),
            dataset=", ".join(set(datasets)),
            description=f"{description} (merged from: {', '.join(experiment_ids)})"
        )
        
        # Convert results back to TestResult objects
        test_results = []
        for r in all_results:
            test_results.append(TestResult(**{k: v for k, v in r.items() if k in TestResult.__dataclass_fields__}))
        
        return self.save_experiment(merged_metadata, test_results)


def generate_experiment_id(experiment_type: str, dataset_name: str = "") -> str:
    """
    Generate a unique experiment ID.
    
    Args:
        experiment_type: Type of experiment
        dataset_name: Optional dataset name
        
    Returns:
        Experiment ID string
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if dataset_name:
        return f"{experiment_type}_{dataset_name}_{timestamp}"
    return f"{experiment_type}_{timestamp}"


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    manager = ResultsManager()
    
    # Create sample experiment
    metadata = ExperimentMetadata(
        experiment_id="speaker_verification_test",
        experiment_type="speaker_verification",
        timestamp=datetime.now().strftime("%Y%m%d_%H%M%S"),
        dataset="voxceleb_mini",
        description="Test run with 10 users"
    )
    
    # Sample results
    results = [
        TestResult(
            test_id="001",
            test_type="genuine",
            user_id="user_001",
            similarity_score=0.85,
            spoof_probability=0.05,
            label="genuine",
            system_decision="accepted"
        ),
        TestResult(
            test_id="002",
            test_type="impostor",
            user_id="user_002",
            similarity_score=0.45,
            spoof_probability=0.08,
            label="impostor",
            system_decision="rejected"
        ),
    ]
    
    # Sample metrics
    metrics = {
        "far": 0.02,
        "frr": 0.05,
        "eer": 0.035,
        "threshold": 0.65
    }
    
    # Save experiment
    filepath = manager.save_experiment(metadata, results, metrics)
    print(f"\nSaved to: {filepath}")
    
    # Load and display summary
    summary = manager.get_experiment_summary(metadata.experiment_id)
    print(f"\nExperiment Summary:")
    print(json.dumps(summary, indent=2))
    
    # Export to CSV
    csv_path = manager.export_to_csv(metadata.experiment_id)
    print(f"\nExported to CSV: {csv_path}")
