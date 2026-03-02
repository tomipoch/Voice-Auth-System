# ⚡ QUICK START - Mini Dataset en 30 Minutos

## 🎯 Objetivo
Crear mini-dataset usando el frontend y ejecutar primera evaluación.

---

## 📝 Checklist Rápido

### **1. Verificar Usuarios (2 min)**

```bash
# Ver usuarios existentes
docker exec -it voice-db psql -U voice_user -d voice_biometrics -c "SELECT email FROM users;"
```

**Necesitas:** Mínimo 5 usuarios
- ✅ Si ya tienes 5+: ir al paso 2
- ❌ Si tienes menos: crear más usuarios en el frontend

---

### **2. Realizar Enrollments (20 min)**

**Para cada usuario:**

1. Abrir frontend: `http://localhost:5173`
2. Login con usuario
3. Ir a sección "Enrollment"
4. Grabar 3 frases (el sistema las muestra)
5. Completar enrollment
6. Logout

**Repetir 5-10 veces con diferentes usuarios**

✅ **Checkpoint:** Enrollments completados

---

### **3. Exportar Dataset (1 min)**

```bash
cd Backend

python evaluation/scripts/export_dataset_from_db.py \
    --output evaluation/dataset/from_frontend
```

**Output esperado:**
```
✅ Dataset exported to: evaluation/dataset/from_frontend
📊 8 speakers
📝 Config: evaluation/dataset/from_frontend/dataset_config.json
```

---

### **4. Ejecutar Evaluación (2 min)**

```bash
python evaluation/scripts/evaluate_speaker_verification.py \
    --dataset evaluation/dataset/from_frontend \
    --config dataset_config.json \
    --name primera_evaluacion
```

**Output esperado:**
```
============================================================
RESULTS: primera_evaluacion
============================================================
EER: 0.035 at threshold 0.742
Genuine: 24 tests, μ=0.856
Impostor: 36 tests, μ=0.324
============================================================

✓ Results saved to: evaluation/results/speaker_verification_primera_evaluacion_*.json
```

---

### **5. Visualizar Resultados (1 min)**

```bash
python evaluation/scripts/plot_results.py
```

Ver gráficas en: `evaluation/results/plots/`

---

## 🎉 ¡Listo!

En 30 minutos has:
- ✅ Creado mini-dataset real
- ✅ Ejecutado evaluación completa
- ✅ Calculado FAR, FRR, EER
- ✅ Generado visualizaciones

---

## 📊 Próximos Pasos

### **Mejorar Dataset**
1. Agregar más usuarios (objetivo: 10-15)
2. Hacer verificaciones de prueba
3. Usar evaluation logger para captura automática

### **Evaluación Anti-Spoofing**
```bash
# Generar voces sintéticas
pip install gtts
for i in {1..10}; do
    gtts-cli "Frase de prueba $i" --lang es \
        --output evaluation/dataset/spoof/tts_$i.wav
done

# Evaluar
python evaluation/scripts/evaluate_antispoofing.py \
    --dataset evaluation/dataset \
    --model ensemble_antispoofing
```

### **Evaluación con Logging Automático**
```bash
# Iniciar sesión de evaluación
curl -X POST http://localhost:8000/api/evaluation/start-session \
    -H "Content-Type: application/json" \
    -d '{"session_name": "eval_manual_1"}'

# Usar frontend normalmente (enrollments + verifications)

# Anotar resultados
python evaluation/scripts/annotate_results.py \
    --session eval_manual_1_...
```

---

## 💡 Troubleshooting

**"No users with voiceprints found"**
→ Haz enrollments en el frontend primero

**"Module 'matplotlib' not found"**
→ `pip install matplotlib`

**"Database connection error"**
→ Verifica docker: `docker ps | grep voice-db`

---

## 📚 Más Información

- `evaluation_guide.md` - Guía completa
- `dataset_creation_guide.md` - Métodos de creación
- `walkthrough.md` - Documentación del framework
