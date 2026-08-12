# Lógica de Decisión del Sistema: Modelo de Cascada Secuencial

## 🎯 Resumen Ejecutivo

El sistema utiliza un **modelo de cascada secuencial (puertas)**, NO una suma ponderada de scores. Cada módulo actúa como un filtro independiente con su propio threshold, y el audio debe pasar todas las etapas para ser aceptado.

---

## 🚪 Arquitectura de Cascada

```
Audio Input
    ↓
┌─────────────────────────────┐
│  Etapa 1: Antispoofing      │  → ❌ Rechaza si score ≥ 0.994
│  Threshold: 0.994           │
└─────────────────────────────┘
    ↓ Pasa (score < 0.994)
┌─────────────────────────────┐
│  Etapa 2: Speaker Recognition│ → ❌ Rechaza si similarity < 0.707
│  Threshold: 0.707           │
└─────────────────────────────┘
    ↓ Pasa (similarity ≥ 0.707)
┌─────────────────────────────┐
│  Etapa 3: Text Verification │  → ❌ Rechaza si WER ≥ 25%
│  Threshold: 25.0% WER       │
└─────────────────────────────┘
    ↓ Pasa (WER < 25%)
✅ ACEPTADO
```

---

## 📋 Implementación (Código)

### Método: `cascade_decision()`

```python
def cascade_decision(audio_data, enrollment_embeddings, expected_text=None):
    """
    Decisión en cascada: 3 etapas secuenciales.
    Cada etapa puede rechazar el audio (early rejection).
    """
    result = {
        'stage1_antispoof_score': None,
        'stage1_passed': False,
        'stage2_identity_score': None,
        'stage2_passed': False,
        'stage3_text_wer': None,
        'stage3_passed': False,
        'final_decision': False,
        'rejection_stage': None  # 1, 2, 3, o None si acepta
    }
    
    # ETAPA 1: Antispoofing
    spoof_score = spoof_detector.detect_spoof(audio_data)
    result['stage1_antispoof_score'] = spoof_score
    result['stage1_passed'] = spoof_score < 0.994
    
    if not result['stage1_passed']:
        result['rejection_stage'] = 1
        return result  # ❌ Rechazado en Etapa 1
    
    # ETAPA 2: Speaker Recognition
    identity_score = max(similarities_with_enrollments)
    result['stage2_identity_score'] = identity_score
    result['stage2_passed'] = identity_score >= 0.707
    
    if not result['stage2_passed']:
        result['rejection_stage'] = 2
        return result  # ❌ Rechazado en Etapa 2
    
    # ETAPA 3: Text Verification (si aplica)
    if expected_text is not None:
        text_wer = calculate_WER(expected_text, transcribed_text)
        result['stage3_text_wer'] = text_wer
        result['stage3_passed'] = text_wer < 25.0
        
        if not result['stage3_passed']:
            result['rejection_stage'] = 3
            return result  # ❌ Rechazado en Etapa 3
    else:
        result['stage3_passed'] = True
    
    # ✅ ACEPTA: Pasó las 3 etapas
    result['final_decision'] = True
    return result
```

---

## ⚙️ Configuración de Thresholds

```python
thresholds = {
    'antispoof': 0.994,    # Antispoofing: valores bajos = genuino
    'identity': 0.707,     # Speaker Recognition: similitud mínima requerida
    'text_wer': 25.0       # Text Verification: error máximo permitido (%)
}
```

### Interpretación de Scores:

| Módulo | Score Range | Interpretación | Threshold | Condición Aceptación |
|--------|-------------|----------------|-----------|---------------------|
| **Antispoofing** | 0.0 - 1.0 | 0=genuino, 1=spoof | 0.994 | `score < 0.994` |
| **Speaker Recognition** | 0.0 - 1.0 | Similitud coseno normalizada | 0.707 | `score ≥ 0.707` |
| **Text Verification** | 0 - 100 | WER % (Word Error Rate) | 25.0 | `WER < 25.0` |

---

## 🔒 Lógica de Decisión Final

### ✅ Audio ACEPTADO si y solo si:

```python
(antispoof_score < 0.994) AND (identity_score ≥ 0.707) AND (text_wer < 25.0)
```

**Lógica conjuntiva (AND):** Todas las condiciones deben cumplirse.

### ❌ Audio RECHAZADO si:

- **Etapa 1 falla:** `antispoof_score ≥ 0.994` → Audio sintético/fraudulento
- **Etapa 2 falla:** `identity_score < 0.707` → No es el hablante enrollado
- **Etapa 3 falla:** `text_wer ≥ 25.0` → No dijo la frase correcta

---

## 📊 Comparación: Cascada vs Suma Ponderada

### ❌ NO es una Suma Ponderada:

```python
# Esto NO es lo que hace el sistema
score_final = w1 * antispoof + w2 * identity + w3 * text
if score_final > threshold_global:
    ACEPTA
else:
    RECHAZA
```

