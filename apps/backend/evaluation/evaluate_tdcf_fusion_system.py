"""
Evaluación del Sistema Integrado con métricas académicas:
1. t-DCF (tandem Detection Cost Function)
2. Tasa de Aceptación Sistémica (End-to-End FRR)
3. Matriz de Decisión Triple (Lógica de Cascada)

Sistema de cascada:
Etapa 1: Antispoofing (rechaza ataques)
Etapa 2: Speaker Recognition (verifica identidad)
Etapa 3: Text Verification (valida texto pronunciado)
"""

import sys
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, List, Tuple
import logging
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.infrastructure.biometrics.SpoofDetectorAdapter import SpoofDetectorAdapter
from src.infrastructure.biometrics.SpeakerEmbeddingAdapter import SpeakerEmbeddingAdapter
from src.infrastructure.biometrics.ASRAdapter import ASRAdapter
from parse_phrases import parse_phrases_from_report

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


class TandemDCFFusionEvaluator:
    """Evaluador con FUSIÓN MULTIMODAL, t-DCF, End-to-End FRR y Matriz de Cascada."""
    
    def __init__(self):
        """Inicializar todos los módulos del sistema."""
        # Módulo 1: Antispoofing
        self.spoof_detector = SpoofDetectorAdapter(
            model_name="ensemble_antispoofing",
            use_gpu=True
        )
        
        # Módulo 2: Speaker Recognition
        self.speaker_embedding = SpeakerEmbeddingAdapter(
            model_id=1,
            use_gpu=True
        )
        
        # Módulo 3: Text Verification (ASR)
        self.asr_adapter = ASRAdapter(use_gpu=True)
        
        logger.info("✅ Sistema integrado con FUSIÓN cargado (3 módulos)\n")
        
        # Configuración de fusión (optimizada desde evaluate_multimodal_fusion.py)
        self.fusion_config = {
            'weights': {
                'identity': 0.7,      # 70% peso para identidad
                'antispoof': 0.3      # 30% peso para antispoofing
            },
            'threshold': 0.45  # Threshold óptimo (ACER 0%)
        }
        
        # Thresholds optimizados
        self.thresholds = {
            'text_wer': 25.0
        }
        
        # Parámetros para t-DCF (ASVspoof 2021 estándar)
        self.tdcf_params = {
            'C_miss': 1.0,      # Costo de no detectar ataque
            'C_fa': 10.0,       # Costo de rechazar genuino (10x peor)
            'P_tar': 0.95,      # Prior de genuinos (95%)
            'P_nontar': 0.05    # Prior de ataques (5%)
        }
    
    def normalize_text_for_comparison(self, text: str) -> str:
        """Normalizar texto para comparación."""
        import unicodedata
        import re
        
        text = text.lower()
        text = ''.join(
            c for c in unicodedata.normalize('NFD', text)
            if unicodedata.category(c) != 'Mn'
        )
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def calculate_wer_levenshtein(self, ref_words: list, hyp_words: list) -> float:
        """Calcular WER con Levenshtein distance."""
        d = np.zeros((len(ref_words) + 1, len(hyp_words) + 1), dtype=np.int32)
        
        for i in range(len(ref_words) + 1):
            d[i][0] = i
        for j in range(len(hyp_words) + 1):
            d[0][j] = j
        
        for i in range(1, len(ref_words) + 1):
            for j in range(1, len(hyp_words) + 1):
                if ref_words[i-1] == hyp_words[j-1]:
                    d[i][j] = d[i-1][j-1]
                else:
                    substitution = d[i-1][j-1] + 1
                    insertion = d[i][j-1] + 1
                    deletion = d[i-1][j] + 1
                    d[i][j] = min(substitution, insertion, deletion)
        
        if len(ref_words) == 0:
            return 100.0 if len(hyp_words) > 0 else 0.0
        
        wer = (float(d[len(ref_words)][len(hyp_words)]) / len(ref_words)) * 100
        return wer
    
    def load_audio(self, audio_path: Path) -> bytes:
        """Cargar archivo de audio."""
        with open(audio_path, 'rb') as f:
            return f.read()
    
    def calculate_cosine_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """Calcular similitud coseno entre dos embeddings."""
        dot_product = np.dot(emb1, emb2)
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        similarity = (similarity + 1.0) / 2.0
        
        return float(similarity)
    
    def calculate_fusion_score(
        self,
        identity_score: float,
        antispoof_score: float
    ) -> float:
        """
        Calcular score de fusión multimodal.
        
        Formula: fusion = w_identity * identity + w_antispoof * (1 - antispoof)
        
        Nota: Antispoofing invierte (1 - score) porque valores bajos = genuino
        """
        w_identity = self.fusion_config['weights']['identity']
        w_antispoof = self.fusion_config['weights']['antispoof']
        
        # Normalizar antispoofing: 0=spoof, 1=genuino
        antispoof_normalized = 1.0 - antispoof_score
        
        fusion_score = (w_identity * identity_score) + (w_antispoof * antispoof_normalized)
        
        return fusion_score
    
    def cascade_decision(
        self, 
        audio_data: bytes, 
        enrollment_embeddings: List[np.ndarray],
        expected_text: str = None
    ) -> Dict:
        """
        Decisión en cascada con FUSIÓN: 2 etapas secuenciales.
        
        Etapa 1: FUSIÓN MULTIMODAL (Antispoofing + Speaker Recognition combinados)
        Etapa 2: Text Verification (si aplica)
        """
        result = {
            'stage1_antispoof_score': None,
            'stage1_identity_score': None,
            'stage1_fusion_score': None,
            'stage1_passed': False,
            'stage2_text_wer': None,
            'stage2_passed': False,
            'transcribed_text': None,
            'final_decision': False,
            'rejection_stage': None  # 1, 2, o None si acepta
        }
        
        # ETAPA 1: FUSIÓN MULTIMODAL
        # Obtener score de antispoofing
        spoof_score = self.spoof_detector.detect_spoof(audio_data)
        result['stage1_antispoof_score'] = spoof_score
        
        # Obtener score de identidad
        test_embedding = self.speaker_embedding._extract_real_embedding(audio_data, "audio/wav")
        similarities = []
        for enroll_emb in enrollment_embeddings:
            similarity = self.calculate_cosine_similarity(test_embedding, enroll_emb)
            similarities.append(similarity)
        
        identity_score = max(similarities) if similarities else 0.0
        result['stage1_identity_score'] = identity_score
        
        # Calcular score de fusión
        fusion_score = self.calculate_fusion_score(identity_score, spoof_score)
        result['stage1_fusion_score'] = fusion_score
        
        # Decidir según threshold de fusión
        result['stage1_passed'] = fusion_score >= self.fusion_config['threshold']
        
        if not result['stage1_passed']:
            result['rejection_stage'] = 1
            return result
        
        # ETAPA 2: Text Verification (si aplica)
        if expected_text is not None:
            transcribed_text = self.asr_adapter.transcribe(audio_data)
            result['transcribed_text'] = transcribed_text
            
            ref_normalized = self.normalize_text_for_comparison(expected_text)
            hyp_normalized = self.normalize_text_for_comparison(transcribed_text)
            
            ref_words = ref_normalized.split()
            hyp_words = hyp_normalized.split()
            
            text_wer = self.calculate_wer_levenshtein(ref_words, hyp_words)
            result['stage2_text_wer'] = text_wer
            result['stage2_passed'] = text_wer < self.thresholds['text_wer']
            
            if not result['stage2_passed']:
                result['rejection_stage'] = 2
                return result
        else:
            # Sin texto esperado, la etapa 2 se considera pasada
            result['stage2_passed'] = True
        
        # ACEPTA: Pasó las 2 etapas
        result['final_decision'] = True
        return result
    
    def calculate_tdcf(
        self,
        genuine_scores: List[float],
        attack_scores: List[float],
        threshold: float
    ) -> Dict:
        """
        Calcular t-DCF (tandem Detection Cost Function).
        
        t-DCF = C_miss * P_miss * P_tar + C_fa * P_fa * P_nontar
        
        donde:
        - P_miss = tasa de ataques no detectados (miss rate)
        - P_fa = tasa de genuinos rechazados (false alarm rate)
        """
        # False Rejection: genuinos con score >= threshold (rechazados)
        genuine_rejected = sum(1 for s in genuine_scores if s >= threshold)
        P_fa = genuine_rejected / len(genuine_scores) if len(genuine_scores) > 0 else 0.0
        
        # Miss: ataques con score < threshold (aceptados)
        attacks_accepted = sum(1 for s in attack_scores if s < threshold)
        P_miss = attacks_accepted / len(attack_scores) if len(attack_scores) > 0 else 0.0
        
        # Calcular t-DCF
        tdcf = (
            self.tdcf_params['C_miss'] * P_miss * self.tdcf_params['P_tar'] +
            self.tdcf_params['C_fa'] * P_fa * self.tdcf_params['P_nontar']
        )
        
        return {
            'tdcf': tdcf,
            'P_miss': P_miss,
            'P_fa': P_fa,
            'threshold': threshold
        }
    
    def calculate_min_tdcf(
        self,
        genuine_scores: List[float],
        attack_scores: List[float]
    ) -> Dict:
        """Encontrar el threshold óptimo que minimiza t-DCF."""
        all_scores = sorted(set(genuine_scores + attack_scores))
        
        best_tdcf = float('inf')
        best_threshold = None
        best_metrics = None
        
        for threshold in all_scores:
            metrics = self.calculate_tdcf(genuine_scores, attack_scores, threshold)
            if metrics['tdcf'] < best_tdcf:
                best_tdcf = metrics['tdcf']
                best_threshold = threshold
                best_metrics = metrics
        
        return best_metrics
    
    def evaluate_system(self):
        """Evaluar sistema completo con FUSIÓN, t-DCF, End-to-End FRR y Matriz de Cascada."""
        logger.info("=" * 80)
        logger.info("🎯 EVALUACIÓN DEL SISTEMA CON FUSIÓN MULTIMODAL")
        logger.info("=" * 80)
        logger.info("")
        
        # Paths
        evaluation_dir = Path(__file__).parent
        backend_dir = evaluation_dir.parent
        apps_dir = backend_dir.parent
        project_root = apps_dir.parent
        dataset_dir = project_root / "infra" / "evaluation" / "dataset"
        
        # Cargar frases del reporte
        report_file = backend_dir / "evaluation" / "results" / "dataset_verification_report.txt"
        logger.info("📖 Cargando frases esperadas del reporte...")
        expected_phrases = parse_phrases_from_report(report_file)
        logger.info(f"  ✅ {len(expected_phrases)} frases cargadas\n")
        
        genuine_dir = dataset_dir / "recordings" / "auto_recordings_20251218"
        attacks_dir = dataset_dir / "attacks"
        cloning_dir = dataset_dir / "cloning"
        
        # Estructuras para almacenar resultados
        genuine_results = []
        attack_results = []
        
        # Matriz de decisión: [etapa_rechazo][tipo_audio]
        cascade_matrix = {
            'genuine': {'stage1_fusion': 0, 'stage2_text': 0, 'accepted': 0},
            'tts': {'stage1_fusion': 0, 'accepted': 0},
            'cloning': {'stage1_fusion': 0, 'stage2_text': 0, 'accepted': 0}
        }
        
        # Scores para calcular t-DCF (usamos stage1 antispoofing como score principal)
        genuine_antispoof_scores = []
        attack_antispoof_scores = []
        
        # Procesar enrollments de usuarios genuinos
        logger.info("🔵 Extrayendo enrollments de usuarios genuinos...")
        users = [d for d in genuine_dir.iterdir() if d.is_dir()]
        user_enrollments = {}
        
        for user_dir in users:
            username = user_dir.name
            enrollment_audios = sorted([f for f in user_dir.glob("*.wav") 
                                       if "_enrollment_" in f.name])
            
            if len(enrollment_audios) < 3:
                continue
            
            enrollments = []
            for audio_file in enrollment_audios[:3]:
                audio_data = self.load_audio(audio_file)
                embedding = self.speaker_embedding._extract_real_embedding(audio_data, "audio/wav")
                enrollments.append(embedding)
            
            user_enrollments[username] = enrollments
            logger.info(f"  Usuario {username}: {len(enrollments)} enrollments")
        
        logger.info(f"\n✅ {len(user_enrollments)} usuarios enrollados\n")
        
        # GENUINOS
        logger.info("🟢 Evaluando audios genuinos...")
        total_genuine = 0
        
        for username, enrollments in user_enrollments.items():
            user_dir = genuine_dir / username
            verification_audios = sorted([f for f in user_dir.glob("*.wav") 
                                         if "_verification_" in f.name])
            
            for audio_file in verification_audios:
                expected_text = expected_phrases.get(audio_file.name)
                audio_data = self.load_audio(audio_file)
                
                result = self.cascade_decision(audio_data, enrollments, expected_text)
                
                # Registrar scores para t-DCF (usamos fusion score ahora)
                genuine_antispoof_scores.append(result['stage1_fusion_score'])
                
                # Actualizar matriz de cascada
                if result['final_decision']:
                    cascade_matrix['genuine']['accepted'] += 1
                elif result['rejection_stage'] == 1:
                    cascade_matrix['genuine']['stage1_fusion'] += 1
                elif result['rejection_stage'] == 2:
                    cascade_matrix['genuine']['stage2_text'] += 1
                
                genuine_results.append({
                    'filename': audio_file.name,
                    'username': username,
                    'result': result
                })
                
                total_genuine += 1
        
        logger.info(f"  ✅ {total_genuine} audios genuinos evaluados\n")
        
        # ATAQUES TTS
        logger.info("🔴 Evaluando ataques TTS...")
        total_tts = 0
        
        for user_dir in attacks_dir.iterdir():
            if not user_dir.is_dir():
                continue
            
            # Identificar víctima
            victim_username = None
            for username in user_enrollments.keys():
                if user_dir.name.startswith(username):
                    victim_username = username
                    break
            
            if victim_username is None:
                continue
            
            victim_enrollments = user_enrollments[victim_username]
            
            for attack_audio in user_dir.glob("*.wav"):
                # TTS attacks no tienen frases en el reporte
                audio_data = self.load_audio(attack_audio)
                
                result = self.cascade_decision(audio_data, victim_enrollments, expected_text=None)
                
                # Registrar scores para t-DCF (usamos fusion score ahora)
                attack_antispoof_scores.append(result['stage1_fusion_score'])
                
                # Actualizar matriz de cascada
                if result['final_decision']:
                    cascade_matrix['tts']['accepted'] += 1
                elif result['rejection_stage'] == 1:
                    cascade_matrix['tts']['stage1_fusion'] += 1
                
                attack_results.append({
                    'filename': attack_audio.name,
                    'attack_type': 'tts',
                    'victim': victim_username,
                    'result': result
                })
                
                total_tts += 1
        
        logger.info(f"  ✅ {total_tts} ataques TTS evaluados\n")
        
        # ATAQUES CLONING
        logger.info("🟠 Evaluando ataques de clonación...")
        total_cloning = 0
        
        for user_dir in cloning_dir.iterdir():
            if not user_dir.is_dir():
                continue
            
            # Identificar víctima
            victim_username = None
            for username in user_enrollments.keys():
                if user_dir.name.startswith(username):
                    victim_username = username
                    break
            
            if victim_username is None:
                continue
            
            victim_enrollments = user_enrollments[victim_username]
            
            for attack_audio in user_dir.glob("*.wav"):
                expected_text = expected_phrases.get(attack_audio.name)
                audio_data = self.load_audio(attack_audio)
                
                result = self.cascade_decision(audio_data, victim_enrollments, expected_text)
                
                # Registrar scores para t-DCF (usamos fusion score ahora)
                attack_antispoof_scores.append(result['stage1_fusion_score'])
                
                # Actualizar matriz de cascada
                if result['final_decision']:
                    cascade_matrix['cloning']['accepted'] += 1
                elif result['rejection_stage'] == 1:
                    cascade_matrix['cloning']['stage1_fusion'] += 1
                elif result['rejection_stage'] == 2:
                    cascade_matrix['cloning']['stage2_text'] += 1
                
                attack_results.append({
                    'filename': attack_audio.name,
                    'attack_type': 'cloning',
                    'victim': victim_username,
                    'result': result
                })
                
                total_cloning += 1
        
        logger.info(f"  ✅ {total_cloning} ataques de clonación evaluados\n")
        
        # ========== CALCULAR MÉTRICAS ==========
        
        logger.info("=" * 80)
        logger.info("📊 MÉTRICAS DEL SISTEMA")
        logger.info("=" * 80)
        logger.info("")
        
        # 1. END-TO-END FRR (Tasa de Rechazo de Genuinos)
        genuine_accepted = cascade_matrix['genuine']['accepted']
        end_to_end_frr = 1.0 - (genuine_accepted / total_genuine)
        end_to_end_far = (cascade_matrix['tts']['accepted'] + cascade_matrix['cloning']['accepted']) / (total_tts + total_cloning)
        
        logger.info("1️⃣  TASA DE ACEPTACIÓN SISTÉMICA (End-to-End)")
        logger.info(f"   FRR (False Rejection Rate): {end_to_end_frr*100:.2f}%")
        logger.info(f"   FAR (False Acceptance Rate): {end_to_end_far*100:.2f}%")
        logger.info(f"   Genuinos aceptados: {genuine_accepted}/{total_genuine}")
        logger.info(f"   Ataques aceptados: {cascade_matrix['tts']['accepted'] + cascade_matrix['cloning']['accepted']}/{total_tts + total_cloning}")
        logger.info("")
        
        # 2. t-DCF (tandem Detection Cost Function) - usando fusion scores
        tdcf_current = self.calculate_tdcf(
            genuine_antispoof_scores,
            attack_antispoof_scores,
            self.fusion_config['threshold']
        )
        
        tdcf_optimal = self.calculate_min_tdcf(
            genuine_antispoof_scores,
            attack_antispoof_scores
        )
        
        logger.info("2️⃣  t-DCF (tandem Detection Cost Function)")
        logger.info(f"   t-DCF (threshold fusión actual {self.fusion_config['threshold']:.3f}): {tdcf_current['tdcf']:.4f}")
        logger.info(f"   t-DCF mínimo: {tdcf_optimal['tdcf']:.4f} (threshold óptimo: {tdcf_optimal['threshold']:.3f})")
        logger.info(f"   P_miss (ataques aceptados): {tdcf_current['P_miss']*100:.2f}%")
        logger.info(f"   P_fa (genuinos rechazados etapa 1): {tdcf_current['P_fa']*100:.2f}%")
        logger.info("")
        
        # 3. MATRIZ DE DECISIÓN CON FUSIÓN (Cascada)
        logger.info("3️⃣  MATRIZ DE DECISIÓN CON FUSIÓN (Lógica de Cascada)")
        logger.info("")
        logger.info("   GENUINOS:")
        logger.info(f"     Rechazados en Etapa 1 (FUSIÓN): {cascade_matrix['genuine']['stage1_fusion']}/{total_genuine} ({cascade_matrix['genuine']['stage1_fusion']/total_genuine*100:.1f}%)")
        logger.info(f"     Rechazados en Etapa 2 (Texto): {cascade_matrix['genuine']['stage2_text']}/{total_genuine} ({cascade_matrix['genuine']['stage2_text']/total_genuine*100:.1f}%)")
        logger.info(f"     ✅ Aceptados: {cascade_matrix['genuine']['accepted']}/{total_genuine} ({cascade_matrix['genuine']['accepted']/total_genuine*100:.1f}%)")
        logger.info("")
        logger.info("   ATAQUES TTS:")
        logger.info(f"     Rechazados en Etapa 1 (FUSIÓN): {cascade_matrix['tts']['stage1_fusion']}/{total_tts} ({cascade_matrix['tts']['stage1_fusion']/total_tts*100:.1f}%)")
        logger.info(f"     ❌ Aceptados: {cascade_matrix['tts']['accepted']}/{total_tts} ({cascade_matrix['tts']['accepted']/total_tts*100:.1f}%)")
        logger.info("")
        logger.info("   ATAQUES CLONING:")
        logger.info(f"     Rechazados en Etapa 1 (FUSIÓN): {cascade_matrix['cloning']['stage1_fusion']}/{total_cloning} ({cascade_matrix['cloning']['stage1_fusion']/total_cloning*100:.1f}%)")
        logger.info(f"     Rechazados en Etapa 2 (Texto): {cascade_matrix['cloning']['stage2_text']}/{total_cloning} ({cascade_matrix['cloning']['stage2_text']/total_cloning*100:.1f}%)")
        logger.info(f"     ❌ Aceptados: {cascade_matrix['cloning']['accepted']}/{total_cloning} ({cascade_matrix['cloning']['accepted']/total_cloning*100:.1f}%)")
        logger.info("")
        
        # ========== GUARDAR RESULTADOS ==========
        
        results_dict = {
            'evaluation_date': datetime.now().isoformat(),
            'dataset': {
                'genuine_count': total_genuine,
                'tts_count': total_tts,
                'cloning_count': total_cloning,
                'total_attacks': total_tts + total_cloning
            },
            'thresholds': self.thresholds,
            'tdcf_params': self.tdcf_params,
            'metrics': {
                'end_to_end_frr': end_to_end_frr,
                'end_to_end_far': end_to_end_far,
                'tdcf_current': tdcf_current,
                'tdcf_optimal': tdcf_optimal
            },
            'cascade_matrix': cascade_matrix,
            'genuine_results': genuine_results,
            'attack_results': attack_results
        }
        
        # Guardar JSON
        results_dir = evaluation_dir / "results"
        results_dir.mkdir(exist_ok=True)
        
        json_file = results_dir / "tdcf_fusion_system_evaluation.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results_dict, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Resultados guardados en: {json_file}")
        
        # ========== GENERAR VISUALIZACIONES ==========
        
        # TODO: Actualizar plot_results para sistema con fusión (2 etapas)
        # self.plot_results(results_dict, results_dir)
        
        logger.info("")
        logger.info("=" * 80)
        logger.info("✅ EVALUACIÓN CON FUSIÓN COMPLETADA")
        logger.info("=" * 80)
    
    def plot_results(self, results: Dict, results_dir: Path):
        """Generar visualizaciones de los resultados."""
        fig = plt.figure(figsize=(20, 12))
        
        # Plot 1: Matriz de Cascada
        ax1 = plt.subplot(2, 3, 1)
        cascade = results['cascade_matrix']
        
        categories = ['Genuinos', 'TTS', 'Cloning']
        stage1_rejects = [cascade['genuine']['stage1'], cascade['tts']['stage1'], cascade['cloning']['stage1']]
        stage2_rejects = [cascade['genuine']['stage2'], cascade['tts']['stage2'], cascade['cloning']['stage2']]
        stage3_rejects = [cascade['genuine']['stage3'], cascade['tts']['stage3'], cascade['cloning']['stage3']]
        accepted = [cascade['genuine']['accepted'], cascade['tts']['accepted'], cascade['cloning']['accepted']]
        
        x = np.arange(len(categories))
        width = 0.2
        
        ax1.bar(x - 1.5*width, stage1_rejects, width, label='Etapa 1 (Antispoofing)', color='#e74c3c')
        ax1.bar(x - 0.5*width, stage2_rejects, width, label='Etapa 2 (Speaker)', color='#f39c12')
        ax1.bar(x + 0.5*width, stage3_rejects, width, label='Etapa 3 (Texto)', color='#3498db')
        ax1.bar(x + 1.5*width, accepted, width, label='✅ Aceptados', color='#2ecc71')
        
        ax1.set_xlabel('Tipo de Audio', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Cantidad', fontsize=12, fontweight='bold')
        ax1.set_title('Matriz de Decisión Triple (Cascada)', fontsize=14, fontweight='bold')
        ax1.set_xticks(x)
        ax1.set_xticklabels(categories)
        ax1.legend()
        ax1.grid(axis='y', alpha=0.3)
        
        # Plot 2: End-to-End FRR/FAR
        ax2 = plt.subplot(2, 3, 2)
        metrics = results['metrics']
        
        rates = [metrics['end_to_end_frr'] * 100, metrics['end_to_end_far'] * 100]
        colors = ['#e74c3c', '#2ecc71']
        labels = [f"FRR\n{rates[0]:.1f}%", f"FAR\n{rates[1]:.1f}%"]
        
        bars = ax2.bar(['FRR', 'FAR'], rates, color=colors, alpha=0.7, edgecolor='black', linewidth=2)
        
        for bar, rate in zip(bars, rates):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{rate:.2f}%',
                    ha='center', va='bottom', fontsize=12, fontweight='bold')
        
        ax2.set_ylabel('Tasa (%)', fontsize=12, fontweight='bold')
        ax2.set_title('Tasa de Aceptación Sistémica (End-to-End)', fontsize=14, fontweight='bold')
        ax2.set_ylim([0, max(rates) * 1.2])
        ax2.grid(axis='y', alpha=0.3)
        
        # Plot 3: t-DCF Comparison
        ax3 = plt.subplot(2, 3, 3)
        
        tdcf_values = [
            metrics['tdcf_current']['tdcf'],
            metrics['tdcf_optimal']['tdcf']
        ]
        
        bars = ax3.bar(['t-DCF\n(actual)', 't-DCF\n(óptimo)'], tdcf_values, 
                       color=['#3498db', '#2ecc71'], alpha=0.7, edgecolor='black', linewidth=2)
        
        for bar, value in zip(bars, tdcf_values):
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height,
                    f'{value:.4f}',
                    ha='center', va='bottom', fontsize=12, fontweight='bold')
        
        ax3.set_ylabel('t-DCF', fontsize=12, fontweight='bold')
        ax3.set_title('tandem Detection Cost Function', fontsize=14, fontweight='bold')
        ax3.set_ylim([0, max(tdcf_values) * 1.2])
        ax3.grid(axis='y', alpha=0.3)
        
        # Plot 4: Porcentaje de rechazo por etapa (GENUINOS)
        ax4 = plt.subplot(2, 3, 4)
        total_genuine = results['dataset']['genuine_count']
        
        genuine_stages = [
            cascade['genuine']['stage1'] / total_genuine * 100,
            cascade['genuine']['stage2'] / total_genuine * 100,
            cascade['genuine']['stage3'] / total_genuine * 100,
            cascade['genuine']['accepted'] / total_genuine * 100
        ]
        
        colors_pie = ['#e74c3c', '#f39c12', '#3498db', '#2ecc71']
        labels_pie = [
            f'Etapa 1\n{genuine_stages[0]:.1f}%',
            f'Etapa 2\n{genuine_stages[1]:.1f}%',
            f'Etapa 3\n{genuine_stages[2]:.1f}%',
            f'Aceptados\n{genuine_stages[3]:.1f}%'
        ]
        
        ax4.pie(genuine_stages, labels=labels_pie, colors=colors_pie, autopct='',
               startangle=90, textprops={'fontsize': 10, 'fontweight': 'bold'})
        ax4.set_title('Flujo de Genuinos por Cascada', fontsize=14, fontweight='bold')
        
        # Plot 5: Porcentaje de rechazo por etapa (ATAQUES)
        ax5 = plt.subplot(2, 3, 5)
        total_attacks = results['dataset']['total_attacks']
        
        attack_stages = [
            (cascade['tts']['stage1'] + cascade['cloning']['stage1']) / total_attacks * 100,
            (cascade['tts']['stage2'] + cascade['cloning']['stage2']) / total_attacks * 100,
            (cascade['tts']['stage3'] + cascade['cloning']['stage3']) / total_attacks * 100,
            (cascade['tts']['accepted'] + cascade['cloning']['accepted']) / total_attacks * 100
        ]
        
        labels_pie2 = [
            f'Etapa 1\n{attack_stages[0]:.1f}%',
            f'Etapa 2\n{attack_stages[1]:.1f}%',
            f'Etapa 3\n{attack_stages[2]:.1f}%',
            f'Aceptados\n{attack_stages[3]:.1f}%'
        ]
        
        ax5.pie(attack_stages, labels=labels_pie2, colors=colors_pie, autopct='',
               startangle=90, textprops={'fontsize': 10, 'fontweight': 'bold'})
        ax5.set_title('Flujo de Ataques por Cascada', fontsize=14, fontweight='bold')
        
        # Plot 6: Tabla de métricas
        ax6 = plt.subplot(2, 3, 6)
        ax6.axis('off')
        
        table_data = [
            ['Métrica', 'Valor'],
            ['', ''],
            ['End-to-End FRR', f"{metrics['end_to_end_frr']*100:.2f}%"],
            ['End-to-End FAR', f"{metrics['end_to_end_far']*100:.2f}%"],
            ['', ''],
            ['t-DCF (actual)', f"{metrics['tdcf_current']['tdcf']:.4f}"],
            ['t-DCF (mínimo)', f"{metrics['tdcf_optimal']['tdcf']:.4f}"],
            ['Threshold óptimo', f"{metrics['tdcf_optimal']['threshold']:.3f}"],
            ['', ''],
            ['P_miss (ataques aceptados)', f"{metrics['tdcf_current']['P_miss']*100:.2f}%"],
            ['P_fa (genuinos rechazados)', f"{metrics['tdcf_current']['P_fa']*100:.2f}%"],
        ]
        
        table = ax6.table(cellText=table_data, cellLoc='left', loc='center',
                         colWidths=[0.6, 0.4])
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 2)
        
        # Formatear tabla
        for i in range(len(table_data)):
            if i == 0:
                table[(i, 0)].set_facecolor('#3498db')
                table[(i, 1)].set_facecolor('#3498db')
                table[(i, 0)].set_text_props(weight='bold', color='white')
                table[(i, 1)].set_text_props(weight='bold', color='white')
            elif table_data[i][0] == '':
                table[(i, 0)].set_facecolor('#ecf0f1')
                table[(i, 1)].set_facecolor('#ecf0f1')
            else:
                table[(i, 0)].set_facecolor('#ffffff')
                table[(i, 1)].set_facecolor('#f8f9fa')
        
        ax6.set_title('Resumen de Métricas', fontsize=14, fontweight='bold', pad=20)
        
        plt.tight_layout()
        
        # Guardar
        plot_file = results_dir / "tdcf_fusion_system_evaluation.png"
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"📊 Gráficos guardados en: {plot_file}")


if __name__ == "__main__":
    evaluator = TandemDCFFusionEvaluator()
    evaluator.evaluate_system()
