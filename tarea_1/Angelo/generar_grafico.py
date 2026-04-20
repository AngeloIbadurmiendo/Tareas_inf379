import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors
from matplotlib.lines import Line2D

plt.rcParams['font.family'] = 'serif'

df_raw = pd.read_csv('data/GlobalLandTemperaturesByCountry_cleaned.csv')
df_raw = df_raw.dropna(subset=['AverageTemperature'])
df_raw['dt'] = pd.to_datetime(df_raw['dt'])
df_raw['year'] = df_raw['dt'].dt.year
df_raw['month'] = df_raw['dt'].dt.month

df_recent = df_raw[df_raw['year'] >= 1990].copy()
df_baseline = df_raw[(df_raw['year'] >= 1950) & (df_raw['year'] < 1990)].copy()

df_annual = df_recent.groupby(['Country', 'year'])['AverageTemperature'].agg(
    temp_min='min', temp_max='max'
)
df_annual['amplitude'] = df_annual['temp_max'] - df_annual['temp_min']

df_country = df_annual.groupby('Country').agg(
    mean_min=('temp_min', 'mean'),
    mean_max=('temp_max', 'mean'),
    mean_amplitude=('amplitude', 'mean')
)

baseline_stats = df_baseline.groupby(['Country', 'month'])['AverageTemperature'].agg(
    hist_mean='mean', hist_std='std'
)
baseline_stats = baseline_stats[baseline_stats['hist_std'] > 0]

df_z = df_recent.merge(baseline_stats, left_on=['Country', 'month'], right_index=True, how='inner')
df_z['z_score'] = (df_z['AverageTemperature'] - df_z['hist_mean']) / df_z['hist_std']

cooling = df_z[df_z['z_score'] < -2]
n_cooling = cooling.groupby('Country').size().rename('n_cooling')
severity = cooling.groupby('Country')['z_score'].mean().abs().rename('severity')

df_final = df_country.join(n_cooling).join(severity).dropna()

min_years = df_recent.groupby('Country')['year'].nunique()
valid_countries = min_years[min_years >= 15].index
df_final = df_final[df_final.index.isin(valid_countries)]

amp_n = (df_final['mean_amplitude'] - df_final['mean_amplitude'].min()) / (df_final['mean_amplitude'].max() - df_final['mean_amplitude'].min())
sev_n = (df_final['severity'] - df_final['severity'].min()) / (df_final['severity'].max() - df_final['severity'].min())
df_final['score'] = amp_n * 0.5 + sev_n * 0.5

top8 = df_final.nlargest(8, 'score').sort_values('mean_amplitude')

fig, ax = plt.subplots(figsize=(14, 8), facecolor='#0d1117')
ax.set_facecolor('#0d1117')

cmap = cm.get_cmap('Blues')
norm = mcolors.Normalize(vmin=top8['severity'].min() * 0.9, vmax=top8['severity'].max() * 1.05)

for i, (country, row) in enumerate(top8.iterrows()):
    color = cmap(norm(row['severity']))
    marker_size = 80 + row['n_cooling'] * 3
    ax.plot([row['mean_min'], row['mean_max']], [i, i], color=color, linewidth=3.5, alpha=0.85, zorder=2)
    ax.scatter(row['mean_min'], i, color=color, s=marker_size, edgecolors='white', linewidth=1, zorder=3, marker='o')
    ax.scatter(row['mean_max'], i, color=color, s=marker_size, edgecolors='white', linewidth=1, zorder=3, marker='D')
    ax.annotate(f'{row["mean_amplitude"]:.1f} °C',
                xy=((row['mean_min'] + row['mean_max']) / 2, i + 0.3),
                ha='center', va='bottom', fontsize=9, color='#c9d1d9', fontweight='bold')
    ax.annotate(f'n={int(row["n_cooling"])}',
                xy=(row['mean_max'] + 0.8, i),
                ha='left', va='center', fontsize=8, color='#8b949e', fontstyle='italic')

global_mean = df_recent['AverageTemperature'].mean()
ax.axvline(x=global_mean, color='#f0883e', linestyle='--', linewidth=1, alpha=0.6, zorder=1)
ax.annotate(f'Media global: {global_mean:.1f} °C', xy=(global_mean, len(top8) - 0.5),
            ha='center', va='bottom', fontsize=8, color='#f0883e', fontstyle='italic')

ax.set_yticks(range(len(top8)))
ax.set_yticklabels(top8.index, fontsize=11, color='#c9d1d9')
ax.set_xlabel('Temperatura Promedio Mensual (°C)', fontsize=12, color='#c9d1d9', labelpad=10)
ax.set_title('Amplitud Térmica Extrema y Anomalías de Enfriamiento por País (1990–2013)',
             fontsize=14, color='#e6edf3', fontweight='bold', pad=20)

ax.tick_params(axis='x', colors='#8b949e')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#30363d')
ax.spines['bottom'].set_color('#30363d')
ax.grid(axis='x', color='#21262d', linestyle='--', alpha=0.7)

sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])
cbar = plt.colorbar(sm, ax=ax, pad=0.02)
cbar.set_label('Severidad de Anomalías de Enfriamiento (|Z-score| medio)', fontsize=10, color='#c9d1d9')
cbar.ax.tick_params(colors='#8b949e')
cbar.outline.set_edgecolor('#30363d')

legend_elements = [
    Line2D([0], [0], marker='o', color='w', label='Temp. Mín. Anual Media',
           markerfacecolor='#58a6ff', markersize=10, linestyle='None'),
    Line2D([0], [0], marker='D', color='w', label='Temp. Máx. Anual Media',
           markerfacecolor='#58a6ff', markersize=10, linestyle='None'),
    Line2D([0], [0], color='#58a6ff', linewidth=3, label='Amplitud Térmica'),
    Line2D([0], [0], color='#f0883e', linewidth=1, linestyle='--', label='Media Global'),
]
ax.legend(handles=legend_elements, loc='lower right', fontsize=9,
          facecolor='#161b22', edgecolor='#30363d', labelcolor='#c9d1d9')

plt.tight_layout()
plt.savefig('Angelo_Ibaceta/grafico_asimetria.png', dpi=300, bbox_inches='tight', facecolor='#0d1117')
plt.close()

print("Top 8 paises seleccionados:")
for c, r in top8.iterrows():
    print(f"  {c}: amp={r['mean_amplitude']:.2f}C, sev={r['severity']:.2f}, n_cooling={int(r['n_cooling'])}, min={r['mean_min']:.2f}, max={r['mean_max']:.2f}")
