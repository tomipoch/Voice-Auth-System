# Evaluación del Sistema Biométrico

Carpeta de evaluación del sistema biométrico de voz.

## 📁 Estructura

```
evaluation/
├── scripts/              # Scripts de evaluación
├── dataset/             # Datos (recordings, attacks, cloning)
├── results/             # Resultados de evaluaciones
├── docs/                # Documentación
├── plots/               # Gráficos generados
└── logs/                # Logs de ejecución
```

## 🔧 Scripts Principales

### Evaluación por Módulo
- `evaluate_speaker_verification.py` - Reconocimiento de hablante
- `evaluate_antispoofing.py` - Anti-spoofing
- `evaluate_asr.py` - ASR (Automatic Speech Recognition)

### Gestión de Datos
- `export_dataset_from_db.py` - Exportar datos desde la base de datos
- `create_dataset_config.py` - Configurar dataset

### Análisis y Resultados
- `metrics_calculator.py` - Cálculo de métricas
- `results_manager.py` - Gestión de resultados
- `annotate_results.py` - Anotación de resultados
- `plot_results.py` - Generación de gráficos

### Utilidades
- `evaluation_logger.py` - Logger de evaluación

## 📚 Documentación

- `docs/EVALUACION_COMPLETA_SISTEMA_BIOMETRICO.md` - Evaluación completa
- `docs/FINAL_COMPLETE_METRICS_REPORT.md` - Reporte final de métricas
- `docs/evaluation_guide.md` - Guía de evaluación
- `docs/QUICKSTART.md` - Inicio rápido
- `docs/ELEVENLABS_VOICE_CLONING_GUIDE.md` - Guía de clonación de voz
- `docs/SPOOF_ATTACKS_CAPTURE_GUIDE.md` - Guía de ataques de spoofing

## 🚀 Uso

1. **Exportar datos desde la base de datos:**
   ```bash
   python scripts/export_dataset_from_db.py
   ```

2. **Evaluar módulos:**
   ```bash
   python scripts/evaluate_speaker_verification.py
   python scripts/evaluate_antispoofing.py
   python scripts/evaluate_asr.py
   ```

3. **Generar gráficos:**
   ```bash
   python scripts/plot_results.py
   ```

## 📊 Resultados

Los resultados se guardan en:
- `results/` - Archivos JSON/CSV
- `plots/` - Gráficos PNG
- `logs/` - Logs de ejecución
