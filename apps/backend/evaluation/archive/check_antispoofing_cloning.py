import json
from pathlib import Path

# Cargar evaluación individual de antispoofing
results_file = Path(__file__).parent / "results" / "antispoofing_evaluation.json"
with open(results_file, 'r') as f:
    antispoofing_data = json.load(f)

print("=== EVALUACIÓN INDIVIDUAL ANTISPOOFING ===\n")

genuine_total = 0
genuine_correct = 0
tts_total = 0
tts_detected = 0
cloning_total = 0
cloning_detected = 0

# Identificar por nombre de archivo
for result in antispoofing_data['results']:
    filename = result['filename']
    label = result['true_label']
    predicted = result['predicted_label']
    
    # Los genuinos tienen true_label = 'bonafide'
    if label == 'bonafide':
        genuine_total += 1
        if predicted == 'bonafide':
            genuine_correct += 1
    else:
        # Es un ataque - determinar si es TTS o Cloning por el directorio
        # TTS están en /attacks/, cloning en /cloning/
        if '/attacks/' in filename or 'attacks' in filename.lower():
            tts_total += 1
            if predicted == 'spoof':
                tts_detected += 1
        else:
            cloning_total += 1
            if predicted == 'spoof':
                cloning_detected += 1

print(f"GENUINOS:")
print(f"  Total: {genuine_total}")
print(f"  Correctos (bonafide): {genuine_correct} ({genuine_correct/genuine_total*100:.1f}%)")
print(f"  Falsos rechazos: {genuine_total - genuine_correct} ({(genuine_total - genuine_correct)/genuine_total*100:.1f}%)")

print(f"\nATAQUES TTS:")
print(f"  Total: {tts_total}")
print(f"  Detectados (spoof): {tts_detected} ({tts_detected/tts_total*100:.1f}% ✓)")
print(f"  No detectados: {tts_total - tts_detected} ({(tts_total - tts_detected)/tts_total*100:.1f}%)")

print(f"\nATAQUES CLONING:")
print(f"  Total: {cloning_total}")
print(f"  Detectados (spoof): {cloning_detected} ({cloning_detected/cloning_total*100:.1f}% ✓)")
print(f"  No detectados: {cloning_total - cloning_detected} ({(cloning_total - cloning_detected)/cloning_total*100:.1f}%)")

print(f"\n{'='*60}")
print(f"RESUMEN GLOBAL:")
print(f"  TTS detectados: {tts_detected}/{tts_total} = {tts_detected/tts_total*100:.1f}%")
print(f"  Cloning detectados: {cloning_detected}/{cloning_total} = {cloning_detected/cloning_total*100:.1f}%")
total_attacks = tts_total + cloning_total
total_detected = tts_detected + cloning_detected
print(f"  TODOS los ataques: {total_detected}/{total_attacks} = {total_detected/total_attacks*100:.1f}%")
print(f"{'='*60}")

# Mostrar algunos ejemplos de cloning para verificar
print(f"\nEjemplos de ataques CLONING (primeros 3):")
count = 0
for result in antispoofing_data['results']:
    if result['true_label'] == 'spoof' and '/cloning/' in result.get('filename', '') or 'cloning' in result.get('filename', '').lower():
        if count < 3:
            print(f"  {result['filename']}")
            print(f"    Score: {result['score']:.4f}, Predicted: {result['predicted_label']}")
            count += 1
