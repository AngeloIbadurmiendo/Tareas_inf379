import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

df = pd.read_csv('data/GlobalLandTemperaturesByCountry_cleaned.csv')
df = df.dropna(subset=['AverageTemperature'])
df['dt'] = pd.to_datetime(df['dt'])
df['Year'] = df['dt'].dt.year
df['Month'] = df['dt'].dt.month

df = df[(df['Year'] >= 1850)]
df_july = df[df['Month'] == 7].copy()

df_july['Decade'] = (df_july['Year'] // 10) * 10

country_target = 'Norway'
df_country = df_july[df_july['Country'] == country_target]

sns.set_theme(style="white", rc={"axes.facecolor": (0, 0, 0, 0)})

pal = sns.color_palette("YlOrRd", len(df_country['Decade'].unique()))

g = sns.FacetGrid(df_country, row="Decade", hue="Decade", aspect=30, height=0.6, palette=pal)

g.map(sns.kdeplot, "AverageTemperature", bw_adjust=.5, clip_on=False, fill=True, alpha=0.8, linewidth=1.5)
g.map(sns.kdeplot, "AverageTemperature", clip_on=False, color="w", lw=2, bw_adjust=.5)

def label(x, color, label):
    ax = plt.gca()
    ax.text(-0.02, .2, label, fontweight="bold", color=color,
            ha="right", va="center", transform=ax.transAxes)

g.map(label, "AverageTemperature")

g.figure.subplots_adjust(hspace=-0.4)
g.set_titles("")
g.set(yticks=[], ylabel="")
g.despine(bottom=True, left=True)

plt.xlabel("Temperatura Promedio de Julio (°C)")
plt.suptitle(f"Evolución de Temperaturas de Verano por décadas en {country_target} (1850-2013)", y=1.02)
plt.savefig("grafico_ridgeline.png", dpi=300, bbox_inches='tight')
plt.show()