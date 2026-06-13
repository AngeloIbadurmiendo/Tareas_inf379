import pandas as pd
import pycountry

# ─────────────────────────────────────────────────────────
# 1. Cargar dataset (ya limpiado en T1)
# ─────────────────────────────────────────────────────────
ruta = '../../tarea_1/Angelo/data/GlobalLandTemperaturesByCountry_cleaned.csv'
df = pd.read_csv(ruta)
df['dt'] = pd.to_datetime(df['dt'])
df['year'] = df['dt'].dt.year
df = df.dropna(subset=['AverageTemperature'])
print(f"Dataset cargado: {len(df):,} registros | {df['Country'].nunique()} países")

# ─────────────────────────────────────────────────────────
# 2. Filtrar continentes y separar períodos
# ─────────────────────────────────────────────────────────
no_paises = ['Africa', 'Asia', 'Europe', 'North America', 'South America', 'Oceania', 'Antarctica']
df = df[~df['Country'].isin(no_paises)]

baseline = df[(df['year'] >= 1951) & (df['year'] <= 1980)]
reciente = df[(df['year'] >= 1993) & (df['year'] <= 2013)]

# ─────────────────────────────────────────────────────────
# 3. Promedios por período y cálculo de delta
# ─────────────────────────────────────────────────────────
avg_base = baseline.groupby('Country')['AverageTemperature'].mean().rename('temp_baseline')
avg_rec  = reciente.groupby('Country')['AverageTemperature'].mean().rename('temp_reciente')
unc_base = baseline.groupby('Country')['AverageTemperatureUncertainty'].mean().rename('unc_baseline')
unc_rec  = reciente.groupby('Country')['AverageTemperatureUncertainty'].mean().rename('unc_reciente')

result = pd.concat([avg_base, avg_rec, unc_base, unc_rec], axis=1).dropna()
result['delta_temperatura'] = (result['temp_reciente'] - result['temp_baseline']).round(3)

# Filtro de calidad: mínimo de años con datos en cada período
n_years_base = baseline.groupby('Country')['year'].nunique()
n_years_rec  = reciente.groupby('Country')['year'].nunique()
valid = (n_years_base >= 20) & (n_years_rec >= 15)
result = result[valid].reset_index()
result.rename(columns={'Country': 'Pais'}, inplace=True)

# ─────────────────────────────────────────────────────────
# 4. Categorización para tooltips
# ─────────────────────────────────────────────────────────
def categorizar(delta):
    if delta < 0:    return 'Enfriamiento'
    elif delta < 0.5: return 'Calentamiento leve'
    elif delta < 1.0: return 'Calentamiento moderado'
    elif delta < 1.5: return 'Calentamiento significativo'
    else:             return 'Calentamiento severo'

result['categoria'] = result['delta_temperatura'].apply(categorizar)

# ─────────────────────────────────────────────────────────
# 5. Mapeo de códigos ISO (compatibilidad en Datawrapper)
# ─────────────────────────────────────────────────────────
MANUAL_MAP = {
    'Russia': 'RU', 'South Korea': 'KR', 'North Korea': 'KP', 'Iran': 'IR', 'Syria': 'SY',
    'Bolivia': 'BO', 'Tanzania': 'TZ', 'Venezuela': 'VE', 'Moldova': 'MD', 'Vietnam': 'VN',
    'Laos': 'LA', 'Ivory Coast': 'CI', "Cote D'Ivoire": 'CI', 'Congo': 'CG',
    'Congo (Democratic Republic Of The)': 'CD', 'Burma': 'MM', 'Myanmar': 'MM',
    'Macedonia': 'MK', 'Czech Republic': 'CZ', 'Slovakia': 'SK', 'United States': 'US',
    'United Kingdom': 'GB', 'United Kingdom (Europe)': 'GB', 'France (Europe)': 'FR',
    'Netherlands (Europe)': 'NL', 'Denmark (Europe)': 'DK', 'Gaza Strip': 'PS',
    'Palestina': 'PS', 'Palestine': 'PS', 'Swaziland': 'SZ', 'Eswatini': 'SZ',
    'Timor Leste': 'TL', 'East Timor': 'TL', 'Cape Verde': 'CV', 'Cabo Verde': 'CV',
    'Gambia': 'GM', 'The Gambia': 'GM', 'Turkey': 'TR', 'Turkiye': 'TR',
    'Turks And Caicos Islands': 'TC', 'Turks And Caicas Islands': 'TC'
}

def buscar_iso(nombre):
    if nombre in MANUAL_MAP: return MANUAL_MAP[nombre]
    try:
        pais = pycountry.countries.get(name=nombre)
        if pais: return pais.alpha_2
    except Exception: pass
    try:
        pais = pycountry.countries.get(common_name=nombre)
        if pais: return pais.alpha_2
    except Exception: pass
    try:
        res = pycountry.countries.search_fuzzy(nombre)
        if res: return res[0].alpha_2
    except Exception: pass
    return None

result['ISO_Code'] = result['Pais'].apply(buscar_iso)

# ─────────────────────────────────────────────────────────
# 6. Filtrar solo países soberanos reconocidos
# ─────────────────────────────────────────────────────────
EXCLUIR_ISO = {
    'SJ', 'AX', 'JE', 'GG', 'IM', 'RE', 'PM', 'YT', 'VI', 'VG', 'AI', 'MF', 'SX', 'BL', 'UM', 
    'PR', 'MS', 'GP', 'GF', 'NC', 'MQ', 'GS', 'TC', 'CX', 'KY', 'PF', 'FO', 'FK', 'BQ', 'TF', 
    'AS', 'NU', 'CW', 'AW', 'HM', 'MP', 'GU', 'PS', 'XK'
}

df_final = result[result['ISO_Code'].notna()]
df_final = df_final[~df_final['ISO_Code'].isin(EXCLUIR_ISO)]

# ─────────────────────────────────────────────────────────
# 7. Exportar
# ─────────────────────────────────────────────────────────
cols = ['ISO_Code', 'Pais', 'delta_temperatura', 'temp_baseline', 
        'temp_reciente', 'unc_baseline', 'unc_reciente', 'categoria']
df_final = df_final[cols].sort_values('delta_temperatura', ascending=False)

output_path = 'datos_mapa_t3_final.csv'
df_final.to_csv(output_path, index=False, encoding='utf-8-sig')

# ─────────────────────────────────────────────────────────
# 8. Reporte final
# ─────────────────────────────────────────────────────────
print(f"\n[OK] CSV exportado: {output_path}")
print(f"   Filas: {len(df_final)} países soberanos\n")

print("-- Top 5 mayor calentamiento --")
print(df_final.head(5)[['Pais', 'delta_temperatura', 'categoria']].to_string(index=False))

chile = df_final[df_final['Pais'] == 'Chile']
if not chile.empty:
    row = chile.iloc[0]
    rank = chile.index[0] + 1
    print(f"\n-- Chile --")
    print(f"   Delta:       {row['delta_temperatura']}C")
    print(f"   Categoria:   {row['categoria']}")
    print(f"   Ranking:     #{rank} de {len(df_final)}")
