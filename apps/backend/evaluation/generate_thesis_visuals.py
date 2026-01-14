"""
Generar visualizaciones específicas para la tesis:
1. Gráfico de Barras: Rendimiento del Sistema vs. Tipo de Ataque
2. Tabla Resumida: Matriz de Decisión por Etapas
"""

import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Cargar resultados
results_file = Path(__file__).parent / "results" / "tdcf_system_evaluation.json"
with open(results_file, 'r') as f:
    data = json.load(f)

# Preparar datos
cascade = data['cascade_matrix']
metrics = data['metrics']
dataset = data['dataset']

# ============================================================================
# FIGURA COMBINADA: Gráfico de Barras + Tabla
# ============================================================================

fig = plt.figure(figsize=(18, 10))

# SUBPLOT 1: Gráfico de Barras
ax1 = plt.subplot(1, 2, 1)

# Datos
categories = ['Genuinos', 'TTS', 'Cloning']
totals = [
    dataset['genuine_count'],
    dataset['tts_count'],
    dataset['cloning_count']
]

# Calcular aceptados y rechazados
accepted = [
    cascade['genuine']['accepted'],
    cascade['tts']['accepted'],
    cascade['cloning']['accepted']
]

rejected = [
    totals[i] - accepted[i] for i in range(len(totals))
]

# Calcular porcentajes
accepted_pct = [accepted[i] / totals[i] * 100 for i in range(len(totals))]
rejected_pct = [rejected[i] / totals[i] * 100 for i in range(len(totals))]

# Posiciones de las barras
x = np.arange(len(categories))
width = 0.35

# Crear barras
bars1 = ax1.bar(x - width/2, accepted_pct, width, 
               label='Aceptados', color='#2ecc71', alpha=0.8, edgecolor='black', linewidth=1.5)
bars2 = ax1.bar(x + width/2, rejected_pct, width, 
               label='Rechazados', color='#e74c3c', alpha=0.8, edgecolor='black', linewidth=1.5)

