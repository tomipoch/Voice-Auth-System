"""
Evaluación del Sistema Integrado de Autenticación por Voz
Integra los 3 módulos: Antispoofing + Speaker Recognition + Text Verification

Sistema de decisión:
- Para ACEPTAR un audio, debe pasar los 3 módulos:
  1. Antispoofing: debe ser clasificado como genuino
  2. Speaker Recognition: debe tener alta similitud con el speaker enrollado
  3. Text Verification: debe decir el texto correcto (si aplica)
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


class IntegratedSystemEvaluator:
    """Evaluador del sistema integrado de autenticación por voz."""
    
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
        
        logger.info("✅ Sistema integrado cargado (3 módulos)\n")
        
        # Configuración de fusión multi-modal (antispoofing + speaker)
        self.fusion_weights = {
            'identity': 0.6,
            'antispoof': 0.4
        }
        self.fusion_threshold = 0.45
        
        # Thresholds individuales (optimizados de evaluaciones individuales)
        self.thresholds = {
            'antispoof': 0.994,  # Threshold optimizado de antispoofing evaluation
            'identity': 0.707,   # EER threshold de speaker recognition evaluation
            'text_wer': 25.0     # WER < 25% = texto correcto (promedio 8.04% + 2*std, más realista)
        }
    
    def normalize_text_for_comparison(self, text: str) -> str:
        """Normalizar texto para comparación justa (igual que evaluate_text_verification.py)."""
        import unicodedata
        import re
        
        # Minúsculas
        text = text.lower()
        
        # Quitar tildes
        text = ''.join(
            c for c in unicodedata.normalize('NFD', text)
            if unicodedata.category(c) != 'Mn'
        )
        
        # Quitar puntuación y caracteres especiales
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Normalizar espacios múltiples
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def calculate_wer_levenshtein(self, ref_words: list, hyp_words: list) -> float:
        """Calcular WER con Levenshtein distance (igual que evaluate_text_verification.py)."""
        # Programación dinámica para distancia de edición
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
    
    def verify_audio_integrated(
        self, 
        audio_data: bytes, 
        enrollment_embeddings: List[np.ndarray],
        expected_text: str = None
    ) -> Dict:
        """
        Verificar audio con sistema integrado.
        
        Returns:
            Dict con scores individuales y decisión final
        """
        # Módulo 1: Antispoofing
        spoof_score = self.spoof_detector.detect_spoof(audio_data)
        is_genuine_antispoof = spoof_score < self.thresholds['antispoof']
        
        # Módulo 2: Speaker Recognition
        test_embedding = self.speaker_embedding._extract_real_embedding(audio_data, "audio/wav")
        similarities = []
        for enroll_emb in enrollment_embeddings:
            similarity = self.calculate_cosine_similarity(test_embedding, enroll_emb)
            similarities.append(similarity)
        
        identity_score = max(similarities) if similarities else 0.0
        is_correct_speaker = identity_score >= self.thresholds['identity']
        
        # Fusión multi-modal (antispoofing + speaker)
        fusion_score = (
            self.fusion_weights['identity'] * identity_score + 
            self.fusion_weights['antispoof'] * (1 - spoof_score)
        )
        passes_fusion = fusion_score >= self.fusion_threshold
        
        # Módulo 3: Text Verification (si se proporciona texto esperado)
        text_wer = None
        is_correct_text = True  # Por defecto True si no hay verificación de texto
        transcribed_text = None
        
        if expected_text is not None:
            # Transcribir audio
            transcribed_text = self.asr_adapter.transcribe(audio_data)
            
            # Calcular WER con normalización apropiada y Levenshtein distance
            ref_normalized = self.normalize_text_for_comparison(expected_text)
            hyp_normalized = self.normalize_text_for_comparison(transcribed_text)
            
            ref_words = ref_normalized.split()
            hyp_words = hyp_normalized.split()
            
            # Calcular distancia de Levenshtein (programación dinámica)
            text_wer = self.calculate_wer_levenshtein(ref_words, hyp_words)
            
            is_correct_text = text_wer < self.thresholds['text_wer']
        
        # Decisión final del sistema integrado
        # Estrategia 1: Todos los módulos deben aprobar (AND lógico)
        decision_all_modules = is_genuine_antispoof and is_correct_speaker and is_correct_text
        
        # Estrategia 2: Fusión multi-modal + texto (más permisiva en antispoofing/speaker)
        decision_fusion = passes_fusion and is_correct_text
        
        return {
            'spoof_score': spoof_score,
            'identity_score': identity_score,
            'fusion_score': fusion_score,
            'text_wer': text_wer,
            'transcribed_text': transcribed_text,
            'is_genuine_antispoof': is_genuine_antispoof,
            'is_correct_speaker': is_correct_speaker,
            'is_correct_text': is_correct_text,
            'passes_fusion': passes_fusion,
            'decision_all_modules': decision_all_modules,
            'decision_fusion': decision_fusion,
            'test_embedding': test_embedding
        }
    
    def evaluate_integrated_system(self):
        """Evaluar sistema integrado con dataset."""
        logger.info("=" * 80)
        logger.info("🎯 EVALUACIÓN DEL SISTEMA INTEGRADO")
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
        
        # Resultados
        results = {
            'genuine': [],
            'tts': [],
            'cloning': []
        }
        
        # Procesar genuinos
        logger.info("🟢 Procesando audios genuinos...")
        users = [d for d in genuine_dir.iterdir() if d.is_dir()]
        
        for user_idx, user_dir in enumerate(users, 1):
            username = user_dir.name
            
            # Separar archivos por tipo
            enrollment_audios = sorted([f for f in user_dir.glob("*.wav") if "_enrollment_" in f.name])
            verification_audios = sorted([f for f in user_dir.glob("*.wav") if "_verification_" in f.name])
            
            if len(enrollment_audios) < 3 or len(verification_audios) < 1:
                logger.warning(f"Usuario {username} no tiene suficientes audios (enrollment: {len(enrollment_audios)}, verification: {len(verification_audios)})")
                continue
            
            # Enrollment: audios con "_enrollment_"
            enrollment_embeddings = []
            for enroll_audio in enrollment_audios[:3]:  # Usar primeros 3 enrollments
                try:
                    audio_data = self.load_audio(enroll_audio)
                    embedding = self.speaker_embedding._extract_real_embedding(audio_data, "audio/wav")
                    enrollment_embeddings.append(embedding)
                except Exception as e:
                    logger.error(f"Error enrolling {enroll_audio.name}: {e}")
            
            # Test: audios con "_verification_"
            test_audios = verification_audios
            
            logger.info(f"  Usuario {user_idx}/{len(users)}: {username} - {len(enrollment_audios[:3])} enrollment, {len(test_audios)} verification")
            
            for test_audio in test_audios:
                try:
                    audio_data = self.load_audio(test_audio)
                    
                    # Obtener frase esperada
                    expected_text = expected_phrases.get(test_audio.name, None)
                    
                    # Verificar con sistema integrado
                    result = self.verify_audio_integrated(
                        audio_data, 
                        enrollment_embeddings,
                        expected_text=expected_text
                    )
                    
                    result['username'] = username
                    result['filename'] = test_audio.name
                    result['category'] = 'genuine'
                    
                    results['genuine'].append(result)
                    
                except Exception as e:
                    logger.error(f"Error processing {test_audio.name}: {e}")
        
        logger.info(f"  ✅ Genuinos procesados: {len(results['genuine'])}\n")
        
        # Procesar ataques TTS
        logger.info("🔴 Procesando ataques TTS...")
        
        # Crear un diccionario con los enrollments de cada usuario
        user_enrollments = {}
        for user_dir in users:
            username = user_dir.name
            # Usar solo archivos de enrollment
            enrollment_audios = sorted([f for f in user_dir.glob("*.wav") if "_enrollment_" in f.name])[:3]
            enrollments = []
            for enroll_audio in enrollment_audios:
                try:
                    audio_data = self.load_audio(enroll_audio)
                    embedding = self.speaker_embedding._extract_real_embedding(audio_data, "audio/wav")
                    enrollments.append(embedding)
                except Exception as e:
                    logger.error(f"Error enrolling {enroll_audio.name}: {e}")
            user_enrollments[username] = enrollments
        
        tts_files = list(attacks_dir.rglob("*.wav"))
        
        for attack_audio in tts_files:
            try:
                # Extraer el nombre del usuario víctima del nombre del archivo
                # Formato: {username}_tts_attack_{number}.wav
                victim_username = None
                for username in user_enrollments.keys():
                    if attack_audio.name.startswith(username):
                        victim_username = username
                        break
                
                if not victim_username or not user_enrollments.get(victim_username):
                    logger.warning(f"No se encontró usuario víctima para {attack_audio.name}")
                    continue
                
                audio_data = self.load_audio(attack_audio)
                
                # Usar los enrollments reales del usuario víctima
                victim_enrollments = user_enrollments[victim_username]
                
                # Obtener frase esperada
                expected_text = expected_phrases.get(attack_audio.name, None)
                
                result = self.verify_audio_integrated(
                    audio_data,
                    victim_enrollments,
                    expected_text=expected_text
                )
                
                result['filename'] = attack_audio.name
                result['category'] = 'tts'
                result['victim_user'] = victim_username
                
                results['tts'].append(result)
                
            except Exception as e:
                logger.error(f"Error processing {attack_audio.name}: {e}")
        
        logger.info(f"  ✅ TTS procesados: {len(results['tts'])}\n")
        
        # Procesar ataques de cloning
        logger.info("🔴 Procesando ataques de cloning...")
        cloning_files = list(cloning_dir.rglob("*.wav"))
        
        for attack_audio in cloning_files:
            try:
                # Extraer el nombre del usuario víctima del nombre del archivo
                # Formato: {username}_cloning_attack_{number}.wav
                victim_username = None
                for username in user_enrollments.keys():
                    if attack_audio.name.startswith(username):
                        victim_username = username
                        break
                
                if not victim_username or not user_enrollments.get(victim_username):
                    logger.warning(f"No se encontró usuario víctima para {attack_audio.name}")
                    continue
                
                audio_data = self.load_audio(attack_audio)
                
                # Usar los enrollments reales del usuario víctima
                victim_enrollments = user_enrollments[victim_username]
                
                # Obtener frase esperada
                expected_text = expected_phrases.get(attack_audio.name, None)
                
                result = self.verify_audio_integrated(
                    audio_data,
                    victim_enrollments,
                    expected_text=expected_text
                )
                
                result['filename'] = attack_audio.name
                result['category'] = 'cloning'
                result['victim_user'] = victim_username
                
                results['cloning'].append(result)
                
            except Exception as e:
                logger.error(f"Error processing {attack_audio.name}: {e}")
        
        logger.info(f"  ✅ Cloning procesados: {len(results['cloning'])}\n")
        
        # Calcular métricas
        metrics = self.calculate_metrics(results)
        
        # Generar reportes
        self.generate_reports(results, metrics)
        
        return results, metrics
    
    def calculate_metrics(self, results: Dict) -> Dict:
        """Calcular métricas del sistema integrado."""
        logger.info("📊 Calculando métricas del sistema integrado...\n")
        
        genuine_results = results['genuine']
        all_attacks = results['tts'] + results['cloning']
        
        total_genuine = len(genuine_results)
        total_attacks = len(all_attacks)
        
        # Estrategia 1: Todos los módulos (AND lógico)
        genuine_accepted_all = sum(1 for r in genuine_results if r['decision_all_modules'])
        attacks_rejected_all = sum(1 for r in all_attacks if not r['decision_all_modules'])
        
        bpcer_all = ((total_genuine - genuine_accepted_all) / total_genuine * 100) if total_genuine > 0 else 0
        apcer_all = ((total_attacks - attacks_rejected_all) / total_attacks * 100) if total_attacks > 0 else 0
        acer_all = (bpcer_all + apcer_all) / 2
        
        # Estrategia 2: Fusión multi-modal + texto
        genuine_accepted_fusion = sum(1 for r in genuine_results if r['decision_fusion'])
        attacks_rejected_fusion = sum(1 for r in all_attacks if not r['decision_fusion'])
        
        bpcer_fusion = ((total_genuine - genuine_accepted_fusion) / total_genuine * 100) if total_genuine > 0 else 0
        apcer_fusion = ((total_attacks - attacks_rejected_fusion) / total_attacks * 100) if total_attacks > 0 else 0
        acer_fusion = (bpcer_fusion + apcer_fusion) / 2
        
        # Métricas por módulo individual
        # Antispoofing
        genuine_pass_antispoof = sum(1 for r in genuine_results if r['is_genuine_antispoof'])
        attacks_reject_antispoof = sum(1 for r in all_attacks if not r['is_genuine_antispoof'])
        
        # Speaker Recognition
        genuine_pass_speaker = sum(1 for r in genuine_results if r['is_correct_speaker'])
        attacks_reject_speaker = sum(1 for r in all_attacks if not r['is_correct_speaker'])
        
        # Análisis por tipo de ataque
        tts_results = results['tts']
        cloning_results = results['cloning']
        
        tts_rejected_all = sum(1 for r in tts_results if not r['decision_all_modules'])
        tts_rejected_fusion = sum(1 for r in tts_results if not r['decision_fusion'])
        
        cloning_rejected_all = sum(1 for r in cloning_results if not r['decision_all_modules'])
        cloning_rejected_fusion = sum(1 for r in cloning_results if not r['decision_fusion'])
        
        metrics = {
            'total': {
                'genuine': total_genuine,
                'attacks': total_attacks,
                'tts': len(tts_results),
                'cloning': len(cloning_results)
            },
            'strategy_all_modules': {
                'bpcer': bpcer_all,
                'apcer': apcer_all,
                'acer': acer_all,
                'genuine_accepted': genuine_accepted_all,
                'attacks_rejected': attacks_rejected_all,
                'tts_rejected': tts_rejected_all,
                'cloning_rejected': cloning_rejected_all
            },
            'strategy_fusion': {
                'bpcer': bpcer_fusion,
                'apcer': apcer_fusion,
                'acer': acer_fusion,
                'genuine_accepted': genuine_accepted_fusion,
                'attacks_rejected': attacks_rejected_fusion,
                'tts_rejected': tts_rejected_fusion,
                'cloning_rejected': cloning_rejected_fusion
            },
            'module_antispoofing': {
                'genuine_pass': genuine_pass_antispoof,
                'genuine_pass_rate': genuine_pass_antispoof / total_genuine * 100 if total_genuine > 0 else 0,
                'attacks_reject': attacks_reject_antispoof,
                'attacks_reject_rate': attacks_reject_antispoof / total_attacks * 100 if total_attacks > 0 else 0
            },
            'module_speaker': {
                'genuine_pass': genuine_pass_speaker,
                'genuine_pass_rate': genuine_pass_speaker / total_genuine * 100 if total_genuine > 0 else 0,
                'attacks_reject': attacks_reject_speaker,
                'attacks_reject_rate': attacks_reject_speaker / total_attacks * 100 if total_attacks > 0 else 0
            }
        }
        
        # Mostrar resultados
        logger.info("=" * 80)
        logger.info("📊 RESULTADOS DEL SISTEMA INTEGRADO")
        logger.info("=" * 80)
        logger.info("")
        
        logger.info(f"Dataset:")
        logger.info(f"  - Genuinos: {total_genuine}")
        logger.info(f"  - Ataques: {total_attacks} (TTS: {len(tts_results)}, Cloning: {len(cloning_results)})")
        logger.info("")
        
        logger.info("Estrategia 1: Todos los módulos (AND lógico)")
        logger.info(f"  Thresholds:")
        logger.info(f"    - Antispoofing: {self.thresholds['antispoof']}")
        logger.info(f"    - Speaker Identity: {self.thresholds['identity']}")
        logger.info(f"  BPCER: {bpcer_all:.2f}%")
        logger.info(f"  APCER: {apcer_all:.2f}%")
        logger.info(f"  ACER: {acer_all:.2f}%")
        logger.info(f"  Genuinos aceptados: {genuine_accepted_all}/{total_genuine}")
        logger.info(f"  Ataques rechazados: {attacks_rejected_all}/{total_attacks}")
        logger.info("")
        
        logger.info("Estrategia 2: Fusión Multi-Modal (60/40)")
        logger.info(f"  Pesos: Identity={self.fusion_weights['identity']}, Antispoof={self.fusion_weights['antispoof']}")
        logger.info(f"  Threshold: {self.fusion_threshold}")
        logger.info(f"  BPCER: {bpcer_fusion:.2f}%")
        logger.info(f"  APCER: {apcer_fusion:.2f}%")
        logger.info(f"  ACER: {acer_fusion:.2f}%")
        logger.info(f"  Genuinos aceptados: {genuine_accepted_fusion}/{total_genuine}")
        logger.info(f"  Ataques rechazados: {attacks_rejected_fusion}/{total_attacks}")
        logger.info("")
        
        logger.info("Rendimiento por Módulo:")
        logger.info(f"  Antispoofing:")
        logger.info(f"    - Genuinos aceptados: {genuine_pass_antispoof}/{total_genuine} ({metrics['module_antispoofing']['genuine_pass_rate']:.1f}%)")
        logger.info(f"    - Ataques rechazados: {attacks_reject_antispoof}/{total_attacks} ({metrics['module_antispoofing']['attacks_reject_rate']:.1f}%)")
        logger.info(f"  Speaker Recognition:")
        logger.info(f"    - Genuinos aceptados: {genuine_pass_speaker}/{total_genuine} ({metrics['module_speaker']['genuine_pass_rate']:.1f}%)")
        logger.info(f"    - Ataques rechazados: {attacks_reject_speaker}/{total_attacks} ({metrics['module_speaker']['attacks_reject_rate']:.1f}%)")
        logger.info("")
        
        return metrics
    
    def generate_reports(self, results: Dict, metrics: Dict):
        """Generar reportes y visualizaciones."""
        logger.info("📈 Generando visualizaciones...\n")
        
        output_dir = Path(__file__).parent / "results"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Guardar JSON
        json_path = output_dir / "integrated_system_evaluation.json"
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics,
            'configuration': {
                'fusion_weights': self.fusion_weights,
                'fusion_threshold': self.fusion_threshold,
                'thresholds': self.thresholds
            }
        }
        
        with open(json_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        # Generar visualizaciones
        self.generate_visualizations(results, metrics, output_dir)
        
        logger.info(f"✅ Reportes guardados en: {output_dir}")
    
    def generate_visualizations(self, results: Dict, metrics: Dict, output_dir: Path):
        """Generar gráficos del sistema integrado."""
        fig = plt.figure(figsize=(20, 12))
        
        genuine_results = results['genuine']
        tts_results = results['tts']
        cloning_results = results['cloning']
        all_attacks = tts_results + cloning_results
        
        # Gráfico 1: Comparación de estrategias
        ax1 = plt.subplot(2, 3, 1)
        strategies = ['Estrategia 1\n(AND Lógico)', 'Estrategia 2\n(Fusión 60/40)']
        bpcer_values = [
            metrics['strategy_all_modules']['bpcer'],
            metrics['strategy_fusion']['bpcer']
        ]
        apcer_values = [
            metrics['strategy_all_modules']['apcer'],
            metrics['strategy_fusion']['apcer']
        ]
        
        x = np.arange(len(strategies))
        width = 0.35
        
        bars1 = ax1.bar(x - width/2, bpcer_values, width, label='BPCER', color='#FF6B6B', alpha=0.8)
        bars2 = ax1.bar(x + width/2, apcer_values, width, label='APCER', color='#4ECDC4', alpha=0.8)
        
        ax1.set_ylabel('Error Rate (%)', fontweight='bold', fontsize=11)
        ax1.set_title('Comparación de Estrategias\n(Sistema Integrado)', fontweight='bold', fontsize=13)
        ax1.set_xticks(x)
        ax1.set_xticklabels(strategies, fontsize=10)
        ax1.legend(fontsize=10)
        ax1.grid(True, alpha=0.3, axis='y')
        
        # Valores sobre barras
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.1f}%', ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        # Gráfico 2: Rendimiento por módulo
        ax2 = plt.subplot(2, 3, 2)
        modules = ['Antispoofing', 'Speaker\nRecognition', 'Sistema\nIntegrado\n(Fusión)']
        genuine_rates = [
            metrics['module_antispoofing']['genuine_pass_rate'],
            metrics['module_speaker']['genuine_pass_rate'],
            100 - metrics['strategy_fusion']['bpcer']
        ]
        attack_rates = [
            metrics['module_antispoofing']['attacks_reject_rate'],
            metrics['module_speaker']['attacks_reject_rate'],
            100 - metrics['strategy_fusion']['apcer']
        ]
        
        x = np.arange(len(modules))
        bars1 = ax2.bar(x - width/2, genuine_rates, width, label='Genuinos Aceptados', 
                       color='#95E1D3', alpha=0.8)
        bars2 = ax2.bar(x + width/2, attack_rates, width, label='Ataques Rechazados',
                       color='#F38181', alpha=0.8)
        
        ax2.set_ylabel('Tasa de Éxito (%)', fontweight='bold', fontsize=11)
        ax2.set_title('Rendimiento por Módulo', fontweight='bold', fontsize=13)
        ax2.set_xticks(x)
        ax2.set_xticklabels(modules, fontsize=10)
        ax2.legend(fontsize=9)
        ax2.set_ylim(0, 110)
        ax2.grid(True, alpha=0.3, axis='y')
        
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.1f}%', ha='center', va='bottom', fontsize=8, fontweight='bold')
        
        # Gráfico 3: Dispersión 2D (Identity vs Spoof)
        ax3 = plt.subplot(2, 3, 3)
        
        genuine_identity = [r['identity_score'] for r in genuine_results]
        genuine_spoof = [r['spoof_score'] for r in genuine_results]
        attack_identity = [r['identity_score'] for r in all_attacks]
        attack_spoof = [r['spoof_score'] for r in all_attacks]
        
        ax3.scatter(genuine_identity, genuine_spoof, alpha=0.6, s=60, c='blue',
                   label=f'Genuinos (n={len(genuine_results)})', edgecolors='black', linewidth=0.5)
        ax3.scatter(attack_identity, attack_spoof, alpha=0.6, s=60, c='red',
                   label=f'Ataques (n={len(all_attacks)})', edgecolors='black', linewidth=0.5)
        
        # Línea de decisión de fusión
        x_line = np.linspace(0, 1, 100)
        y_line = 1 - (self.fusion_threshold - self.fusion_weights['identity'] * x_line) / self.fusion_weights['antispoof']
        ax3.plot(x_line, y_line, 'g--', linewidth=2, label='Frontera Fusión 60/40')
        
        ax3.set_xlabel('Identity Score', fontweight='bold', fontsize=11)
        ax3.set_ylabel('Spoof Score', fontweight='bold', fontsize=11)
        ax3.set_title('Espacio de Features 2D\n(Fusión Multi-Modal)', fontweight='bold', fontsize=13)
        ax3.legend(loc='best', fontsize=9)
        ax3.grid(True, alpha=0.3)
        ax3.set_xlim(-0.05, 1.05)
        ax3.set_ylim(-0.05, 1.05)
        
        # Gráfico 4: Detección por tipo de ataque
        ax4 = plt.subplot(2, 3, 4)
        
        categories = ['TTS\nAttacks', 'Cloning\nAttacks', 'All\nAttacks']
        
        rejected_all = [
            metrics['strategy_all_modules']['tts_rejected'] / metrics['total']['tts'] * 100 if metrics['total']['tts'] > 0 else 0,
            metrics['strategy_all_modules']['cloning_rejected'] / metrics['total']['cloning'] * 100 if metrics['total']['cloning'] > 0 else 0,
            (1 - metrics['strategy_all_modules']['apcer'] / 100) * 100
        ]
        
        rejected_fusion = [
            metrics['strategy_fusion']['tts_rejected'] / metrics['total']['tts'] * 100 if metrics['total']['tts'] > 0 else 0,
            metrics['strategy_fusion']['cloning_rejected'] / metrics['total']['cloning'] * 100 if metrics['total']['cloning'] > 0 else 0,
            (1 - metrics['strategy_fusion']['apcer'] / 100) * 100
        ]
        
        x = np.arange(len(categories))
        bars1 = ax4.bar(x - width/2, rejected_all, width, label='Estrategia 1 (AND)',
                       color='#A8E6CF', alpha=0.8)
        bars2 = ax4.bar(x + width/2, rejected_fusion, width, label='Estrategia 2 (Fusión)',
                       color='#FFD3B6', alpha=0.8)
        
        ax4.set_ylabel('Tasa de Detección (%)', fontweight='bold', fontsize=11)
        ax4.set_title('Detección por Tipo de Ataque', fontweight='bold', fontsize=13)
        ax4.set_xticks(x)
        ax4.set_xticklabels(categories, fontsize=10)
        ax4.legend(fontsize=9)
        ax4.set_ylim(0, 110)
        ax4.grid(True, alpha=0.3, axis='y')
        
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax4.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.1f}%', ha='center', va='bottom', fontsize=8, fontweight='bold')
        
        # Gráfico 5: Tabla de métricas finales
        ax5 = plt.subplot(2, 3, 5)
        ax5.axis('off')
        
        table_data = [
            ['Métrica', 'Estrategia 1\n(AND)', 'Estrategia 2\n(Fusión 60/40)'],
            ['BPCER', 
             f"{metrics['strategy_all_modules']['bpcer']:.2f}%",
             f"{metrics['strategy_fusion']['bpcer']:.2f}%"],
            ['APCER',
             f"{metrics['strategy_all_modules']['apcer']:.2f}%",
             f"{metrics['strategy_fusion']['apcer']:.2f}%"],
            ['ACER',
             f"{metrics['strategy_all_modules']['acer']:.2f}%",
             f"{metrics['strategy_fusion']['acer']:.2f}%"],
            ['Genuinos\nAceptados',
             f"{metrics['strategy_all_modules']['genuine_accepted']}/{metrics['total']['genuine']}",
             f"{metrics['strategy_fusion']['genuine_accepted']}/{metrics['total']['genuine']}"],
            ['Ataques\nRechazados',
             f"{metrics['strategy_all_modules']['attacks_rejected']}/{metrics['total']['attacks']}",
             f"{metrics['strategy_fusion']['attacks_rejected']}/{metrics['total']['attacks']}"]
        ]
        
        table = ax5.table(cellText=table_data, cellLoc='center', loc='center',
                         colWidths=[0.3, 0.35, 0.35])
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 2.5)
        
        # Colores
        for i in range(len(table_data)):
            for j in range(3):
                cell = table[(i, j)]
                if i == 0:
                    cell.set_facecolor('#3498DB')
                    cell.set_text_props(weight='bold', color='white')
                elif j == 0:
                    cell.set_facecolor('#ECF0F1')
                    cell.set_text_props(weight='bold')
                elif j == 2:
                    cell.set_facecolor('#D5F4E6')
                    cell.set_text_props(weight='bold')
        
        ax5.set_title('Métricas del Sistema Integrado', fontweight='bold', fontsize=13, pad=20)
        
        # Gráfico 6: Distribución de scores de fusión
        ax6 = plt.subplot(2, 3, 6)
        
        genuine_fusion_scores = [r['fusion_score'] for r in genuine_results]
        attack_fusion_scores = [r['fusion_score'] for r in all_attacks]
        
        bins = np.linspace(0, 1, 30)
        ax6.hist(genuine_fusion_scores, bins=bins, alpha=0.6, color='blue',
                label=f'Genuinos (n={len(genuine_results)})', density=True, edgecolor='black')
        ax6.hist(attack_fusion_scores, bins=bins, alpha=0.6, color='red',
                label=f'Ataques (n={len(all_attacks)})', density=True, edgecolor='black')
        
        ax6.axvline(self.fusion_threshold, color='green', linestyle='--', linewidth=2,
                   label=f'Threshold={self.fusion_threshold}')
        ax6.axvline(np.mean(genuine_fusion_scores), color='blue', linestyle=':',
                   linewidth=1.5, alpha=0.7, label=f'μ Genuinos={np.mean(genuine_fusion_scores):.3f}')
        ax6.axvline(np.mean(attack_fusion_scores), color='red', linestyle=':',
                   linewidth=1.5, alpha=0.7, label=f'μ Ataques={np.mean(attack_fusion_scores):.3f}')
        
        ax6.set_xlabel('Fusion Score (60/40)', fontweight='bold', fontsize=11)
        ax6.set_ylabel('Densidad', fontweight='bold', fontsize=11)
        ax6.set_title('Distribución de Scores Fusionados', fontweight='bold', fontsize=13)
        ax6.legend(loc='upper center', fontsize=8)
        ax6.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        
        output_path = output_dir / "integrated_system_evaluation.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"  ✅ Visualizaciones guardadas: {output_path}")


def main():
    """Función principal."""
    evaluator = IntegratedSystemEvaluator()
    results, metrics = evaluator.evaluate_integrated_system()
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("✅ EVALUACIÓN INTEGRADA FINALIZADA")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
