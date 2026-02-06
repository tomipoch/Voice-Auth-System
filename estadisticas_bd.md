# Estadísticas de Frases en Base de Datos

**Fecha de generación**: 9 de diciembre de 2025  
**Base de datos**: PostgreSQL - voice_biometrics  
**Total de frases**: 37,407

---

## 📊 Resumen General

- **Total de frases en BD**: 37,407
- **Libros procesados**: 26
- **Promedio de palabras por frase**: 18.8
- **Promedio de caracteres por frase**: 107.2
- **Idioma**: Español (es)

---

## 📚 Total de Frases por Libro

Esta tabla muestra el **total estimado** de frases de cada libro en la base de datos, combinando:
- **Primera importación** (6,520 frases con nombre de libro individual)
- **Segunda importación masiva** (30,847 frases marcadas como "PDF_Books")

| # | Libro | Frases (aprox.) | % del Total |
|---|-------|-----------------|-------------|
| 1 | 1984 | 4,278 | 11.4% |
| 2 | Veinte mil leguas de viaje submarino | 4,098 | 11.0% |
| 3 | El diario de Ana Frank | 3,498 | 9.3% |
| 4 | La Ilíada | 2,871 | 7.7% |
| 5 | La guerra de los mundos | 2,453 | 6.6% |
| 6 | Viaje al centro de la tierra | 2,509 | 6.7% |
| 7 | Las aventuras de Tom Sawyer | 2,195 | 5.9% |
| 8 | Vuelta al mundo en 80 días | 2,342 | 6.3% |
| 9 | La Odisea | 1,918 | 5.1% |
| 10 | El hombre invisible | 1,898 | 5.1% |
| 11 | La máquina del tiempo | 1,447 | 3.9% |
| 12 | Sub-sole | 1,296 | 3.5% |
| 13 | Sub-terra | 1,424 | 3.8% |
| 14 | El niño del pijama de rayas | 1,086 | 2.9% |
| 15 | El Principito | 438 | 1.2% |
| 16 | Edipo Rey | 300 | 0.8% |
| 17 | El jardín secreto | 145 | 0.4% |
| 18 | Don Quijote de la Mancha | 87 | 0.2% |
| 19 | Dioses y héroes de la mitología | 56 | 0.1% |
| 20 | Ben quiere a Ana | 30 | 0.1% |
| 21 | Momo | 39 | 0.1% |
| 22 | Matilda | 42 | 0.1% |
| 23 | Charlie y la fábrica de chocolate | 22 | 0.1% |
| 24 | Lejos de Frin | 2 | 0.0% |
| 25 | Frin | 0 | 0.0% |
| 26 | El caso del futbolista enmascarado | 0 | 0.0% |

**Nota**: Los números son aproximados porque la segunda importación (30,847 frases) no guardó el nombre individual de cada libro, solo "PDF_Books" como fuente. Los valores se estimaron basándose en las proporciones de la extracción original.

---

## 🔍 Desglose por Fuente de Importación

### Primera Importación (Script Original)
- **Total**: 6,520 frases
- **Característica**: Cada frase tiene el nombre del libro como fuente
- **Criterios**: 5-30 palabras, filtros estrictos

### Segunda Importación (Masiva)
- **Total**: 30,847 frases
- **Característica**: Todas marcadas como "PDF_Books"
- **Criterios**: 8-35 palabras, filtros más flexibles
- **Script**: `generate_more_phrases.py` + `import_phrases.py`

### Otras Fuentes
- **Generated**: 40 frases (frases de prueba/generadas manualmente)

---

## 🎯 Distribución por Dificultad

| Dificultad | Cantidad | Porcentaje | Descripción |
|------------|----------|------------|-------------|
| **Easy** | 11,554 | 30.9% | < 15 palabras |
| **Medium** | 19,335 | 51.7% | 15-24 palabras |
| **Hard** | 6,518 | 17.4% | ≥ 25 palabras |

---

## 📈 Análisis por Género Literario

### Ciencia Ficción (13,176 frases - 35.2%)
- 1984
- La guerra de los mundos
- La máquina del tiempo
- Veinte mil leguas de viaje submarino
- Viaje al centro de la tierra

### Clásicos Universales (3,258 frases - 8.7%)
- La Ilíada
- La Odisea
- Don Quijote
- Edipo Rey

### Literatura Juvenil/Testimonial (4,584 frases - 12.3%)
- El diario de Ana Frank
- El niño del pijama de rayas
- El Principito

### Aventuras (4,537 frases - 12.1%)
- Las aventuras de Tom Sawyer
- Vuelta al mundo en 80 días

### Literatura Chilena (2,720 frases - 7.3%)
- Sub-terra
- Sub-sole

### Literatura Infantil (103 frases - 0.3%)
- Matilda
- Charlie y la fábrica de chocolate
- Momo
- Ben quiere a Ana

---

## 🔧 Información Técnica

### Proceso de Importación
1. **Primera importación**: Script `extract_phrases.py` (6,520 frases)
2. **Segunda importación**: Scripts `generate_more_phrases.py` + `import_phrases.py` (30,847 frases)
3. **Limpieza**: Script `clean_phrases.py` (5,077 frases corregidas en total)

### Criterios de Calidad
- Longitud: 8-35 palabras
- Caracteres: 50-700
- Sin números excesivos
- Sin caracteres especiales excesivos
- Mayúscula inicial
- Sin errores de OCR (corregidos)

### Última Actualización
- **Fecha**: 9 de diciembre de 2025
- **Última limpieza**: 9 de diciembre de 2025
- **Frases corregidas en última ejecución**: 1

---

## 📝 Notas Importantes

1. **Duplicados**: Se eliminaron durante la importación
2. **Calidad**: Todas las frases han sido limpiadas de errores de OCR
3. **Idioma**: 100% español
4. **Fuente**: La mayoría de frases provienen de libros clásicos de dominio público
5. **Uso**: Optimizadas para verificación biométrica de voz
