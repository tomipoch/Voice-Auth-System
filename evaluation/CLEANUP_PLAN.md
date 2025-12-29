# Plan de Limpieza y Reorganización - Evaluation

## Archivos a ELIMINAR (Duplicados/Obsoletos)

### Results - Anti-Spoofing
- ❌ `ANTISPOOFING_COMPLETE_REPORT.txt` (obsoleto, reemplazado por CORRECTED)
- ❌ `antispoof_threshold_analysis.txt` (duplicado)
- ✅ MANTENER: `ANTISPOOFING_CORRECTED_REPORT_RAW.txt`
- ✅ MANTENER: `FEATURE_ENGINEERING_EVALUATION.txt`
- ✅ MANTENER: `THRESHOLD_OPTIMIZATION_REPORT.txt`

### Results - ASR
- ❌ `asr_adjusted_wer_results.txt` (obsoleto)
- ❌ `asr_correct_mapping_results.txt` (obsoleto)
- ❌ `asr_database_results.txt` (obsoleto)
- ❌ `asr_metrics_results.txt` (obsoleto)
- ❌ `audio_phrase_mapping.txt` (obsoleto)
- ✅ MANTENER: `ASR_COMPLETE_METRICS_REPORT.txt`
- ✅ MANTENER: `ASR_THRESHOLD_ANALYSIS.txt`
- ✅ MANTENER: `asr_threshold_analysis.png`

### Results - Speaker Recognition
- ❌ `far_results_threshold_0.3.txt` (análisis individual, no necesario)
- ❌ `far_results_threshold_0.4.txt`
- ❌ `far_results_threshold_0.5.txt`
- ❌ `far_results_threshold_0.6.txt`
- ❌ `far_results_threshold_0.7.txt`
- ❌ `speaker_verification_test_*.csv` (datos crudos)
- ❌ `speaker_verification_test_*.json` (datos crudos)
- ✅ MANTENER: `eer_results.txt`

### Results - System Comparison
- ❌ `model3_asr_results.txt` (duplicado)
- ❌ `test_eval_*.json` (datos crudos)
- ✅ MANTENER: `COMPLETE_SYSTEM_EVALUATION.txt`

### Plots - Duplicados
- ❌ `system_comparison/model3_complete_system.png` (antiguo)
- ❌ `system_comparison/complete_metrics_comparison.png` (antiguo)
- ✅ MANTENER: `complete_system_metrics_updated.png` (NUEVO)
- ✅ MANTENER: `cascade_flow_diagram.png` (NUEVO)

## Archivos a MANTENER

### Documentación (docs/)
✅ TODOS los archivos .md

### Resultados Finales (results/)
✅ Reportes principales de cada módulo
✅ Evaluación del sistema completo

### Gráficos (plots/)
✅ Todos los gráficos actualizados

### Scripts (scripts/)
✅ Scripts de evaluación principales
✅ Scripts de optimización

## Estructura Final

```
evaluation/
├── docs/
│   ├── MODULO_1_SPEAKER_RECOGNITION.md
│   ├── ANTISPOOFING_COMPLETE_ANALYSIS.md
│   ├── MODULO_3_ASR.md
│   ├── RESUMEN_MODULOS_Y_GRAFICOS.md
│   └── GRAFICOS_ACTUALIZADOS.md
│
├── results/
│   ├── speaker_recognition/
│   │   └── eer_results.txt
│   ├── antispoofing/
│   │   ├── ANTISPOOFING_CORRECTED_REPORT_RAW.txt
│   │   ├── FEATURE_ENGINEERING_EVALUATION.txt
│   │   └── THRESHOLD_OPTIMIZATION_REPORT.txt
│   ├── asr/
│   │   ├── ASR_COMPLETE_METRICS_REPORT.txt
│   │   └── ASR_THRESHOLD_ANALYSIS.txt
│   └── system_comparison/
│       └── COMPLETE_SYSTEM_EVALUATION.txt
│
├── plots/
│   ├── speaker_recognition/ (3 archivos)
│   ├── antispoofing/ (4 archivos)
│   ├── asr/ (3 archivos)
│   └── system_comparison/ (2 archivos NUEVOS)
│
└── scripts/
    └── (scripts principales de evaluación)
```
