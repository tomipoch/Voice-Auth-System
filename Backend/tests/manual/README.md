# Manual Tests

Este directorio contiene pruebas manuales y scripts de validación del sistema de biometría vocal.

## Archivos Disponibles

### `test_complete_manual.py`
Script completo de pruebas que valida todos los componentes del sistema:
- Modelos de embeddings (ECAPA-TDNN, x-vector)
- Anti-spoofing (RawNet2, AASIST)
- ASR (Automatic Speech Recognition)

### `test_pure_antispoofing.py`
Pruebas específicas para validación anti-spoofing.

## Uso

```bash
# Ejecutar pruebas completas
cd tests/manual/
python test_complete_manual.py

# Ejecutar solo anti-spoofing
python test_pure_antispoofing.py
```

## Requisitos

Estos tests requieren:
- Modelos de ML descargados
- Audio de ejemplo en `audio_samples/`
- Dependencias de ML instaladas

## Nota

Estos son tests de desarrollo y validación, no tests unitarios de producción.
Los tests unitarios están en `tests/unit/` y los de integración en `tests/integration/`.