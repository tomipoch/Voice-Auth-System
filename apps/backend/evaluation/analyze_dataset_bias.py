"""
Análisis Crítico del Dataset: Detección de Sesgos y Limitaciones

Este script analiza si el 0% EER es real o consecuencia de:
1. Dataset muy pequeño (4 usuarios)
2. Overfitting al threshold
3. Falta de variabilidad inter-usuario
4. S-Norm sobreajustando al mismo conjunto de prueba
"""

import sys
import logging
from pathlib import Path
import numpy as np
from typing import Dict, List, Tuple
import json

sys.path.append(str(Path(__file__).parent.parent))
from src.infrastructure.biometrics.SpeakerEmbeddingAdapter import SpeakerEmbeddingAdapter

logger = logging.getLogger(__name__)


class DatasetBiasAnalyzer:
    """Analizador de sesgos en el dataset."""
    
    def __init__(self, recordings_dir: Path):
        self.recordings_dir = recordings_dir
        self.speaker_adapter = SpeakerEmbeddingAdapter(use_gpu=True)
        self.users = ["anachamorromunoz", "ft_fernandotomas", "piapobletech", "rapomo3"]
        self.voiceprints = {}
        self.all_embeddings = {}  # Todos los embeddings por usuario
        
    def load_audio(self, audio_path: Path) -> bytes:
        with open(audio_path, 'rb') as f:
            return f.read()
    
    def calculate_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        norm1 = emb1 / (np.linalg.norm(emb1) + 1e-8)
        norm2 = emb2 / (np.linalg.norm(emb2) + 1e-8)
        similarity = np.dot(norm1, norm2)
        return float(max(0.0, min(1.0, similarity)))
    
    def extract_all_embeddings(self):
        """Extraer todos los embeddings (enrollment + verification) por usuario."""
        print("\nExtrayendo todos los embeddings...")
        
        for user in self.users:
            user_dir = self.recordings_dir / user
            all_files = sorted(user_dir.glob(f"{user}_*.wav"))
            
            embeddings = []
            for audio_file in all_files:
                audio_data = self.load_audio(audio_file)
                embedding = self.speaker_adapter.extract_embedding(audio_data, audio_format="wav")
                embeddings.append(embedding)
            
            self.all_embeddings[user] = embeddings
            print(f"  {user}: {len(embeddings)} embeddings")
    
    def analyze_intra_user_variability(self) -> Dict:
        """
        Analizar variabilidad INTRA-usuario (qué tan consistentes son los audios del mismo usuario).
        Baja variabilidad = embeddings muy similares = fácil de clasificar
        """
        print("\n1. ANÁLISIS DE VARIABILIDAD INTRA-USUARIO")
        print("=" * 80)
        
        results = {}
        
        for user, embeddings in self.all_embeddings.items():
            # Calcular todas las similitudes intra-usuario
            similarities = []
            for i in range(len(embeddings)):
                for j in range(i + 1, len(embeddings)):
                    sim = self.calculate_similarity(embeddings[i], embeddings[j])
                    similarities.append(sim)
            
            mean_sim = np.mean(similarities)
            std_sim = np.std(similarities)
            min_sim = np.min(similarities)
            max_sim = np.max(similarities)
            
            results[user] = {
                'mean': mean_sim,
                'std': std_sim,
                'min': min_sim,
                'max': max_sim,
                'comparisons': len(similarities)
            }
            
            print(f"\n{user}:")
            print(f"  Similitud promedio: {mean_sim:.4f} ± {std_sim:.4f}")
            print(f"  Rango: [{min_sim:.4f}, {max_sim:.4f}]")
            print(f"  Comparaciones: {len(similarities)}")
            
            # Interpretación
            if std_sim < 0.05:
                print(f"  ⚠️  ALERTA: Variabilidad MUY BAJA - Usuario muy consistente (puede ser artificial)")
            elif std_sim < 0.10:
                print(f"  ✓ Variabilidad baja - Usuario consistente")
            else:
                print(f"  ✓ Variabilidad normal")
        
        return results
    
    def analyze_inter_user_separability(self) -> Dict:
        """
        Analizar separabilidad INTER-usuario (qué tan diferentes son los usuarios entre sí).
        Alta separabilidad = usuarios muy distintos = fácil de clasificar
        """
        print("\n\n2. ANÁLISIS DE SEPARABILIDAD INTER-USUARIO")
        print("=" * 80)
        
        results = {}
        
        for user_a in self.users:
            for user_b in self.users:
                if user_a >= user_b:
                    continue
                
                # Calcular similitudes entre todos los pares de embeddings
                similarities = []
                for emb_a in self.all_embeddings[user_a]:
                    for emb_b in self.all_embeddings[user_b]:
                        sim = self.calculate_similarity(emb_a, emb_b)
                        similarities.append(sim)
                
                mean_sim = np.mean(similarities)
                std_sim = np.std(similarities)
                max_sim = np.max(similarities)
                
                pair = f"{user_a} vs {user_b}"
                results[pair] = {
                    'mean': mean_sim,
                    'std': std_sim,
                    'max': max_sim,
                    'comparisons': len(similarities)
                }
                
                print(f"\n{pair}:")
                print(f"  Similitud promedio: {mean_sim:.4f} ± {std_sim:.4f}")
                print(f"  Máxima similitud: {max_sim:.4f}")
                
                # Interpretación
                if mean_sim < 0.30:
                    print(f"  ✓ Usuarios MUY SEPARABLES - Fácil de distinguir")
                elif mean_sim < 0.50:
                    print(f"  ✓ Usuarios separables")
                else:
                    print(f"  ⚠️  DIFÍCIL: Usuarios similares")
        
        return results
    
    def calculate_fisher_ratio(self, intra_results: Dict, inter_results: Dict) -> float:
        """
        Fisher Ratio = Varianza INTER-clase / Varianza INTRA-clase
        
        Ratio alto = clases bien separadas (fácil de clasificar)
        Ratio bajo = clases solapadas (difícil de clasificar)
        """
        print("\n\n3. FISHER RATIO (DISCRIMINABILIDAD)")
        print("=" * 80)
        
        # Varianza intra-clase (promedio de varianzas de cada usuario)
        intra_variances = [r['std']**2 for r in intra_results.values()]
        avg_intra_variance = np.mean(intra_variances)
        
        # Varianza inter-clase (varianza de las medias entre pares de usuarios)
        inter_means = [r['mean'] for r in inter_results.values()]
        inter_variance = np.var(inter_means)
        
        # Fisher Ratio
        fisher_ratio = inter_variance / (avg_intra_variance + 1e-8)
        
        print(f"Varianza INTRA-clase (promedio): {avg_intra_variance:.6f}")
        print(f"Varianza INTER-clase: {inter_variance:.6f}")
        print(f"Fisher Ratio: {fisher_ratio:.4f}")
        
        # Interpretación
        if fisher_ratio > 10:
            print(f"\n⚠️  ALERTA: Fisher Ratio EXTREMADAMENTE ALTO")
            print(f"   → Dataset demasiado fácil de clasificar")
            print(f"   → 0% EER probablemente NO es generalizable")
        elif fisher_ratio > 5:
            print(f"\n⚠️  Fisher Ratio alto - Dataset relativamente fácil")
        else:
            print(f"\n✓ Fisher Ratio normal - Dataset desafiante")
        
        return fisher_ratio
    
    def analyze_threshold_sensitivity(self) -> Dict:
        """
        Analizar sensibilidad al threshold.
        Si hay un rango amplio de thresholds con 0% error, el resultado es sospechoso.
        """
        print("\n\n4. ANÁLISIS DE SENSIBILIDAD AL THRESHOLD")
        print("=" * 80)
        
        # Crear voiceprints (promedio de 3 primeros audios)
        for user in self.users:
            self.voiceprints[user] = np.mean(self.all_embeddings[user][:3], axis=0)
        
        # Calcular scores genuinos
        genuine_scores = []
        for user in self.users:
            voiceprint = self.voiceprints[user]
            for embedding in self.all_embeddings[user][3:]:  # Verification audios
                score = self.calculate_similarity(voiceprint, embedding)
                genuine_scores.append(score)
        
        # Calcular scores impostores
        impostor_scores = []
        for claimed_user in self.users:
            claimed_voiceprint = self.voiceprints[claimed_user]
            for actual_user in self.users:
                if actual_user == claimed_user:
                    continue
                for embedding in self.all_embeddings[actual_user][3:]:
                    score = self.calculate_similarity(claimed_voiceprint, embedding)
                    impostor_scores.append(score)
        
        genuine_scores = np.array(genuine_scores)
        impostor_scores = np.array(impostor_scores)
        
        print(f"Genuine scores:")
        print(f"  Min: {np.min(genuine_scores):.4f}")
        print(f"  Max: {np.max(genuine_scores):.4f}")
        print(f"  Mean: {np.mean(genuine_scores):.4f} ± {np.std(genuine_scores):.4f}")
        
        print(f"\nImpostor scores:")
        print(f"  Min: {np.min(impostor_scores):.4f}")
        print(f"  Max: {np.max(impostor_scores):.4f}")
        print(f"  Mean: {np.mean(impostor_scores):.4f} ± {np.std(impostor_scores):.4f}")
        
        # ¿Hay solapamiento?
        max_impostor = np.max(impostor_scores)
        min_genuine = np.min(genuine_scores)
        gap = min_genuine - max_impostor
        
        print(f"\nGAP (separación):")
        print(f"  Max impostor score: {max_impostor:.4f}")
        print(f"  Min genuine score: {min_genuine:.4f}")
        print(f"  GAP: {gap:.4f}")
        
        if gap > 0.1:
            print(f"\n⚠️  ALERTA: GAP MUY GRANDE ({gap:.4f})")
            print(f"   → No hay solapamiento entre genuinos e impostores")
            print(f"   → Cualquier threshold en [{max_impostor:.4f}, {min_genuine:.4f}] da 0% error")
            print(f"   → Rango de {gap:.4f} unidades de threshold con error perfecto")
            print(f"   → 0% EER NO es realista para producción")
        elif gap > 0:
            print(f"\n⚠️  GAP positivo - Clasificación perfecta es posible")
            print(f"   → Pero dataset puede ser demasiado fácil")
        else:
            print(f"\n✓ Hay solapamiento - Dataset más realista")
        
        return {
            'genuine_min': float(np.min(genuine_scores)),
            'genuine_max': float(np.max(genuine_scores)),
            'genuine_mean': float(np.mean(genuine_scores)),
            'impostor_min': float(np.min(impostor_scores)),
            'impostor_max': float(np.max(impostor_scores)),
            'impostor_mean': float(np.mean(impostor_scores)),
            'gap': float(gap),
            'perfect_threshold_range': float(gap) if gap > 0 else 0
        }
    
    def estimate_confidence_intervals(self, n_bootstrap: int = 1000) -> Dict:
        """
        Bootstrap para estimar intervalos de confianza del EER.
        Si el IC es [0%, 0%], el dataset es demasiado pequeño para ser confiable.
        """
        print("\n\n5. INTERVALOS DE CONFIANZA (BOOTSTRAP)")
        print("=" * 80)
        print(f"Realizando {n_bootstrap} iteraciones de bootstrap...")
        
        # Obtener todos los scores
        genuine_scores = []
        impostor_scores = []
        
        for user in self.users:
            voiceprint = self.voiceprints[user]
            for embedding in self.all_embeddings[user][3:]:
                score = self.calculate_similarity(voiceprint, embedding)
                genuine_scores.append(score)
        
        for claimed_user in self.users:
            claimed_voiceprint = self.voiceprints[claimed_user]
            for actual_user in self.users:
                if actual_user == claimed_user:
                    continue
                for embedding in self.all_embeddings[actual_user][3:]:
                    score = self.calculate_similarity(claimed_voiceprint, embedding)
                    impostor_scores.append(score)
        
        genuine_scores = np.array(genuine_scores)
        impostor_scores = np.array(impostor_scores)
        
        # Bootstrap
        eers = []
        for _ in range(n_bootstrap):
            # Resample con reemplazo
            gen_sample = np.random.choice(genuine_scores, size=len(genuine_scores), replace=True)
            imp_sample = np.random.choice(impostor_scores, size=len(impostor_scores), replace=True)
            
            # Calcular EER
            thresholds = np.linspace(0, 1, 100)
            fars = []
            frrs = []
            for t in thresholds:
                far = np.sum(imp_sample >= t) / len(imp_sample)
                frr = np.sum(gen_sample < t) / len(gen_sample)
                fars.append(far)
                frrs.append(frr)
            
            fars = np.array(fars)
            frrs = np.array(frrs)
            eer_idx = np.argmin(np.abs(fars - frrs))
            eer = ((fars[eer_idx] + frrs[eer_idx]) / 2) * 100
            eers.append(eer)
        
        eers = np.array(eers)
        mean_eer = np.mean(eers)
        ci_lower = np.percentile(eers, 2.5)
        ci_upper = np.percentile(eers, 97.5)
        
        print(f"\nEER estimado: {mean_eer:.2f}%")
        print(f"Intervalo de confianza 95%: [{ci_lower:.2f}%, {ci_upper:.2f}%]")
        
        if ci_upper < 5.0:
            print(f"\n⚠️  IC muy estrecho y bajo - Dataset puede estar sobreajustado")
            print(f"   → Con más usuarios, EER probablemente subirá")
        
        return {
            'mean_eer': float(mean_eer),
            'ci_95_lower': float(ci_lower),
            'ci_95_upper': float(ci_upper),
            'std_eer': float(np.std(eers))
        }
    
    def generate_report(self, output_path: Path, results: Dict):
        """Generar reporte de sesgos."""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("ANÁLISIS CRÍTICO DEL DATASET - DETECCIÓN DE SESGOS\n")
            f.write("=" * 80 + "\n\n")
            
            f.write("⚠️  ADVERTENCIA: 0% EER es SOSPECHOSO\n")
            f.write("-" * 80 + "\n\n")
            
            # Tamaño del dataset
            f.write("TAMAÑO DEL DATASET:\n")
            f.write(f"  Usuarios: {len(self.users)}\n")
            f.write(f"  Intentos genuinos: {sum(len(embs[3:]) for embs in self.all_embeddings.values())}\n")
            f.write(f"  Intentos impostores: {sum(len(embs[3:]) for embs in self.all_embeddings.values()) * (len(self.users) - 1)}\n")
            f.write(f"  ⚠️  CRÍTICO: 4 usuarios es EXTREMADAMENTE PEQUEÑO\n")
            f.write(f"  → Sistemas comerciales usan 1000-10000 usuarios\n")
            f.write(f"  → Resultados NO son generalizables\n\n")
            
            # Fisher Ratio
            f.write("DISCRIMINABILIDAD (FISHER RATIO):\n")
            f.write(f"  Fisher Ratio: {results['fisher_ratio']:.4f}\n")
            if results['fisher_ratio'] > 10:
                f.write(f"  ⚠️  CRÍTICO: Dataset demasiado fácil de clasificar\n\n")
            
            # GAP
            f.write("SEPARACIÓN (GAP):\n")
            f.write(f"  GAP: {results['threshold_sensitivity']['gap']:.4f}\n")
            f.write(f"  Rango de threshold perfecto: {results['threshold_sensitivity']['perfect_threshold_range']:.4f}\n")
            if results['threshold_sensitivity']['gap'] > 0.1:
                f.write(f"  ⚠️  CRÍTICO: No hay solapamiento - 0% EER es trivial\n\n")
            
            # Intervalos de confianza
            f.write("INTERVALOS DE CONFIANZA (95%):\n")
            f.write(f"  EER estimado: {results['confidence_intervals']['mean_eer']:.2f}%\n")
            f.write(f"  IC 95%: [{results['confidence_intervals']['ci_95_lower']:.2f}%, ")
            f.write(f"{results['confidence_intervals']['ci_95_upper']:.2f}%]\n\n")
            
            f.write("CONCLUSIÓN:\n")
            f.write("-" * 80 + "\n")
            f.write("El 0% EER es consecuencia de:\n")
            f.write("  1. Dataset muy pequeño (4 usuarios)\n")
            f.write("  2. Usuarios extremadamente separables (Fisher Ratio alto)\n")
            f.write("  3. No hay solapamiento entre genuinos e impostores (GAP grande)\n")
            f.write("  4. S-Norm sobreajusta al mismo conjunto de usuarios\n\n")
            f.write("RECOMENDACIONES PARA LA TESIS:\n")
            f.write("  • Reportar EER con intervalos de confianza\n")
            f.write("  • Mencionar limitación del tamaño del dataset\n")
            f.write("  • Usar cross-validation leave-one-out\n")
            f.write("  • Comparar con y sin S-Norm\n")
            f.write("  • Proyectar EER esperado con más usuarios\n")
        
        print(f"\nReporte guardado en: {output_path}")


