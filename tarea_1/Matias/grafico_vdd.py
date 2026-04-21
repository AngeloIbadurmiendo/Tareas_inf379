import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

df = pd.read_csv('data/GlobalTemperatures_limpio.csv')
df['dt'] = pd.to_datetime(df['dt'])
df['Year'] = df['dt'].dt.year
df['Month'] = df['dt'].dt.month

df = df[df['Year'] >= 1850].dropna(subset=['LandAndOceanAverageTemperature'])

df['Decade'] = (df['Year'] // 10) * 10
df_decadas = df.groupby(['Decade', 'Month'])['LandAndOceanAverageTemperature'].mean().reset_index()
df_decadas = df_decadas.sort_values(['Decade', 'Month']).reset_index(drop=True)

min_decade = df_decadas['Decade'].min()
df_decadas['Angle'] = ((df_decadas['Decade'] - min_decade) / 10) * 2 * np.pi + (df_decadas['Month'] - 1) * (2 * np.pi / 12)

theta = df_decadas['Angle'].values
r = df_decadas['LandAndOceanAverageTemperature'].values
decades = df_decadas['Decade'].values

points = np.array([theta, r]).T.reshape(-1, 1, 2)
segments = np.concatenate([points[:-1], points[1:]], axis=1)

fig = plt.figure(figsize=(20, 10))

ax = fig.add_axes([0.25, 0.1, 0.55, 0.8], projection='polar')

cmap = plt.get_cmap('coolwarm')
norm = plt.Normalize(decades.min(), decades.max())

lc = LineCollection(segments, cmap=cmap, norm=norm, alpha=0.9, linewidth=2.5)
lc.set_array(decades[:-1]) 
ax.add_collection(lc)

ax.set_ylim(10, r.max() + 0.5)
ax.set_xticks(np.linspace(0, 2 * np.pi, 12, endpoint=False))
ax.set_xticklabels(['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'])

ax.set_title('Espiral de temperatura global por década (Land & Ocean)\n1850 - Actualidad', va='bottom', fontsize=16, fontweight='bold')
sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])

cbar = fig.colorbar(sm, ax=ax, pad=0.15)
cbar.set_label('Década', rotation=270, labelpad=15)

plt.show()