### ✅ SÍ es un Sistema de Puertas:

```python
# Esto SÍ es lo que hace el sistema
if (antispoof < 0.994):
    if (identity >= 0.707):
        if (text_wer < 25.0):
            ACEPTA
        else:
            RECHAZA  # Falló en Etapa 3
    else:
        RECHAZA  # Falló en Etapa 2
else:
    RECHAZA  # Falló en Etapa 1
```

---

## 🎯 Ventajas del Modelo de Cascada

### 1. **Early Rejection (Ahorro Computacional)**
Si un audio falla en Etapa 1, no se ejecutan las Etapas 2 y 3.
- **Ahorro:** ~67% del procesamiento en audios rechazados tempranamente
- **Eficiencia:** Crítico para sistemas en tiempo real

### 2. **Interpretabilidad**
Se sabe exactamente en qué etapa y por qué falló cada audio.
- **Debugging:** Fácil identificar módulo problemático
- **Explicabilidad:** Transparencia en decisiones del sistema

### 3. **Modularidad**
Cada módulo se optimiza independientemente con su propio threshold.
- **Flexibilidad:** Ajustar un threshold sin afectar otros
- **Mantenimiento:** Actualizar módulos de forma independiente

### 4. **Seguridad por Capas**
Múltiples niveles de defensa independientes.
- **Redundancia:** Si un módulo falla, otros pueden detectar el ataque
- **Robustez:** Difícil evadir todas las capas simultáneamente

---

## 📈 Resultados del Sistema Actual

### Métricas Globales:
- **FRR (False Rejection Rate):** 19.44%
- **FAR (False Acceptance Rate):** 27.84%
- **t-DCF:** 0.4261

### Matriz de Decisión por Etapas:

| Tipo Audio | Rechazados Etapa 1 | Rechazados Etapa 2 | Rechazados Etapa 3 | Aceptados | Total |
|------------|--------------------|--------------------|-----------------------|-----------|-------|
| **Genuinos** | 6 (16.7%) | 0 (0.0%) | 1 (2.8%) | 29 (80.6%) | 36 |
| **TTS** | 53 (88.3%) | 7 (11.7%) | 0 (0.0%) | 0 (0.0%) | 60 |
| **Cloning** | 9 (24.3%) | 0 (0.0%) | 1 (2.7%) | 27 (73.0%) | 37 |

### Interpretación:
- **TTS:** Bloqueados efectivamente en Etapa 1 (88.3%)
- **Cloning:** Vulnerabilidad identificada - pasan Etapa 1 y 2 (usan voz real)
- **Genuinos:** 80.6% aceptados, 19.4% rechazados (principalmente en Etapa 1)

---

## 🔍 Por qué NO se usa Suma Ponderada

### Problemas de la Suma Ponderada:

1. **Compensación indeseable:** Un score alto puede compensar otro bajo
   - Ejemplo: Spoof score 0.99 (malo) + Identity 0.95 (bueno) → Puede aceptar ataque

2. **Difícil interpretabilidad:** No se sabe qué módulo causó la decisión

3. **Optimización compleja:** Encontrar pesos óptimos requiere búsqueda exhaustiva

4. **Menos seguro:** Un solo módulo fuerte puede "rescatar" a los débiles

### Ventaja del Modelo de Cascada:

**Principio de Seguridad:** "La cadena es tan fuerte como su eslabón más débil, pero TODOS los eslabones deben resistir"

---

## 🛠️ Casos Especiales

### Caso 1: Ataques TTS sin Texto Esperado
```python
if expected_text is None:
    # Etapa 3 se considera automáticamente pasada
    result['stage3_passed'] = True
```
Los ataques TTS no tienen frases en el dataset, por lo que solo se evalúan Etapas 1 y 2.

### Caso 2: Múltiples Enrollments
```python
identity_score = max(similarities_with_all_enrollments)
```
Se toma la similitud máxima entre todas las grabaciones de enrollment del usuario.

---

## 📚 Referencias

- **Código fuente:** `apps/backend/evaluation/evaluate_tdcf_system.py`
- **Método principal:** `cascade_decision()` (líneas 132-200)
- **Configuración:** `self.thresholds` (líneas 58-62)
- **Estándar:** ASVspoof 2021 LA Challenge (t-DCF metrics)

---

## 🎓 Conclusión

El sistema implementa un **modelo de cascada estricto con decisión conjuntiva (AND)**, donde cada módulo actúa como un filtro binario independiente. Este diseño prioriza:
- **Seguridad:** Múltiples capas de verificación
- **Eficiencia:** Early rejection
- **Interpretabilidad:** Trazabilidad de decisiones
- **Modularidad:** Optimización independiente

A diferencia de sistemas de fusión por suma ponderada, el modelo de cascada no permite que un módulo "compense" las debilidades de otro, garantizando que todas las verificaciones se cumplan antes de aceptar un audio.