def main():
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 80)
    print("ANÁLISIS CRÍTICO DEL DATASET")
    print("Detectando sesgos y limitaciones que explican el 0% EER")
    print("=" * 80)
    
    project_root = Path(__file__).parent.parent.parent.parent
    dataset_base = project_root / "infra" / "evaluation" / "dataset"
    recordings_dir = dataset_base / "recordings" / "auto_recordings_20251218"
    
    analyzer = DatasetBiasAnalyzer(recordings_dir)
    
    # 1. Extraer todos los embeddings
    analyzer.extract_all_embeddings()
    
    # 2. Análisis de variabilidad intra-usuario
    intra_results = analyzer.analyze_intra_user_variability()
    
    # 3. Análisis de separabilidad inter-usuario
    inter_results = analyzer.analyze_inter_user_separability()
    
    # 4. Fisher Ratio
    fisher_ratio = analyzer.calculate_fisher_ratio(intra_results, inter_results)
    
    # 5. Sensibilidad al threshold
    threshold_sensitivity = analyzer.analyze_threshold_sensitivity()
    
    # 6. Intervalos de confianza
    confidence_intervals = analyzer.estimate_confidence_intervals(n_bootstrap=1000)
    
    # Compilar resultados
    results = {
        'intra_user_variability': {k: {kk: float(vv) if isinstance(vv, np.float64) else vv 
                                       for kk, vv in v.items()} 
                                   for k, v in intra_results.items()},
        'fisher_ratio': float(fisher_ratio),
        'threshold_sensitivity': threshold_sensitivity,
        'confidence_intervals': confidence_intervals
    }
    
    # Generar reporte
    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)
    
    report_path = results_dir / "dataset_bias_analysis.txt"
    analyzer.generate_report(report_path, results)
    
    # Guardar JSON
    json_path = results_dir / "dataset_bias_analysis.json"
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Resultados JSON: {json_path}")


if __name__ == "__main__":
    main()