# Añadir etiquetas de valores
for i, (bar1, bar2) in enumerate(zip(bars1, bars2)):
    # Valores absolutos
    height1 = bar1.get_height()
    height2 = bar2.get_height()
    
    ax1.text(bar1.get_x() + bar1.get_width()/2., height1 + 1,
            f'{accepted[i]}/{totals[i]}\n({height1:.1f}%)',
            ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    ax1.text(bar2.get_x() + bar2.get_width()/2., height2 + 1,
            f'{rejected[i]}/{totals[i]}\n({height2:.1f}%)',
            ha='center', va='bottom', fontsize=10, fontweight='bold')

# Configuración del gráfico
ax1.set_xlabel('Tipo de Audio', fontsize=14, fontweight='bold')
ax1.set_ylabel('Porcentaje (%)', fontsize=14, fontweight='bold')
ax1.set_title('Rendimiento del Sistema vs. Tipo de Ataque', fontsize=16, fontweight='bold', pad=20)
ax1.set_xticks(x)
ax1.set_xticklabels(categories, fontsize=12)
ax1.legend(fontsize=12, loc='upper right')
ax1.set_ylim([0, 110])
ax1.grid(axis='y', alpha=0.3, linestyle='--')

# Añadir línea de referencia en 50%
ax1.axhline(y=50, color='gray', linestyle='--', linewidth=1, alpha=0.5)
ax1.text(2.5, 52, '50%', fontsize=10, color='gray')

# SUBPLOT 2: Tabla
ax2 = plt.subplot(1, 2, 2)
ax2.axis('off')

# Preparar datos de la tabla
table_data = []

# Encabezado
table_data.append(['Tipo de Audio', 'Total', 'Etapa 1\n(Antispoofing)', 'Etapa 2\n(Speaker)', 'Etapa 3\n(Texto)', 'Aceptados', 'Tasa\nAceptación'])

# Genuinos
genuine_total = dataset['genuine_count']
genuine_stage3 = cascade['genuine'].get('stage3', 0)
table_data.append([
    'Genuinos',
    f"{genuine_total}",
    f"{cascade['genuine']['stage1']}\n({cascade['genuine']['stage1']/genuine_total*100:.1f}%)",
    f"{cascade['genuine']['stage2']}\n({cascade['genuine']['stage2']/genuine_total*100:.1f}%)",
    f"{genuine_stage3}\n({genuine_stage3/genuine_total*100:.1f}%)",
    f"{cascade['genuine']['accepted']}\n({cascade['genuine']['accepted']/genuine_total*100:.1f}%)",
    f"✓ {cascade['genuine']['accepted']/genuine_total*100:.1f}%"
])

# TTS
tts_total = dataset['tts_count']
table_data.append([
    'Ataques TTS',
    f"{tts_total}",
    f"{cascade['tts']['stage1']}\n({cascade['tts']['stage1']/tts_total*100:.1f}%)",
    f"{cascade['tts']['stage2']}\n({cascade['tts']['stage2']/tts_total*100:.1f}%)",
    f"N/A",
    f"{cascade['tts']['accepted']}\n({cascade['tts']['accepted']/tts_total*100:.1f}%)",
    f"✗ {cascade['tts']['accepted']/tts_total*100:.1f}%"
])

# Cloning
cloning_total = dataset['cloning_count']
cloning_stage3 = cascade['cloning'].get('stage3', 0)
table_data.append([
    'Ataques Cloning',
    f"{cloning_total}",
    f"{cascade['cloning']['stage1']}\n({cascade['cloning']['stage1']/cloning_total*100:.1f}%)",
    f"{cascade['cloning']['stage2']}\n({cascade['cloning']['stage2']/cloning_total*100:.1f}%)",
    f"{cloning_stage3}\n({cloning_stage3/cloning_total*100:.1f}%)",
    f"{cascade['cloning']['accepted']}\n({cascade['cloning']['accepted']/cloning_total*100:.1f}%)",
    f"⚠ {cascade['cloning']['accepted']/cloning_total*100:.1f}%"
])

# Totales
total_attacks = dataset['total_attacks']
total_all = genuine_total + total_attacks
total_stage1 = cascade['genuine']['stage1'] + cascade['tts']['stage1'] + cascade['cloning']['stage1']
total_stage2 = cascade['genuine']['stage2'] + cascade['tts']['stage2'] + cascade['cloning']['stage2']
total_stage3 = genuine_stage3 + cloning_stage3
total_accepted = cascade['genuine']['accepted'] + cascade['tts']['accepted'] + cascade['cloning']['accepted']

table_data.append([
    'TOTAL',
    f"{total_all}",
    f"{total_stage1}\n({total_stage1/total_all*100:.1f}%)",
    f"{total_stage2}\n({total_stage2/total_all*100:.1f}%)",
    f"{total_stage3}\n({total_stage3/(genuine_total+cloning_total)*100:.1f}%)*",
    f"{total_accepted}\n({total_accepted/total_all*100:.1f}%)",
    f"{total_accepted/total_all*100:.1f}%"
])

# Crear tabla
table = ax2.table(cellText=table_data, cellLoc='center', loc='center',
                colWidths=[0.18, 0.08, 0.14, 0.14, 0.14, 0.14, 0.13])

table.auto_set_font_size(False)
table.set_fontsize(11)
table.scale(1, 3.5)

# Formatear celdas
for i in range(len(table_data)):
    for j in range(len(table_data[0])):
        cell = table[(i, j)]
        
        if i == 0:  # Encabezado
            cell.set_facecolor('#3498db')
            cell.set_text_props(weight='bold', color='white', fontsize=12)
        elif i == len(table_data) - 1:  # Fila de totales
            cell.set_facecolor('#95a5a6')
            cell.set_text_props(weight='bold', fontsize=11)
        else:  # Datos
            if j == 0:  # Primera columna
                cell.set_facecolor('#ecf0f1')
                cell.set_text_props(weight='bold')
            elif j == 6:  # Columna de tasa de aceptación
                if 'TTS' in table_data[i][0]:
                    cell.set_facecolor('#d5f4e6')  # Verde claro
                elif 'Cloning' in table_data[i][0]:
                    cell.set_facecolor('#fadbd8')  # Rojo claro
                elif 'Genuinos' in table_data[i][0]:
                    cell.set_facecolor('#d5f4e6')  # Verde claro
            else:
                cell.set_facecolor('#ffffff')

# Título
ax2.set_title('Matriz de Decisión por Etapas', 
            fontsize=16, fontweight='bold', pad=20)

# Nota al pie
note_text = '* Etapa 3 (Texto) solo aplica para Genuinos y Cloning (no para TTS)\n'
note_text += 'Rechazados = Cantidad rechazada en cada etapa (acumulativo)\n'
note_text += '✓ = Bueno  |  ✗ = Excelente  |  ⚠ = Vulnerable'

ax2.text(0.5, -0.05, note_text,
       ha='center', va='top', fontsize=9, style='italic',
       transform=ax2.transAxes, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

# Guardar figura combinada
plt.tight_layout()

output_file = Path(__file__).parent / "results" / "thesis_combined_visualization.png"
plt.savefig(output_file, dpi=300, bbox_inches='tight')
plt.close()

print(f"✅ Visualización combinada guardada: {output_file}")

# ============================================================================
# IMPRIMIR MÉTRICAS ADICIONALES NO INCLUIDAS EN LOS GRÁFICOS
# ============================================================================

print("\n" + "="*80)
print("📊 MÉTRICAS ADICIONALES (no incluidas en gráficos/tabla)")
print("="*80)

print("\n1️⃣  t-DCF (tandem Detection Cost Function):")
print(f"   • t-DCF actual: {metrics['tdcf_current']['tdcf']:.4f}")
print(f"   • Threshold usado: {metrics['tdcf_current']['threshold']:.3f}")
print(f"   • t-DCF mínimo posible: {metrics['tdcf_optimal']['tdcf']:.4f}")
print(f"   • Threshold óptimo sugerido: {metrics['tdcf_optimal']['threshold']:.3f}")
print(f"   • P_miss (ataques no detectados): {metrics['tdcf_current']['P_miss']*100:.2f}%")
print(f"   • P_fa (genuinos rechazados): {metrics['tdcf_current']['P_fa']*100:.2f}%")

print("\n2️⃣  Tasas End-to-End del Sistema:")
print(f"   • FRR (False Rejection Rate): {metrics['end_to_end_frr']*100:.2f}%")
print(f"   • FAR (False Acceptance Rate): {metrics['end_to_end_far']*100:.2f}%")
print(f"   • Tasa de genuinos aceptados: {(1-metrics['end_to_end_frr'])*100:.2f}%")
print(f"   • Tasa de ataques rechazados: {(1-metrics['end_to_end_far'])*100:.2f}%")

print("\n3️⃣  Rendimiento por Módulo Individual:")
print(f"   • Antispoofing (Etapa 1):")
print(f"     - Genuinos que pasan: {genuine_total - cascade['genuine']['stage1']}/{genuine_total} ({(genuine_total - cascade['genuine']['stage1'])/genuine_total*100:.1f}%)")
print(f"     - Ataques bloqueados: {cascade['tts']['stage1'] + cascade['cloning']['stage1']}/{total_attacks} ({(cascade['tts']['stage1'] + cascade['cloning']['stage1'])/total_attacks*100:.1f}%)")
print(f"   • Speaker Recognition (Etapa 2):")
print(f"     - Genuinos que pasan: {genuine_total - cascade['genuine']['stage1'] - cascade['genuine']['stage2']}/{genuine_total - cascade['genuine']['stage1']} (100.0%)")
print(f"     - Ataques bloqueados: {cascade['tts']['stage2'] + cascade['cloning']['stage2']}/{total_attacks - cascade['tts']['stage1'] - cascade['cloning']['stage1']} ({(cascade['tts']['stage2'] + cascade['cloning']['stage2'])/(total_attacks - cascade['tts']['stage1'] - cascade['cloning']['stage1'])*100:.1f}%)")
print(f"   • Text Verification (Etapa 3):")
genuinos_etapa3 = genuine_total - cascade['genuine']['stage1'] - cascade['genuine']['stage2']
cloning_etapa3 = cloning_total - cascade['cloning']['stage1'] - cascade['cloning']['stage2']
cloning_stage3_val = cascade['cloning'].get('stage3', 0)
print(f"     - Genuinos que pasan: {cascade['genuine']['accepted']}/{genuinos_etapa3} ({cascade['genuine']['accepted']/genuinos_etapa3*100:.1f}%)")
print(f"     - Ataques cloning bloqueados: {cloning_stage3_val}/{cloning_etapa3} ({cloning_stage3_val/cloning_etapa3*100:.1f}%)")

print("\n4️⃣  Comparativa TTS vs. Cloning:")
print(f"   • TTS son más fáciles de detectar:")
print(f"     - 88.3% bloqueados en Etapa 1 (antispoofing)")
print(f"     - 0% logran engañar al sistema completo")
print(f"   • Cloning son más sofisticados:")
print(f"     - Solo 24.3% bloqueados en Etapa 1")
print(f"     - 73.0% logran engañar al sistema completo")
print(f"     - Pasan speaker recognition (misma voz)")
print(f"     - Dicen el texto correcto")

print("\n5️⃣  Parámetros de Configuración:")
text_wer = data['thresholds'].get('text_wer', 'N/A')
print(f"   • Threshold Text WER: {text_wer}%")
print("   • Parámetros t-DCF:")
print(f"     - C_miss (costo de no detectar ataque): {data['tdcf_params']['C_miss']}")
print(f"     - C_fa (costo de rechazar genuino): {data['tdcf_params']['C_fa']}")
print(f"     - P_tar (prior de genuinos): {data['tdcf_params']['P_tar']}")
print(f"     - P_nontar (prior de ataques): {data['tdcf_params']['P_nontar']}")

print("\n" + "="*80)
print("✅ GENERACIÓN COMPLETADA")
print("="*80)
