import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.lines import Line2D

df = pd.read_csv('respuestas.csv', sep=';')

# Heatmap

col_acciones = '¿Qué acciones concretas realizas para contribuir a la prevención del cambio climático?'
col_responsabilidad = 'En una escala del 1 al 10, ¿Qué grado de responsabilidad sientes frente al fenómeno del calentamiento global?'

def agrupar_responsabilidad(val):
    try:
        v = int(val)
        if v <= 3: return 'Baja (1-3)'
        elif v <= 7: return 'Media (4-7)'
        else: return 'Alta (8-10)'
    except:
        return 'Desconocido'

df['Grupo Responsabilidad'] = df[col_responsabilidad].apply(agrupar_responsabilidad)

categorias = {
    'Reciclaje': ['reciclar', 'reciclaje', 'basura', 'plástico', 'envases', 'orgánica', 'reciclo'],
    'Ahorrar agua': ['agua', 'duchas', 'ducha'],
    'Ahorrar electricidad': ['luces', 'corriente', 'electricidad', 'apagadas', 'día', 'luz', 'ampolletas', 'desenchufar'],
    'Transporte sostenible': ['transporte', 'público', 'auto', 'bici', 'caminar', 'pie', 'metro', 'micro'],
    'Ninguna': ['ninguna', 'nada', 'no']
}

for cat in categorias: df[cat] = 0
df['Otras acciones'] = 0

for i, row in df.iterrows():
    respuesta = str(row[col_acciones]).lower().strip()
    if respuesta in ['', 'nan', 'ninguna', 'nada']:
        df.at[i, 'Ninguna'] = 1
        continue

    found = False
    for cat, keys in categorias.items():
        if cat != 'Ninguna' and any(k in respuesta for k in keys):
            df.at[i, cat] = 1
            found = True

    if not found:
        df.at[i, 'Otras acciones'] = 1

cols = list(categorias.keys()) + ['Otras acciones']

heatmap_data = (
    df.groupby('Grupo Responsabilidad')[cols]
    .sum()
    .reindex(['Baja (1-3)', 'Media (4-7)', 'Alta (8-10)'])
    .fillna(0)
    .T
)

orden = sorted(
    [c for c in cols if c not in ['Ninguna', 'Otras acciones']],
    key=lambda x: heatmap_data.loc[x].sum(),
    reverse=True
) + ['Otras acciones', 'Ninguna']

heatmap_data = heatmap_data.reindex(orden)

plt.figure(figsize=(10,6))
sns.heatmap(heatmap_data, annot=True, cmap='Greens', linewidths=.5, cbar_kws={'label':'Frecuencia'})
plt.title('Hábitos vs. Grado de Responsabilidad Percibida')
plt.xlabel('Grado de Responsabilidad')
plt.ylabel('Hábitos de Prevención')
plt.tight_layout()
plt.savefig('heatmap.png', dpi=300)
plt.show()


# TREEMAP

col_transporte = 'Elige 4 transportes que usas frecuentemente'

transportes = df[col_transporte].dropna().str.split(';').explode().str.strip()

def clasificar(t):
    t = str(t).lower()
    if any(x in t for x in ['eléctrico', 'metro', 'pie', 'bici', 'bicicleta', 'trole']):
        return 'Bajo Impacto'
    elif any(x in t for x in ['micro', 'bus', 'colectivo']):
        return 'Medio Impacto'
    elif any(x in t for x in ['auto', 'moto', 'taxi', 'uber', 'avión']):
        return 'Alto Impacto'
    return 'Otro'

df_trans = pd.DataFrame({'Transporte': transportes})
df_trans['Impacto'] = df_trans['Transporte'].apply(clasificar)

counts = df_trans.groupby(['Impacto', 'Transporte']).size().reset_index(name='Freq')

colores = {
    'Bajo Impacto': '#A8E6CF',
    'Medio Impacto': '#FFD3B6',
    'Alto Impacto': '#FF8B94'
}

def layout(sizes, x, y, w, h):
    if len(sizes) == 1:
        return [{'x': x, 'y': y, 'w': w, 'h': h}]
    mid = len(sizes) // 2
    s1, s2 = sum(sizes[:mid]), sum(sizes[mid:])
    total = s1 + s2
    if w > h:
        w1 = w * s1 / total
        return layout(sizes[:mid], x, y, w1, h) + layout(sizes[mid:], x+w1, y, w-w1, h)
    else:
        h1 = h * s1 / total
        return layout(sizes[:mid], x, y, w, h1) + layout(sizes[mid:], x, y+h1, w, h-h1)

fig, ax = plt.subplots(figsize=(10,10))

totales = counts.groupby('Impacto')['Freq'].sum()
total = totales.sum()

h_alto = 100 * totales.get('Alto Impacto', 0) / total
h_top = 100 - h_alto

den = totales.get('Bajo Impacto', 0) + totales.get('Medio Impacto', 1)
w_bajo = 100 * totales.get('Bajo Impacto', 0) / den

contenedores = [
    {'id':'Bajo Impacto', 'x':0, 'y':h_alto, 'w':w_bajo, 'h':h_top},
    {'id':'Medio Impacto', 'x':w_bajo, 'y':h_alto, 'w':100-w_bajo, 'h':h_top},
    {'id':'Alto Impacto', 'x':0, 'y':0, 'w':100, 'h':h_alto}
]

for c in contenedores:
    sub = counts[counts['Impacto'] == c['id']].sort_values('Freq', ascending=False)
    if sub.empty: continue

    rects = layout(sub['Freq'].tolist(), c['x'], c['y'], c['w'], c['h'])

    for i, r in enumerate(rects):
        ax.add_patch(
            patches.Rectangle(
                (r['x'], r['y']), r['w'], r['h'],
                facecolor=colores[c['id']],
                edgecolor='white',
                linewidth=3
            )
        )

        if r['w'] > 6 and r['h'] > 6:
            ax.text(
                r['x'] + r['w']/2,
                r['y'] + r['h']/2,
                f"{sub.iloc[i]['Transporte']}\n({sub.iloc[i]['Freq']})",
                ha='center', va='center', fontsize=10, weight='bold'
            )

ax.set_xlim(0,100)
ax.set_ylim(0,100)
ax.axis('off')

legend = [
    Line2D([0],[0], marker='s', color='w', label=k, markerfacecolor=v, markersize=15)
    for k, v in colores.items()
]

ax.legend(handles=legend, loc='lower center', bbox_to_anchor=(0.5,-0.08), ncol=3, frameon=False)

plt.title('Transportes más Usados y su Impacto Ambiental')
plt.savefig('treemap.png', dpi=300, bbox_inches='tight')
plt.show()