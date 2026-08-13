# Guía de Administración - Sistema de Challenges

## Introducción

Esta guía está diseñada para administradores que necesitan configurar y gestionar el sistema de Challenges y reglas de calidad de frases.

---

## Acceso al Panel de Administración

### Requisitos
- Cuenta con rol `admin` o `superadmin`
- Acceso a la aplicación web

### Acceder al Panel
1. Iniciar sesión en la aplicación
2. Navegar a `/admin/phrase-rules`
3. Verás el panel de configuración de reglas

---

## Configuración de Reglas

### Categorías de Reglas

#### 📊 Thresholds (Umbrales de Calidad)

Estas reglas determinan cuándo una frase debe ser deshabilitada por bajo rendimiento.

**1. Min Success Rate** (Tasa Mínima de Éxito)
- **Rango**: 0.5 - 1.0 (50% - 100%)
- **Default**: 0.70 (70%)
- **Descripción**: Porcentaje mínimo de intentos exitosos para mantener una frase activa
- **Ejemplo**: Si una frase tiene menos del 70% de éxito, se deshabilitará automáticamente

**2. Min ASR Score** (Score Mínimo ASR)
- **Rango**: 0.5 - 1.0
- **Default**: 0.80 (80%)
- **Descripción**: Confianza mínima del reconocimiento de voz automático
- **Ejemplo**: Si el ASR tiene menos del 80% de confianza, la frase puede ser problemática

**3. Min Phrase OK Rate** (Tasa Mínima de Transcripción)
- **Rango**: 0.5 - 1.0
- **Default**: 0.75 (75%)
- **Descripción**: Porcentaje de veces que la frase se transcribe correctamente
- **Ejemplo**: Si solo el 60% de usuarios dicen la frase correctamente, puede ser confusa

**4. Min Attempts For Analysis** (Intentos Mínimos)
- **Rango**: 5 - 50
- **Default**: 10
- **Descripción**: Número mínimo de intentos antes de analizar el rendimiento de una frase
- **Ejemplo**: Se necesitan al menos 10 intentos para tener datos estadísticamente significativos

---

#### ⏱️ Rate Limits (Límites de Uso)

Estas reglas previenen abuso y mejoran la experiencia del usuario.

**1. Exclude Recent Phrases** (Excluir Frases Recientes)
- **Rango**: 10 - 100
- **Default**: 50
- **Descripción**: Número de frases usadas recientemente que no se repetirán
- **Ejemplo**: Las últimas 50 frases usadas no aparecerán nuevamente

**2. Max Challenges Per User** (Máximo de Challenges Activos)
- **Rango**: 1 - 10
- **Default**: 3
- **Descripción**: Máximo de challenges activos simultáneos por usuario
- **Ejemplo**: Un usuario no puede tener más de 3 challenges sin usar al mismo tiempo

**3. Max Challenges Per Hour** (Máximo por Hora)
- **Rango**: 5 - 100
- **Default**: 20
- **Descripción**: Máximo de challenges que un usuario puede crear por hora
- **Ejemplo**: Previene que un usuario cree más de 20 challenges en una hora

---

#### 🧹 Cleanup (Limpieza Automática)

Estas reglas mantienen la base de datos limpia y eficiente.

**1. Challenge Expiry Minutes** (Expiración de Challenges)
- **Rango**: 1 - 60 minutos
- **Default**: 5 minutos
- **Descripción**: Tiempo que un challenge permanece válido
- **Ejemplo**: Un challenge expira 5 minutos después de ser creado

**2. Cleanup Expired After Hours** (Limpiar Expirados)
- **Rango**: 1 - 24 horas
- **Default**: 1 hora
- **Descripción**: Tiempo antes de borrar challenges expirados de la DB
- **Ejemplo**: Los challenges expirados se borran después de 1 hora

**3. Cleanup Used After Hours** (Limpiar Usados)
- **Rango**: 1 - 168 horas (7 días)
- **Default**: 24 horas
- **Descripción**: Tiempo antes de borrar challenges usados de la DB
- **Ejemplo**: Los challenges usados se borran después de 24 horas

---

## Cómo Modificar una Regla

### Paso a Paso

1. **Localizar la regla** en el panel de administración
2. **Mover el slider** al valor deseado
3. **Ver el preview** del nuevo valor en tiempo real
4. **Hacer clic en "Guardar"** para aplicar el cambio
5. **Confirmar** que aparece el mensaje de éxito

### Ejemplo Práctico

**Escenario**: Quieres hacer el sistema más estricto

1. Aumentar `min_success_rate` de 0.70 a 0.80
   - Esto deshabilitará frases con menos del 80% de éxito
   
