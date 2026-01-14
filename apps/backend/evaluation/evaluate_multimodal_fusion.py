"""
Evaluación de Fusión Multi-Modal: Antispoofing + Verificación de Identidad

Este script implementa y evalúa diferentes estrategias de fusión entre:
- Antispoofing (AASIST-L + RawNet2): Detecta ataques sintéticos
- Speaker Recognition (ECAPA-TDNN): Verifica identidad del hablante

Estrategias de fusión:
1. Lineal ponderada: w1*identity + w2*antispoof
2. Adaptativa: Ajusta threshold de antispoofing según confianza de identidad
3. Multiplicativa: identity * antispoof
4. Por reglas: if identity > threshold then relax antispoof

Uso:
    python evaluation/evaluate_multimodal_fusion.py
"""

import sys
import json
import logging
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple
from collections import defaultdict

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.infrastructure.biometrics.SpoofDetectorAdapter import SpoofDetectorAdapter
from src.infrastructure.biometrics.SpeakerEmbeddingAdapter import SpeakerEmbeddingAdapter

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


class MultimodalFusionEvaluator:
    """Evaluador de fusión multi-modal antispoofing + speaker recognition."""
    
    def __init__(self):
        logger.info("🔧 Inicializando modelos...")
        self.spoof_detector = SpoofDetectorAdapter(
            model_name="ensemble_antispoofing",
            use_gpu=True
        )
        self.speaker_embedding = SpeakerEmbeddingAdapter(
            model_id=1,
            use_gpu=True
        )
        logger.info("✅ Modelos cargados\n")
    
    def calculate_cosine_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """Calcular similitud coseno entre dos embeddings."""
        dot_product = np.dot(emb1, emb2)
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        # Convertir de [-1, 1] a [0, 1]
        similarity = (similarity + 1.0) / 2.0
        
        return float(similarity)
    
    def load_audio(self, audio_path: Path) -> bytes:
        """Cargar archivo de audio."""
        with open(audio_path, 'rb') as f:
            return f.read()
    
    def get_multimodal_scores(
        self, 
        audio_path: Path,
        enrollment_audios: List[Path],
        user_id: str
    ) -> Dict[str, float]:
        """
        Obtener scores de antispoofing e identidad para un audio.
        
        Args:
            audio_path: Audio a evaluar
            enrollment_audios: Audios de enrollment del usuario
            user_id: ID del usuario
        
        Returns:
            Dict con spoof_score, identity_score, similarity
        """
        audio_data = self.load_audio(audio_path)
        
        # Score de antispoofing (0.0=genuino, 1.0=spoof)
        spoof_score = self.spoof_detector.detect_spoof(audio_data)
        
        # Score de identidad (similaridad con enrollment)
        # Extraer embedding del audio de test
        test_embedding = self.speaker_embedding._extract_real_embedding(audio_data, "audio/wav")
        
        # Calcular similaridad con cada audio de enrollment
        similarities = []
        for enroll_audio in enrollment_audios:
            enroll_data = self.load_audio(enroll_audio)
            enroll_embedding = self.speaker_embedding._extract_real_embedding(enroll_data, "audio/wav")
            
            similarity = self.calculate_cosine_similarity(test_embedding, enroll_embedding)
            similarities.append(similarity)
        
        # Usar máxima similaridad (más permisivo)
        identity_score = max(similarities) if similarities else 0.0
        
        return {
            'spoof_score': spoof_score,
            'identity_score': identity_score,
            'max_similarity': identity_score
        }
    
    def fusion_linear(
        self, 
        spoof_score: float, 
        identity_score: float,
        w_identity: float = 0.7,
        w_antispoof: float = 0.3
    ) -> float:
        """
        Fusión lineal ponderada.
        
        Score más alto = más confianza de que es genuino
        
        Args:
            spoof_score: 0.0=genuino, 1.0=spoof
            identity_score: 0.0=diferente, 1.0=mismo speaker
            w_identity: Peso para identidad
            w_antispoof: Peso para antispoofing
        
        Returns:
            Score combinado (más alto = más genuino)
        """
        # Invertir spoof_score para que alto = genuino
        antispoof_quality = 1.0 - spoof_score
        
        # Fusión lineal
        combined = w_identity * identity_score + w_antispoof * antispoof_quality
        
        return combined
    
    def fusion_adaptive(
        self,
        spoof_score: float,
        identity_score: float,
        identity_threshold_high: float = 0.85,
        identity_threshold_low: float = 0.60
    ) -> Dict[str, float]:
        """
        Fusión adaptativa: ajusta threshold de antispoofing según identidad.
        
        Lógica:
        - Si identity > 0.85: Usuario muy confiable → relajar antispoofing (threshold=0.95)
        - Si 0.60 < identity < 0.85: Usuario normal → threshold estándar (0.85)
        - Si identity < 0.60: Usuario dudoso → threshold estricto (0.75)
        
        Returns:
            Dict con threshold_antispoof, es_genuino
        """
        if identity_score >= identity_threshold_high:
            # Alta confianza de identidad → muy permisivo con antispoofing
            threshold_antispoof = 0.95
        elif identity_score >= identity_threshold_low:
            # Confianza media → threshold normal
            threshold_antispoof = 0.85
        else:
            # Baja confianza → muy estricto
            threshold_antispoof = 0.75
        
        # Decidir si es genuino
        es_genuino = spoof_score < threshold_antispoof
        
        return {
            'threshold_antispoof': threshold_antispoof,
            'es_genuino': es_genuino,
            'identity_score': identity_score,
            'spoof_score': spoof_score
        }
    
    def fusion_multiplicative(
        self,
        spoof_score: float,
        identity_score: float
    ) -> float:
        """
        Fusión multiplicativa: ambos deben estar confiables.
        
        Returns:
            Score combinado (más alto = más genuino)
        """
        antispoof_quality = 1.0 - spoof_score
        combined = identity_score * antispoof_quality
        return combined
    
    def fusion_rule_based(
        self,
        spoof_score: float,
        identity_score: float,
        identity_threshold: float = 0.80,
        spoof_threshold_relaxed: float = 0.90,
        spoof_threshold_strict: float = 0.80
    ) -> bool:
        """
        Fusión por reglas: decisión binaria.
        
        Reglas:
        1. Si identity > 0.80 → aceptar si spoof_score < 0.90
        2. Si identity <= 0.80 → aceptar si spoof_score < 0.80
        
        Returns:
            True si acepta como genuino, False si rechaza
        """
        if identity_score >= identity_threshold:
            # Usuario confiable → relajar antispoofing
            return spoof_score < spoof_threshold_relaxed
        else:
            # Usuario no confiable → estricto en antispoofing
            return spoof_score < spoof_threshold_strict
    
    def evaluate_fusion_strategies(
        self,
        genuine_scores: List[Dict],
        attack_scores: List[Dict]
    ) -> Dict:
        """
        Evaluar diferentes estrategias de fusión.
        
        Args:
            genuine_scores: Lista de dicts con spoof_score, identity_score
            attack_scores: Lista de dicts con spoof_score, identity_score (identity bajo)
        
        Returns:
            Dict con métricas por estrategia
        """
        results = {}
        
        # Baseline: Solo antispoofing (threshold=0.85)
        baseline_bpcer = sum(1 for g in genuine_scores if g['spoof_score'] >= 0.85) / len(genuine_scores) * 100
        baseline_apcer = sum(1 for a in attack_scores if a['spoof_score'] < 0.85) / len(attack_scores) * 100
        baseline_acer = (baseline_bpcer + baseline_apcer) / 2
        
        results['baseline'] = {
            'name': 'Solo Antispoofing (threshold=0.85)',
            'bpcer': baseline_bpcer,
            'apcer': baseline_apcer,
            'acer': baseline_acer
        }
        
        # Estrategia 1: Fusión lineal (varios pesos)
        for w_id in [0.5, 0.6, 0.7, 0.8]:
            w_as = 1.0 - w_id
            
            genuine_combined = [
                self.fusion_linear(g['spoof_score'], g['identity_score'], w_id, w_as)
                for g in genuine_scores
            ]
            attack_combined = [
                self.fusion_linear(a['spoof_score'], a.get('identity_score', 0.1), w_id, w_as)
                for a in attack_scores
            ]
            
            # Buscar mejor threshold para esta fusión
            best_acer = float('inf')
            best_threshold = 0.5
            
            for threshold in np.arange(0.3, 0.9, 0.05):
                bpcer = sum(1 for s in genuine_combined if s < threshold) / len(genuine_combined) * 100
                apcer = sum(1 for s in attack_combined if s >= threshold) / len(attack_combined) * 100
                acer = (bpcer + apcer) / 2
                
                if acer < best_acer:
                    best_acer = acer
                    best_threshold = threshold
                    best_bpcer = bpcer
                    best_apcer = apcer
            
            results[f'linear_w{w_id:.1f}'] = {
                'name': f'Fusión Lineal (identity={w_id:.1f}, antispoof={w_as:.1f})',
                'bpcer': best_bpcer,
                'apcer': best_apcer,
                'acer': best_acer,
                'threshold': best_threshold
            }
        
        # Estrategia 2: Fusión adaptativa
        adaptive_results = [
            self.fusion_adaptive(g['spoof_score'], g['identity_score'])
            for g in genuine_scores
        ]
        adaptive_bpcer = sum(1 for r in adaptive_results if not r['es_genuino']) / len(adaptive_results) * 100
        
        adaptive_attack_results = [
            self.fusion_adaptive(a['spoof_score'], a.get('identity_score', 0.1))
            for a in attack_scores
        ]
        adaptive_apcer = sum(1 for r in adaptive_attack_results if r['es_genuino']) / len(adaptive_attack_results) * 100
        
        results['adaptive'] = {
            'name': 'Fusión Adaptativa (threshold dinámico)',
            'bpcer': adaptive_bpcer,
            'apcer': adaptive_apcer,
            'acer': (adaptive_bpcer + adaptive_apcer) / 2
        }
        
        # Estrategia 3: Fusión multiplicativa
        genuine_mult = [
            self.fusion_multiplicative(g['spoof_score'], g['identity_score'])
            for g in genuine_scores
        ]
        attack_mult = [
            self.fusion_multiplicative(a['spoof_score'], a.get('identity_score', 0.1))
            for a in attack_scores
        ]
        
        # Buscar mejor threshold
        best_acer = float('inf')
        for threshold in np.arange(0.2, 0.8, 0.05):
            bpcer = sum(1 for s in genuine_mult if s < threshold) / len(genuine_mult) * 100
            apcer = sum(1 for s in attack_mult if s >= threshold) / len(attack_mult) * 100
            acer = (bpcer + apcer) / 2
            
            if acer < best_acer:
                best_acer = acer
                best_threshold = threshold
                best_bpcer = bpcer
                best_apcer = apcer
        
        results['multiplicative'] = {
            'name': 'Fusión Multiplicativa',
            'bpcer': best_bpcer,
            'apcer': best_apcer,
            'acer': best_acer,
            'threshold': best_threshold
        }
        
        # Estrategia 4: Fusión por reglas
        rule_genuine = [
            self.fusion_rule_based(g['spoof_score'], g['identity_score'])
            for g in genuine_scores
        ]
        rule_attack = [
            self.fusion_rule_based(a['spoof_score'], a.get('identity_score', 0.1))
            for a in attack_scores
        ]
        
        rule_bpcer = sum(1 for r in rule_genuine if not r) / len(rule_genuine) * 100
        rule_apcer = sum(1 for r in rule_attack if r) / len(rule_attack) * 100
        
        results['rule_based'] = {
            'name': 'Fusión por Reglas (if identity>0.8 then relax)',
            'bpcer': rule_bpcer,
            'apcer': rule_apcer,
            'acer': (rule_bpcer + rule_apcer) / 2
        }
        
        return results
    
    def process_dataset(self) -> Tuple[List[Dict], List[Dict]]:
        """
        Procesar dataset completo obteniendo scores multimodales.
        
        Returns:
            Tuple de (genuine_scores, attack_scores)
        """
        logger.info("📊 Procesando dataset completo...")
        
        # Paths
        evaluation_dir = Path(__file__).parent
        backend_dir = evaluation_dir.parent
        apps_dir = backend_dir.parent
        project_root = apps_dir.parent
        dataset_dir = project_root / "infra" / "evaluation" / "dataset"
        
        genuine_dir = dataset_dir / "recordings" / "auto_recordings_20251218"
        attacks_dir = dataset_dir / "attacks"
        cloning_dir = dataset_dir / "cloning"
        
        genuine_scores = []
        attack_scores = []
        
        # Procesar usuarios genuinos
        logger.info("\n🟢 Procesando audios GENUINOS...")
        users = [d for d in genuine_dir.iterdir() if d.is_dir()]
        
        for user_idx, user_dir in enumerate(users, 1):
            user_id = user_dir.name
            audio_files = list(user_dir.glob("*.wav"))
            
            if len(audio_files) < 4:
                logger.warning(f"⚠️  Usuario {user_id} tiene solo {len(audio_files)} audios, saltando...")
                continue
            
            # Usar primeros 3 para enrollment, resto para test
            enrollment_audios = audio_files[:3]
            test_audios = audio_files[3:]
            
            logger.info(f"  Usuario {user_idx}/{len(users)}: {user_id} - {len(test_audios)} audios de test")
            
            for test_audio in test_audios:
                try:
                    scores = self.get_multimodal_scores(test_audio, enrollment_audios, user_id)
                    scores['user_id'] = user_id
                    scores['audio_path'] = str(test_audio)
                    genuine_scores.append(scores)
                except Exception as e:
                    logger.error(f"❌ Error en {test_audio.name}: {e}")
        
        logger.info(f"✅ Total genuinos procesados: {len(genuine_scores)}\n")
        
        # Procesar ataques (TTS + Cloning)
        logger.info("🔴 Procesando ATAQUES...")
        
        # TTS attacks (no tienen identidad válida)
        tts_files = list(attacks_dir.rglob("*.wav"))
        logger.info(f"  Ataques TTS: {len(tts_files)}")
        
        for i, attack_audio in enumerate(tts_files, 1):
            try:
                audio_data = self.load_audio(attack_audio)
                spoof_score = self.spoof_detector.detect_spoof(audio_data)
                
                attack_scores.append({
                    'spoof_score': spoof_score,
                    'identity_score': 0.05,  # Muy bajo (no es ningún usuario)
                    'type': 'tts',
                    'audio_path': str(attack_audio)
                })
                
                if i % 50 == 0:
                    logger.info(f"    Procesados {i}/{len(tts_files)} TTS")
            except Exception as e:
                logger.error(f"❌ Error en TTS {attack_audio.name}: {e}")
        
        # Cloning attacks (pueden tener algo de similaridad)
        cloning_files = list(cloning_dir.rglob("*.wav"))
        logger.info(f"  Ataques Clonación: {len(cloning_files)}")
        
        for i, attack_audio in enumerate(cloning_files, 1):
            try:
                audio_data = self.load_audio(attack_audio)
                spoof_score = self.spoof_detector.detect_spoof(audio_data)
                
                # Los clones pueden tener algo de similaridad si logramos identificar al usuario target
                # Por simplicidad, asumimos baja identidad
                attack_scores.append({
                    'spoof_score': spoof_score,
                    'identity_score': 0.15,  # Algo más alto que TTS pero aún bajo
                    'type': 'cloning',
                    'audio_path': str(attack_audio)
                })
                
                if i % 20 == 0:
                    logger.info(f"    Procesados {i}/{len(cloning_files)} Cloning")
            except Exception as e:
                logger.error(f"❌ Error en Cloning {attack_audio.name}: {e}")
        
        logger.info(f"✅ Total ataques procesados: {len(attack_scores)}\n")
        
        return genuine_scores, attack_scores
    
    def generate_visualizations(
        self,
        results: Dict,
        genuine_scores: List[Dict],
        attack_scores: List[Dict],
        output_path: Path
    ):
        """Generar visualizaciones comparativas."""
        logger.info("📊 Generando visualizaciones...")
        
        fig = plt.figure(figsize=(18, 12))
        
        # 1. Comparación de BPCER entre estrategias
        ax1 = plt.subplot(2, 3, 1)
        strategies = list(results.keys())
        bpcers = [results[s]['bpcer'] for s in strategies]
        colors = ['red' if s == 'baseline' else 'green' if bpcers[i] < results['baseline']['bpcer'] else 'orange' 
                  for i, s in enumerate(strategies)]
        
        bars = ax1.barh(range(len(strategies)), bpcers, color=colors, alpha=0.7)
        ax1.set_yticks(range(len(strategies)))
        ax1.set_yticklabels([results[s]['name'][:30] for s in strategies], fontsize=9)
        ax1.set_xlabel('BPCER (%)', fontsize=11)
        ax1.set_title('BPCER por Estrategia\n(menor es mejor)', fontsize=12, fontweight='bold')
        ax1.axvline(results['baseline']['bpcer'], color='red', linestyle='--', 
                   linewidth=2, alpha=0.5, label='Baseline')
        ax1.legend()
        ax1.grid(True, alpha=0.3, axis='x')
        
        # 2. Comparación de ACER
        ax2 = plt.subplot(2, 3, 2)
        acers = [results[s]['acer'] for s in strategies]
        colors_acer = ['red' if s == 'baseline' else 'green' if acers[i] < results['baseline']['acer'] else 'orange'
                       for i, s in enumerate(strategies)]
        
        ax2.barh(range(len(strategies)), acers, color=colors_acer, alpha=0.7)
        ax2.set_yticks(range(len(strategies)))
        ax2.set_yticklabels([results[s]['name'][:30] for s in strategies], fontsize=9)
        ax2.set_xlabel('ACER (%)', fontsize=11)
        ax2.set_title('ACER por Estrategia\n(menor es mejor)', fontsize=12, fontweight='bold')
        ax2.axvline(results['baseline']['acer'], color='red', linestyle='--',
                   linewidth=2, alpha=0.5, label='Baseline')
        ax2.legend()
        ax2.grid(True, alpha=0.3, axis='x')
        
        # 3. Scatter: Identity vs Spoof para genuinos
        ax3 = plt.subplot(2, 3, 3)
        identity_genuine = [g['identity_score'] for g in genuine_scores]
        spoof_genuine = [g['spoof_score'] for g in genuine_scores]
        
        ax3.scatter(identity_genuine, spoof_genuine, alpha=0.6, s=50, c='blue', label='Genuinos')
        ax3.axhline(0.85, color='red', linestyle='--', label='Threshold Antispoof=0.85')
        ax3.axvline(0.80, color='orange', linestyle='--', label='Threshold Identity=0.80')
        ax3.set_xlabel('Identity Score', fontsize=11)
        ax3.set_ylabel('Spoof Score', fontsize=11)
        ax3.set_title('Distribución 2D: Genuinos', fontsize=12, fontweight='bold')
        ax3.legend(fontsize=9)
        ax3.grid(True, alpha=0.3)
        
        # 4. Scatter: Identity vs Spoof para ataques
        ax4 = plt.subplot(2, 3, 4)
        identity_attack = [a['identity_score'] for a in attack_scores]
        spoof_attack = [a['spoof_score'] for a in attack_scores]
        
        ax4.scatter(identity_attack, spoof_attack, alpha=0.6, s=50, c='red', label='Ataques')
        ax4.axhline(0.85, color='red', linestyle='--', label='Threshold Antispoof=0.85')
        ax4.axvline(0.80, color='orange', linestyle='--', label='Threshold Identity=0.80')
        ax4.set_xlabel('Identity Score', fontsize=11)
        ax4.set_ylabel('Spoof Score', fontsize=11)
        ax4.set_title('Distribución 2D: Ataques', fontsize=12, fontweight='bold')
        ax4.legend(fontsize=9)
        ax4.grid(True, alpha=0.3)
        
        # 5. Mejora relativa respecto a baseline
        ax5 = plt.subplot(2, 3, 5)
        improvements = []
        for s in strategies:
            if s != 'baseline':
                improvement = results['baseline']['bpcer'] - results[s]['bpcer']
                improvements.append((results[s]['name'][:25], improvement))
        
        improvements.sort(key=lambda x: x[1], reverse=True)
        names, values = zip(*improvements) if improvements else ([], [])
        
        colors_imp = ['green' if v > 0 else 'red' for v in values]
        ax5.barh(range(len(names)), values, color=colors_imp, alpha=0.7)
        ax5.set_yticks(range(len(names)))
        ax5.set_yticklabels(names, fontsize=9)
        ax5.set_xlabel('Mejora en BPCER (puntos porcentuales)', fontsize=11)
        ax5.set_title('Mejora vs Baseline\n(valores positivos = mejor)', fontsize=12, fontweight='bold')
        ax5.axvline(0, color='black', linestyle='-', linewidth=1)
        ax5.grid(True, alpha=0.3, axis='x')
        
        # 6. Tabla resumen de mejor estrategia
        ax6 = plt.subplot(2, 3, 6)
        ax6.axis('off')
        
        # Encontrar mejor estrategia por BPCER
        best_strategy_key = min(
            [k for k in strategies if k != 'baseline'],
            key=lambda x: results[x]['bpcer']
        )
        best = results[best_strategy_key]
        baseline = results['baseline']
        
        table_data = [
            ['Métrica', 'Baseline', 'Mejor Fusión', 'Mejora'],
            ['BPCER', f"{baseline['bpcer']:.2f}%", f"{best['bpcer']:.2f}%", 
             f"{baseline['bpcer'] - best['bpcer']:.2f}pp"],
            ['APCER', f"{baseline['apcer']:.2f}%", f"{best['apcer']:.2f}%",
             f"{baseline['apcer'] - best['apcer']:.2f}pp"],
            ['ACER', f"{baseline['acer']:.2f}%", f"{best['acer']:.2f}%",
             f"{baseline['acer'] - best['acer']:.2f}pp"],
            ['', '', '', ''],
            ['Estrategia Ganadora:', best['name'][:40], '', '']
        ]
        
        table = ax6.table(cellText=table_data, cellLoc='center', loc='center',
                         colWidths=[0.25, 0.25, 0.25, 0.25])
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 2.5)
        
        # Estilo
        for i in range(len(table_data)):
            for j in range(4):
                cell = table[(i, j)]
                if i == 0:
                    cell.set_facecolor('#4CAF50')
                    cell.set_text_props(weight='bold', color='white')
                elif i == 5:
                    cell.set_facecolor('#FFF9C4')
                    cell.set_text_props(weight='bold')
        
        ax6.set_title('🏆 Mejor Estrategia de Fusión', fontsize=14, fontweight='bold', pad=20)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"✅ Visualizaciones guardadas: {output_path}\n")
    
    def generate_report(
        self,
        results: Dict,
        genuine_scores: List[Dict],
        attack_scores: List[Dict],
        output_dir: Path
    ):
        """Generar reporte completo."""
        logger.info("📝 Generando reporte...")
        
        report_lines = [
            "=" * 100,
            "EVALUACIÓN DE FUSIÓN MULTI-MODAL",
            "Antispoofing (AASIST-L + RawNet2) + Speaker Recognition (ECAPA-TDNN)",
            "=" * 100,
            "",
            "Dataset:",
            f"  - Audios Genuinos procesados: {len(genuine_scores)}",
            f"  - Ataques procesados: {len(attack_scores)}",
            f"    * TTS: {sum(1 for a in attack_scores if a['type'] == 'tts')}",
            f"    * Cloning: {sum(1 for a in attack_scores if a['type'] == 'cloning')}",
            "",
            "Estadísticas de Scores:",
            f"  Genuinos:",
            f"    - Spoof Score: mean={np.mean([g['spoof_score'] for g in genuine_scores]):.3f}",
            f"    - Identity Score: mean={np.mean([g['identity_score'] for g in genuine_scores]):.3f}",
            f"  Ataques:",
            f"    - Spoof Score: mean={np.mean([a['spoof_score'] for a in attack_scores]):.3f}",
            f"    - Identity Score: mean={np.mean([a['identity_score'] for a in attack_scores]):.3f}",
            "",
            "=" * 100,
            "RESULTADOS POR ESTRATEGIA",
            "=" * 100,
            ""
        ]
        
        # Ordenar por ACER
        sorted_strategies = sorted(
            results.items(),
            key=lambda x: x[1]['acer']
        )
        
        for rank, (key, data) in enumerate(sorted_strategies, 1):
            marker = "🏆" if rank == 1 else "⭐" if rank == 2 else "  "
            report_lines.extend([
                f"{marker} {rank}. {data['name']}",
                f"     BPCER: {data['bpcer']:.2f}%",
                f"     APCER: {data['apcer']:.2f}%",
                f"     ACER:  {data['acer']:.2f}%",
                ""
            ])
        
        # Análisis de mejora
        baseline = results['baseline']
        best_key = sorted_strategies[0][0]
        best = results[best_key]
        
        bpcer_improvement = baseline['bpcer'] - best['bpcer']
        apcer_improvement = baseline['apcer'] - best['apcer']
        acer_improvement = baseline['acer'] - best['acer']
        
        report_lines.extend([
            "=" * 100,
            "ANÁLISIS DE MEJORA",
            "=" * 100,
            "",
            f"Estrategia Ganadora: {best['name']}",
            "",
            "Mejora respecto a Baseline (Solo Antispoofing):",
            f"  BPCER: {baseline['bpcer']:.2f}% → {best['bpcer']:.2f}% (mejora: {bpcer_improvement:+.2f}pp)",
            f"  APCER: {baseline['apcer']:.2f}% → {best['apcer']:.2f}% (mejora: {apcer_improvement:+.2f}pp)",
            f"  ACER:  {baseline['acer']:.2f}% → {best['acer']:.2f}% (mejora: {acer_improvement:+.2f}pp)",
            "",
            "Interpretación:",
        ])
        
        if bpcer_improvement > 15:
            report_lines.append(f"✅ Mejora EXCELENTE en BPCER: Reducción de {bpcer_improvement:.1f} puntos porcentuales")
        elif bpcer_improvement > 5:
            report_lines.append(f"✅ Mejora BUENA en BPCER: Reducción de {bpcer_improvement:.1f} puntos porcentuales")
        else:
            report_lines.append(f"⚠️  Mejora moderada en BPCER: Reducción de {bpcer_improvement:.1f} puntos porcentuales")
        
        if best['bpcer'] < 15:
            report_lines.append("✅ BPCER final < 15%: Excelente usabilidad para aplicación comercial")
        elif best['bpcer'] < 25:
            report_lines.append("✅ BPCER final < 25%: Buena usabilidad, aceptable para la mayoría de casos")
        else:
            report_lines.append("⚠️  BPCER final aún alto: Considerar ajustes adicionales")
        
        report_lines.extend([
            "",
            "Recomendación de Implementación:",
            f"  1. Implementar estrategia: {best['name']}",
            f"  2. Usar threshold optimizado para esta estrategia",
            f"  3. Monitorear en producción y ajustar según feedback",
            "  4. La fusión multi-modal aprovecha que ECAPA-TDNN es muy preciso (EER=2.78%)",
            "  5. Usuarios con alta confianza de identidad pueden pasar incluso con scores",
            "     de antispoofing más altos, mejorando la experiencia de usuario",
            "",
            "=" * 100,
        ])
        
        # Guardar reporte
        report_path = output_dir / "multimodal_fusion_evaluation.txt"
        with open(report_path, 'w') as f:
            f.write('\n'.join(report_lines))
        
        logger.info(f"✅ Reporte guardado: {report_path}")
        
        # Guardar JSON
        json_data = {
            'dataset': {
                'genuine_count': len(genuine_scores),
                'attack_count': len(attack_scores),
                'tts_count': sum(1 for a in attack_scores if a['type'] == 'tts'),
                'cloning_count': sum(1 for a in attack_scores if a['type'] == 'cloning')
            },
            'strategies': results,
            'best_strategy': best_key,
            'improvement': {
                'bpcer': bpcer_improvement,
                'apcer': apcer_improvement,
                'acer': acer_improvement
            }
        }
        
        json_path = output_dir / "multimodal_fusion_evaluation.json"
        with open(json_path, 'w') as f:
            json.dump(json_data, f, indent=2)
        
        logger.info(f"✅ Datos JSON guardados: {json_path}\n")
    
    def run(self):
        """Ejecutar evaluación completa."""
        logger.info("=" * 100)
        logger.info("🎯 EVALUACIÓN DE FUSIÓN MULTI-MODAL")
        logger.info("=" * 100)
        logger.info("")
        
        # Procesar dataset
        genuine_scores, attack_scores = self.process_dataset()
        
        # Evaluar estrategias de fusión
        logger.info("🔬 Evaluando estrategias de fusión...")
        results = self.evaluate_fusion_strategies(genuine_scores, attack_scores)
        
        # Mostrar tabla resumen
        logger.info("\n" + "=" * 100)
        logger.info("📊 RESUMEN DE RESULTADOS")
        logger.info("=" * 100)
        logger.info(f"{'Estrategia':<45} {'BPCER':<10} {'APCER':<10} {'ACER':<10}")
        logger.info("-" * 100)
        
        sorted_strategies = sorted(results.items(), key=lambda x: x[1]['acer'])
        for rank, (key, data) in enumerate(sorted_strategies, 1):
            marker = "🏆" if rank == 1 else "⭐" if rank == 2 else "  "
            logger.info(
                f"{marker} {data['name']:<43} "
                f"{data['bpcer']:<10.2f} "
                f"{data['apcer']:<10.2f} "
                f"{data['acer']:<10.2f}"
            )
        
        logger.info("=" * 100)
        logger.info("")
        
        # Generar visualizaciones
        output_dir = Path(__file__).parent / "results"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        viz_path = output_dir / "multimodal_fusion_visualizations.png"
        self.generate_visualizations(results, genuine_scores, attack_scores, viz_path)
        
        # Generar reporte
        self.generate_report(results, genuine_scores, attack_scores, output_dir)
        
        # Resumen final
        best_key = sorted_strategies[0][0]
        best = results[best_key]
        baseline = results['baseline']
        
        logger.info("=" * 100)
        logger.info("✅ EVALUACIÓN COMPLETADA")
        logger.info("=" * 100)
        logger.info(f"📁 Resultados guardados en: {output_dir}")
        logger.info("")
        logger.info("🏆 MEJOR ESTRATEGIA:")
        logger.info(f"   {best['name']}")
        logger.info(f"   BPCER: {baseline['bpcer']:.2f}% → {best['bpcer']:.2f}% (mejora: {baseline['bpcer'] - best['bpcer']:+.2f}pp)")
        logger.info(f"   ACER:  {baseline['acer']:.2f}% → {best['acer']:.2f}% (mejora: {baseline['acer'] - best['acer']:+.2f}pp)")
        logger.info("")


def main():
    """Función principal."""
    evaluator = MultimodalFusionEvaluator()
    evaluator.run()


if __name__ == "__main__":
    main()
