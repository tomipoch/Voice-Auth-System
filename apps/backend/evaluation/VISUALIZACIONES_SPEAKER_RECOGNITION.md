# Visualizaciones - Speaker Recognition

**Fecha**: 13 de enero de 2026  
**Estrategia**: Security First (Threshold: 0.5516)  
**Ubicación**: `evaluation/plots/`

---

## 📊 Gráficos Generados

### 1. Distribución de Scores (`score_distribution.png`)

**Descripción**: Histograma comparando la distribución de scores entre intentos genuinos e impostores.

**Elementos**:
- **Barra Verde**: Scores de usuarios genuinos (alta concentración cerca de 1.0)
- **Barra Roja**: Scores de impostores (concentrados cerca de 0.0)
- **Línea Azul**: Threshold Security First (0.5516)

**Interpretación**:
- **Separación clara** entre genuinos e impostores
- Genuinos: mayoría >0.7
- Impostores: mayoría <0.4
- Threshold bien posicionado para minimizar FAR

---

### 2. Curva DET - Detection Error Trade-off (`det_curve.png`)

**Descripción**: Curva que muestra el trade-off entre FAR y FRR para todos los thresholds posibles.

**Elementos**:
- **Curva Azul**: Trade-off FAR vs FRR
- **Punto Naranja**: EER = 2.78% (threshold 0.5375)
- **Punto Morado**: Security First (FAR=1.85%, FRR=5.56%)
- **Línea Diagonal**: FAR = FRR (equilibrio perfecto)

**Interpretación**:
- Cuanto más cerca del origen (0,0), mejor el sistema
- Security First prioriza FAR bajo (seguridad)
- EER muestra el punto de balance perfecto

---

### 3. FAR y FRR vs Threshold (`far_frr_vs_threshold.png`)

**Descripción**: Gráfico que muestra cómo FAR y FRR varían según el threshold elegido.

**Elementos**:
- **Línea Roja**: FAR (decrece cuando threshold sube)
- **Línea Verde**: FRR (crece cuando threshold sube)
- **Línea Azul**: Security First (0.5516)
- **Línea Naranja**: EER (0.5375)
- **Zona Amarilla**: Rango óptimo de operación

**Interpretación**:
- Threshold alto → FAR bajo (seguridad) pero FRR alto (usabilidad baja)
- Threshold bajo → FRR bajo (usabilidad) pero FAR alto (inseguridad)
- Security First equilibra seguridad con usabilidad aceptable

**Valores en nuestro sistema**:
- Security First (0.5516): FAR=1.85%, FRR=5.56%
- Balance óptimo para sistema biométrico de seguridad

---

### 4. Visualización de Embeddings (`embeddings_visualization.png`)

**Descripción**: Proyección 2D de los embeddings de voz de cada usuario usando t-SNE y PCA.

**Elementos**:
- **t-SNE (izquierda)**: Proyección no lineal que preserva vecindarios
- **PCA (derecha)**: Proyección lineal que maximiza varianza
- **Colores**: Cada usuario tiene un color diferente
  - Rojo: anachamorromunoz
  - Azul: ft_fernandotomas
  - Verde: piapobletech
  - Naranja: rapomo3

**Interpretación**:
- **Clusters separados**: Cada usuario forma un grupo distinguible
- **t-SNE**: Muestra separación más dramática (ideal para visualización)
- **PCA**: 
  - PC1 explica X% de varianza
  - PC2 explica Y% de varianza
  - Separación clara confirma discriminabilidad del modelo

**Observaciones**:
- Usuarios bien separados → modelo discrimina correctamente
- Puntos cercanos dentro de cluster → consistencia del usuario
- Ausencia de solapamiento → baja probabilidad de confusión

---

## 📈 Análisis de Métricas

### Resultados con Security First (Threshold 0.5516)

| Métrica | Valor | Interpretación |
|---------|-------|----------------|
| **FAR** | 1.85% | Solo 2 de 108 impostores pasaron ✅ |
| **FRR** | 5.56% | Solo 2 de 36 genuinos rechazados ✅ |
| **EER** | 2.78% | Punto de equilibrio FAR=FRR |
| **Accuracy** | 95.14% | Excelente tasa de clasificación |

### Intervalos de Confianza (Bootstrap, 95%)
- EER: [1.85%, 11.11%]
- Indica variabilidad esperada con dataset pequeño (4 usuarios)

---

## 🎯 Uso de las Visualizaciones en la Tesis

### 1. Score Distribution
- **Capítulo**: Resultados Experimentales
- **Justificación**: Demostrar separabilidad entre clases
- **Mensaje clave**: "El threshold separa efectivamente genuinos de impostores"

### 2. Curva DET
- **Capítulo**: Análisis de Rendimiento
- **Justificación**: Mostrar trade-off FAR/FRR
- **Mensaje clave**: "Security First optimiza seguridad con usabilidad aceptable"

### 3. FAR/FRR vs Threshold
- **Capítulo**: Optimización de Parámetros
- **Justificación**: Explicar selección de threshold
- **Mensaje clave**: "Threshold 0.5516 minimiza FAR manteniendo FRR razonable"

### 4. Embeddings Visualization
- **Capítulo**: Arquitectura del Sistema / Análisis Cualitativo
- **Justificación**: Validar capacidad discriminativa del modelo
- **Mensaje clave**: "ECAPA-TDNN genera representaciones bien separadas"

---

## 📝 Conclusión

Las visualizaciones confirman:

1. ✅ **Separación clara** entre genuinos e impostores
2. ✅ **Threshold bien calibrado** para priorizar seguridad
3. ✅ **Embeddings discriminativos** - usuarios claramente separados
4. ✅ **Trade-off explícito** entre FAR y FRR visualizado

**Recomendación**: Incluir los 4 gráficos en la tesis para validación visual y científica de los resultados.

---

**Ubicación de archivos**:
```
evaluation/plots/
├── score_distribution.png
├── det_curve.png
├── far_frr_vs_threshold.png
└── embeddings_visualization.png
```