2. Reducir `max_challenges_per_hour` de 20 a 10
   - Esto limitará el uso excesivo del sistema

3. Reducir `challenge_expiry_minutes` de 5 a 3
   - Esto hará que los challenges expiren más rápido

---

## Activar/Desactivar Reglas

### Cuándo Desactivar una Regla

- **Testing**: Durante pruebas, puedes desactivar rate limits
- **Mantenimiento**: Desactivar cleanup durante migraciones
- **Emergencias**: Desactivar thresholds si muchas frases se deshabilitan

### Cómo Desactivar

1. Hacer clic en el badge **"Activa"** junto al nombre de la regla
2. La regla cambiará a **"Inactiva"**
3. El sistema dejará de aplicar esa regla inmediatamente

### Cómo Reactivar

1. Hacer clic en el badge **"Inactiva"**
2. La regla cambiará a **"Activa"**
3. El sistema volverá a aplicar la regla

---

## Mejores Prácticas

### Configuración Recomendada para Producción

```
Thresholds:
  min_success_rate: 0.70 (70%)
  min_asr_score: 0.80 (80%)
  min_phrase_ok_rate: 0.75 (75%)
  min_attempts_for_analysis: 10

Rate Limits:
  exclude_recent_phrases: 50
  max_challenges_per_user: 3
  max_challenges_per_hour: 20

Cleanup:
  challenge_expiry_minutes: 5
  cleanup_expired_after_hours: 1
  cleanup_used_after_hours: 24
```

### Configuración para Testing/Desarrollo

```
Thresholds:
  min_success_rate: 0.50 (más permisivo)
  min_asr_score: 0.70 (más permisivo)
  min_phrase_ok_rate: 0.60 (más permisivo)
  min_attempts_for_analysis: 5 (menos datos necesarios)

Rate Limits:
  exclude_recent_phrases: 10 (permite más repetición)
  max_challenges_per_user: 10 (más flexible)
  max_challenges_per_hour: 100 (sin límite real)

Cleanup:
  challenge_expiry_minutes: 30 (más tiempo)
  cleanup_expired_after_hours: 24 (mantener más tiempo)
  cleanup_used_after_hours: 168 (mantener una semana)
```

---

## Monitoreo y Análisis

### Métricas a Observar

1. **Tasa de Challenges Expirados**
   - Si es muy alta, aumentar `challenge_expiry_minutes`

2. **Tasa de Rate Limit Hits**
   - Si es muy alta, ajustar `max_challenges_per_hour`

3. **Frases Deshabilitadas**
   - Si son muchas, revisar `min_success_rate`

4. **Uso de Base de Datos**
   - Si crece mucho, reducir `cleanup_*_after_hours`

### Logs de Auditoría

Todos los cambios de reglas se registran en el audit log:
- Quién hizo el cambio
- Qué regla se modificó
- Valor anterior y nuevo
- Timestamp del cambio

---

## Troubleshooting

### Problema: Muchas frases se deshabilitan

**Solución**:
1. Reducir `min_success_rate` a 0.60
2. Reducir `min_asr_score` a 0.70
3. Aumentar `min_attempts_for_analysis` a 20

### Problema: Usuarios reportan challenges expirados

**Solución**:
1. Aumentar `challenge_expiry_minutes` a 10
2. Verificar que el servidor tiene la hora correcta

### Problema: Base de datos crece mucho

**Solución**:
1. Reducir `cleanup_used_after_hours` a 12
2. Reducir `cleanup_expired_after_hours` a 0.5
3. Ejecutar limpieza manual si es necesario

### Problema: Usuarios abusan del sistema

**Solución**:
1. Reducir `max_challenges_per_hour` a 10
2. Reducir `max_challenges_per_user` a 2
3. Revisar logs de auditoría para identificar usuarios

---

## Soporte

Para asistencia adicional:
- Revisar la actividad reciente en `GET /api/admin/activity?limit=100&action=<nombre>` (admin only)
- Auditar reglas de calidad de frases en `GET /api/admin/phrase-rules`
- Consultar documentación técnica en `API_DOCUMENTATION.md`
- Contactar al equipo de desarrollo

---

## Changelog de Configuración

Se recomienda mantener un registro de cambios importantes:

```
2025-12-02: Configuración inicial
  - Todas las reglas en valores por defecto

2025-12-03: Ajuste de rate limits
  - max_challenges_per_hour: 20 → 15
  - Razón: Reducir carga del servidor

2025-12-05: Ajuste de thresholds
  - min_success_rate: 0.70 → 0.75
  - Razón: Mejorar calidad de frases
```
