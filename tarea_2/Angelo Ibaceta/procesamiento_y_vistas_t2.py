import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import networkx as nx
from itertools import combinations
import os

def generar_reporte_angelo():
    # 1. Cargar datos
    try:
        df = pd.read_csv('respuestas.csv', sep=';')
    except Exception as e:
        print(f"Error al leer el CSV: {e}")
        return

    # Limpiar nombres de columnas para un acceso mas facil
    df.columns = [
        'Sector_Afectado',
        'Pais_Migrar',
        'Cambio_Temperatura',
        'Grado_Responsabilidad',
        'Transportes',
        'Acciones'
    ]

    # 2. PROCESAMIENTO: Separar respuestas multiples de sector afectado y promediar responsabilidad
    sectores_responsabilidad = []
    for idx, row in df.iterrows():
        sectores = str(row['Sector_Afectado']).split(';')
        for sector in sectores:
            s = sector.strip()
            if s:
                sectores_responsabilidad.append({'Sector': s, 'Responsabilidad': row['Grado_Responsabilidad']})
    
    df_sectores = pd.DataFrame(sectores_responsabilidad)
    df_radar = df_sectores.groupby('Sector')['Responsabilidad'].mean().reset_index()

    # Preparar datos para Gráfico Radar
    categorias = list(df_radar['Sector'])
    valores = list(df_radar['Responsabilidad'])
    
    categorias.append(categorias[0])
    valores.append(valores[0])
    
    angulos = np.linspace(0, 2 * np.pi, len(categorias)-1, endpoint=False).tolist()
    angulos.append(angulos[0])

    # 3. GENERAR GRÁFICO RADAR MEJORADO
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    
    # Rellenar y dibujar línea principal con marcadores
    ax.fill(angulos, valores, color='#1f77b4', alpha=0.25)
    ax.plot(angulos, valores, color='#1f77b4', linewidth=2.5, linestyle='solid', marker='o', markersize=8)
    
    # Ajustar grillas (y-ticks)
    ax.set_yticks([2, 4, 6, 8, 10])
    ax.set_yticklabels(["2", "4", "6", "8", "10/10"], color="dimgrey", size=10, weight='bold')
    ax.set_ylim(0, 10)
    
    # Envolver texto largo para los nombres de los sectores
    import textwrap
    categorias_wrap = [textwrap.fill(cat, 15) for cat in categorias[:-1]]
    ax.set_xticks(angulos[:-1])
    ax.set_xticklabels(categorias_wrap, fontsize=11, weight='bold', color='darkslategray')
    
    # Añadir valores numéricos exactos en cada nodo
    for i in range(len(categorias)-1):
        ax.text(angulos[i], valores[i] + 0.8, f"{valores[i]:.1f}", 
                ha='center', va='center', fontsize=11, weight='bold', color='#1f77b4',
                bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', pad=1))
    
    # Títulos descriptivos
    plt.suptitle("¿Qué tanta responsabilidad sienten frente al Cambio Climático?", 
                 size=15, weight='bold', color='black', y=1.05)
    plt.title("Promedio de responsabilidad (escala 1-10) agrupado por\nel sector que cada grupo considera más afectado.", 
              size=12, color='dimgrey', pad=20)
    
    # Ajustes estéticos de la grilla
    ax.grid(color='lightgrey', linestyle='--', linewidth=1)
    ax.spines['polar'].set_color('lightgrey')
    
    plt.tight_layout()
    plt.savefig('radar_angelo.png', dpi=300, bbox_inches='tight')
    plt.close()

    # 4. PROCESAMIENTO AVANZADO: Grafo de Co-ocurrencia de Transportes
    transportes_listas = []
    frecuencias_nodos = {}
    
    for t_str in df['Transportes'].dropna():
        # Separar por punto y coma y limpiar
        transportes = [t.strip() for t in t_str.split(';') if t.strip()]
        transportes_listas.append(transportes)
        for t in transportes:
            frecuencias_nodos[t] = frecuencias_nodos.get(t, 0) + 1

    # Crear el grafo
    G = nx.Graph()
    
    # Añadir nodos con peso (frecuencia)
    for nodo, frec in frecuencias_nodos.items():
        G.add_node(nodo, weight=frec)
        
    # Añadir aristas (co-ocurrencias)
    co_ocurrencias = {}
    for lista_t in transportes_listas:
        # Generar todos los pares posibles en la respuesta de un usuario
        pares = list(combinations(sorted(lista_t), 2))
        for par in pares:
            co_ocurrencias[par] = co_ocurrencias.get(par, 0) + 1
            
    for par, frec in co_ocurrencias.items():
        G.add_edge(par[0], par[1], weight=frec)

    # 5. GENERAR GRÁFICO DE RED (NETWORK GRAPH) MEJORADO
    plt.figure(figsize=(10, 8))
    
    pos = nx.circular_layout(G)
    
    node_sizes = [G.nodes[n]['weight'] * 600 for n in G.nodes]
    edge_weights = [G.edges[u, v]['weight'] * 2.5 for u, v in G.edges]
    
    # Dibujar componentes con mejores colores
    nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color='lightseagreen', alpha=0.9, edgecolors='white', linewidths=2)
    nx.draw_networkx_edges(G, pos, width=edge_weights, alpha=0.5, edge_color='dimgray', connectionstyle="arc3,rad=0.15", arrows=True, arrowstyle="-")
    
    pos_labels = {k: (v[0], v[1]+0.13) for k, v in pos.items()}
    nx.draw_networkx_labels(G, pos_labels, font_size=11, font_family='sans-serif', font_weight='bold', font_color='darkslategray')
    
    # Añadir caja explicativa para mejorar la lectura a primera vista
    texto_explicativo = (
        "CÓMO LEER EL GRÁFICO:\n"
        "• Tamaño del círculo: Popularidad total del transporte.\n"
        "• Grosor de la línea: Cantidad de encuestados que usan\n"
        "  ambos transportes en su rutina."
    )
    plt.figtext(0.5, 0.02, texto_explicativo, ha="center", fontsize=11, 
                bbox={"facecolor":"whitesmoke", "alpha":0.8, "pad":8, "edgecolor":"lightgrey"})
    
    # Títulos claros
    plt.suptitle("Multimodalidad: ¿Cómo combinamos el transporte?", 
                 size=16, weight='bold', color='black', y=1.02)
    plt.title("Análisis de co-ocurrencia entre los medios de transporte seleccionados.", 
              size=12, color='dimgrey', pad=15)
              
    plt.axis('off')
    plt.margins(0.20)
    plt.subplots_adjust(bottom=0.15) # Ajustar para que no corte el texto explicativo
    plt.savefig('grafo_transportes_angelo.png', dpi=300, bbox_inches='tight')
    plt.close()

    print("Gráficos generados exitosamente: radar_angelo.png y grafo_transportes_angelo.png")
    print("Para generar el documento DOCX, por favor ejecuta 'python generador_informe_docx.py'.")

if __name__ == '__main__':
    generar_reporte_angelo()
