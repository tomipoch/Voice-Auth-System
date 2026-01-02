"""
Interactive Annotation Script

Allows manual annotation of evaluation results collected via frontend.
User marks each verification attempt as genuine or impostor, then
FAR and FRR are calculated automatically.

Usage:
    python annotate_results.py --session manual_eval_20251217_020000
"""

import sys
import argparse
import json
import logging
from pathlib import Path
from typing import Dict, List

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)


class ResultAnnotator:
    """Interactive annotator for evaluation results."""
    
    def __init__(self, results_dir: Path = None):
        if results_dir is None:
            self.results_dir = Path(__file__).parent.parent / "results"
        else:
            self.results_dir = Path(results_dir)
    
    def load_session(self, session_id: str) -> Dict:
        """Load session data from file."""
        filepath = self.results_dir / f"{session_id}.json"
        
        if not filepath.exists():
            raise FileNotFoundError(f"Session file not found: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_session(self, session_id: str, data: Dict):
        """Save annotated session data."""
        filepath = self.results_dir / f"{session_id}.json"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Saved annotated data to: {filepath}")
    
    def annotate_attempts(self, attempts: List[Dict]) -> List[Dict]:
        """
        Interactively annotate verification attempts.
        
        Args:
            attempts: List of verification attempts
            
        Returns:
            List of annotated attempts
        """
        print(f"\n{'='*70}")
        print(f"  INTERACTIVE ANNOTATION")
        print(f"{'='*70}")
        print(f"Total attempts to annotate: {len(attempts)}")
        print(f"\nFor each attempt, mark if it was:")
        print(f"  [g] GENUINE - The actual user verifying themselves")
        print(f"  [i] IMPOSTOR - Someone else trying to impersonate")
        print(f"  [s] SKIP - Skip this attempt")
        print(f"  [q] QUIT - Save and quit")
        print(f"{'='*70}\n")
        
        annotated_count = 0
        
        for i, attempt in enumerate(attempts, 1):
            # Skip already annotated
            if attempt.get("manual_annotation"):
                print(f"[{i}/{len(attempts)}] Already annotated - SKIPPING")
                continue
            
            print(f"\n{'─'*70}")
            print(f"Attempt #{i} of {len(attempts)}")
            print(f"{'─'*70}")
            print(f"  User ID: {attempt['user_id']}")
            print(f"  Timestamp: {attempt['timestamp']}")
            print(f"  Similarity Score: {attempt['similarity_score']:.3f}")
            if attempt.get('spoof_probability') is not None:
                print(f"  Spoof Probability: {attempt['spoof_probability']:.3f}")
            if attempt.get('phrase_match_score') is not None:
                print(f"  Phrase Match: {attempt['phrase_match_score']:.3f}")
            print(f"  System Decision: {attempt['system_decision'].upper()}")
            print(f"  Threshold Used: {attempt['threshold_used']:.3f}")
            print(f"{'─'*70}")
            
            while True:
                choice = input(f"\nWas this GENUINE or IMPOSTOR? [g/i/s/q]: ").lower().strip()
                
                if choice == 'q':
                    print("\n⚠️  Quitting annotation...")
                    return attempts
                
                if choice == 's':
                    print("  → Skipped")
                    break
                
                if choice == 'g':
                    attempt['manual_annotation'] = 'genuine'
                    attempt['is_genuine'] = True
                    annotated_count += 1
                    
                    # Determine if this was a correct decision
                    was_accepted = attempt['system_decision'] == 'accepted'
                    if was_accepted:
                        print(f"  ✓ Annotated as GENUINE → TRUE ACCEPTANCE")
                    else:
                        print(f"  ⚠️ Annotated as GENUINE → FALSE REJECTION (FRR)")
                    break
                
                elif choice == 'i':
                    attempt['manual_annotation'] = 'impostor'
                    attempt['is_genuine'] = False
                    annotated_count += 1
                    
                    # Determine if this was a correct decision
                    was_accepted = attempt['system_decision'] == 'accepted'
                    if was_accepted:
                        print(f"  ⚠️ Annotated as IMPOSTOR → FALSE ACCEPTANCE (FAR)")
                    else:
                        print(f"  ✓ Annotated as IMPOSTOR → TRUE REJECTION")
                    break
                
                else:
                    print("  Invalid choice. Please enter 'g', 'i', 's', or 'q'")
        
        print(f"\n{'='*70}")
        print(f"Annotation complete! Annotated {annotated_count} attempts")
        print(f"{'='*70}\n")
        
        return attempts
    
    def calculate_metrics(self, attempts: List[Dict]) -> Dict:
        """
        Calculate FAR and FRR from annotated attempts.
        
        Args:
            attempts: List of annotated verification attempts
            
        Returns:
            Dictionary with metrics
        """
        # Filter only annotated attempts
        annotated = [a for a in attempts if a.get('manual_annotation')]
        
        if not annotated:
            print("⚠️  No annotated attempts found!")
            return {}
        
        # Separate genuine and impostor
        genuine_attempts = [a for a in annotated if a['is_genuine']]
        impostor_attempts = [a for a in annotated if not a['is_genuine']]
        
        # Calculate FAR: impostors accepted / total impostors
        false_accepts = sum(1 for a in impostor_attempts if a['system_decision'] == 'accepted')
        FAR = false_accepts / len(impostor_attempts) if impostor_attempts else 0.0
        
        # Calculate FRR: genuines rejected / total genuines
        false_rejects = sum(1 for a in genuine_attempts if a['system_decision'] == 'rejected')
        FRR = false_rejects / len(genuine_attempts) if genuine_attempts else 0.0
        
        metrics = {
            "total_annotated": len(annotated),
            "total_genuine": len(genuine_attempts),
            "total_impostor": len(impostor_attempts),
            "false_acceptances": false_accepts,
            "false_rejections": false_rejects,
            "FAR": FAR,
            "FRR": FRR,
            "accuracy": 1.0 - ((false_accepts + false_rejects) / len(annotated)) if annotated else 0.0
        }
        
        return metrics
    
    def run_annotation(self, session_id: str):
        """
        Run complete annotation workflow.
        
        Args:
            session_id: Session ID to annotate
        """
        # Load session
        print(f"Loading session: {session_id}...")
        data = self.load_session(session_id)
        
        attempts = data.get('verification_attempts', [])
        
        if not attempts:
            print("⚠️  No verification attempts found in this session!")
            return
        
        # Annotate
        annotated_attempts = self.annotate_attempts(attempts)
        
        # Update data
        data['verification_attempts'] = annotated_attempts
        
        # Calculate metrics
        metrics = self.calculate_metrics(annotated_attempts)
        data['manual_evaluation_metrics'] = metrics
        
        # Display metrics
        if metrics:
            print(f"\n{'='*70}")
            print(f"  EVALUATION METRICS")
            print(f"{'='*70}")
            print(f"Total annotated: {metrics['total_annotated']}")
            print(f"  Genuine attempts: {metrics['total_genuine']}")
            print(f"  Impostor attempts: {metrics['total_impostor']}")
            print(f"\nErrors:")
            print(f"  False Acceptances (FAR): {metrics['false_acceptances']} ({metrics['FAR']:.1%})")
            print(f"  False Rejections (FRR): {metrics['false_rejections']} ({metrics['FRR']:.1%})")
            print(f"\nOverall Accuracy: {metrics['accuracy']:.1%}")
            print(f"{'='*70}\n")
        
        # Save
        self.save_session(session_id, data)
        
        # Export metrics to separate file
        metrics_filepath = self.results_dir / f"{session_id}_metrics.json"
        with open(metrics_filepath, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2)
        print(f"✓ Metrics saved to: {metrics_filepath}")


def main():
    parser = argparse.ArgumentParser(description="Annotate evaluation results")
    parser.add_argument("--session", type=str, required=True,
                        help="Session ID to annotate")
    parser.add_argument("--results-dir", type=str, default=None,
                        help="Results directory (default: evaluation/results/)")
    
    args = parser.parse_args()
    
    annotator = ResultAnnotator(
        results_dir=Path(args.results_dir) if args.results_dir else None
    )
    
    try:
        annotator.run_annotation(args.session)
        print("\n✓ Annotation complete!")
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Annotation cancelled by user")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Annotation failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
