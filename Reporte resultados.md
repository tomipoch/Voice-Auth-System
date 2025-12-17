
# Guía Completa para la Implementación y Reporte de Resultados Experimentales
## Sistema de Autenticación Biométrica por Voz con Detección de Deepfakes

---

## 1. Introducción

Este documento describe, de manera detallada y paso a paso, cómo implementar, medir y reportar resultados experimentales en un sistema de autenticación biométrica por voz ya funcional. El objetivo es servir como guía metodológica para la sección de *Resultados Experimentales* de un proyecto de título en Ingeniería Civil Informática, alineada con estándares académicos y métricas biométricas reconocidas (ISO/IEC, ASVspoof).

La comisión evaluadora no espera un sistema productivo a gran escala, sino evidencia clara de que:
- El sistema toma decisiones biométricas reales.
- Dichas decisiones pueden medirse cuantitativamente.
- El autor comprende y aplica correctamente métricas estándar del área.

---

## 2. Principio metodológico fundamental

Antes de evaluar el sistema completo, es necesario descomponerlo en módulos evaluables de forma independiente. Esto permite:
- Entender el comportamiento de cada componente.
- Identificar fuentes de error.
- Justificar decisiones de diseño arquitectónico.

---

## 3. Descomposición del sistema en módulos evaluables

El sistema de autenticación biométrica por voz puede dividirse en los siguientes módulos:

### 3.1 Verificación de locutor
Responsable de determinar si una muestra de voz corresponde al usuario enrolado.

**Métricas asociadas:**
- FAR (False Acceptance Rate)
- FRR (False Rejection Rate)
- EER (Equal Error Rate)

### 3.2 Detección de falsificaciones (Anti-spoofing)
Encargado de identificar ataques mediante replay o voces sintéticas.

**Métricas asociadas:**
- FAR_spoof
- FRR_spoof
- EER_spoof
- Accuracy (opcional)

### 3.3 Sistema completo
Integración de verificación de locutor + anti-spoofing + lógica de decisión.

**Métricas asociadas:**
- EER final del sistema
- Latencia total de autenticación

---

## 4. Diseño experimental y datasets

### 4.1 Uso de datasets públicos

Para un proyecto de título, es totalmente válido y recomendado utilizar datasets públicos ampliamente aceptados en la literatura:

- **VoxCeleb**: verificación de locutor (audios genuinos).
- **ASVspoof 2019 / 2021**: ataques de spoofing (replay, TTS, deepfakes).

No es necesario reentrenar modelos; los audios se procesan directamente mediante el pipeline implementado.

---

### 4.2 Protocolo experimental mínimo

#### 4.2.1 Enrollment
- Seleccionar N usuarios (ej. 20–40).
- Para cada usuario, utilizar 3 audios para generar el voiceprint.

#### 4.2.2 Pruebas genuinas
- Audios adicionales del mismo locutor.
- Resultado esperado: aceptación.

#### 4.2.3 Pruebas impostor
- Audios de otros locutores intentando autenticarse.
- Resultado esperado: rechazo.

#### 4.2.4 Pruebas spoofing
- Audios sintéticos o de replay provenientes de ASVspoof.
- Resultado esperado: rechazo por el módulo anti-spoofing.

---

## 5. Recolección de scores (paso crítico)

Un principio clave en biometría es **no evaluar solo decisiones binarias**, sino **scores continuos**.

Ejemplo de score:
- Similitud coseno entre embeddings.
- Probabilidad de spoofing generada por el ensemble.

Estos valores deben almacenarse para cada prueba.

### 5.1 Ejemplo de estructura de resultados brutos

| prueba_id | tipo_prueba | score_verificacion | score_spoof | etiqueta_real |
|---------|------------|-------------------|-------------|---------------|
| 001 | genuine | 0.82 | 0.05 | genuino |
| 002 | impostor | 0.41 | 0.12 | impostor |
| 003 | spoof | 0.76 | 0.91 | spoof |

---

## 6. Definición y cálculo de métricas biométricas

### 6.1 FAR y FRR

Dado un umbral θ:

- **FAR** = impostores aceptados / total impostores
- **FRR** = genuinos rechazados / total genuinos

El umbral θ se barre en un rango razonable (ej. 0.3 a 0.9).

---

### 6.2 Equal Error Rate (EER)

Procedimiento estándar:
1. Variar el umbral θ.
2. Calcular FAR(θ) y FRR(θ).
3. Encontrar el punto donde FAR ≈ FRR (interpolación lineal aceptada).

El valor correspondiente se reporta como EER.

---

## 7. Evaluación del módulo Anti-spoofing

El sistema anti-spoofing produce una probabilidad p_spoof ∈ [0,1].

### 7.1 Regla de decisión
- Si p_spoof > φ → clasificar como spoof.
- Si p_spoof ≤ φ → clasificar como genuino.

### 7.2 Métricas
- FAR_spoof: spoof aceptado como genuino.
- FRR_spoof: genuino rechazado como spoof.
- EER_spoof: punto de equilibrio.
- Accuracy: métrica complementaria (opcional).

---

## 8. Evaluación del sistema completo

### 8.1 Experimento 1: Sistema sin anti-spoofing
Se evalúa solo la verificación de locutor.

### 8.2 Experimento 2: Anti-spoofing individual
Evaluación separada de cada modelo (AASIST, RawNet2, etc.).

### 8.3 Experimento 3: Sistema final con ensemble
Comparación directa:
- Sin anti-spoofing.
- Con anti-spoofing (ensemble).

Esto permite demostrar empíricamente el impacto del diseño arquitectónico.

---

## 9. Medición de latencia

Se mide el tiempo de ejecución de cada componente:

| Módulo | Latencia promedio |
|------|------------------|
| Extracción de embeddings | XXX ms |
| Anti-spoofing | XXX ms |
| Decisión final | XXX ms |
| Total | XXX ms |

Estas métricas conectan el análisis académico con viabilidad práctica.

---

## 10. Estructura sugerida del capítulo de resultados

1. Diseño experimental
2. Datasets utilizados
3. Métricas de evaluación
4. Resultados de verificación de locutor
5. Resultados de anti-spoofing
6. Resultados del sistema completo
7. Análisis y discusión de resultados

---

## 11. Consideraciones finales

No es obligatorio alcanzar resultados de estado del arte. Lo esencial es:
- Metodología clara y reproducible.
- Uso correcto de métricas estándar.
- Análisis crítico de resultados y limitaciones.

Este enfoque es plenamente suficiente para un proyecto de título y demuestra dominio técnico, criterio ingenieril y comprensión del área de biometría por voz.
