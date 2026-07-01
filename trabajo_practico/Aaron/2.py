from pathlib import Path
import re
import unicodedata
from difflib import get_close_matches

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent
TEMP_PATH = ROOT / "GlobalLandTemperaturesByMajorCity.csv"
XLSX_PATH = ROOT / "EDGAR_2025_GHG_booklet_2025.xlsx"
OUT_DIR = ROOT / "prepared_data"
OUT_DIR.mkdir(exist_ok=True)


def read_edgar_sheets(xlsx_path: Path) -> dict[str, pd.DataFrame]:
    """Lee las hojas relevantes del archivo Excel EDGAR y exporta CSV auxiliares."""
    xls = pd.ExcelFile(xlsx_path)
    sheet_names = xls.sheet_names

    selected = {}
    lower_names = [s.lower() for s in sheet_names]

    for key, needle in {
        "totals": "totals",
        "capita": "capita",
        "gdp": "gdp",
    }.items():
        matches = [s for s in sheet_names if needle in s.lower()]
        if matches:
            selected[key] = matches[0]

    if not selected.get("totals"):
        raise FileNotFoundError("No se encontró una hoja de totales de GHG en el Excel.")
    if not selected.get("capita"):
        raise FileNotFoundError("No se encontró una hoja de emisiones per cápita en el Excel.")
    if not selected.get("gdp"):
        raise FileNotFoundError("No se encontró una hoja de emisiones por PIB en el Excel.")

    frames = {}
    for key, sheet_name in selected.items():
        df = pd.read_excel(xlsx_path, sheet_name=sheet_name)
        df = df.copy()
        df.columns = [str(c).strip() for c in df.columns]

        if df.empty:
            raise ValueError(f"La hoja {sheet_name} está vacía.")

        country_candidates = [
            c for c in df.columns if c.lower() in {"country", "countries", "entity", "name", "country/region"}
        ]
        if country_candidates:
            country_col = country_candidates[0]
        else:
            country_col = df.columns[0]

        df = df[[country_col] + [c for c in df.columns if c != country_col]].copy()
        df = df.rename(columns={country_col: "Country"})
        df["Country"] = df["Country"].astype(str).str.strip()
        df = df[df["Country"].ne("")].copy()

        year_cols = [c for c in df.columns if str(c).strip() == "2010"]
        if not year_cols:
            year_cols = [c for c in df.columns if str(c).strip().startswith("20") and str(c).strip() in {"2010"}]
        if not year_cols:
            year_cols = [c for c in df.columns if str(c).strip().isdigit() and int(str(c).strip()) >= 1990]
        if not year_cols:
            raise ValueError(f"No se encontró una columna de año válida en la hoja {sheet_name}.")

        value_col = year_cols[0]
        df = df[["Country", value_col]].copy()
        df = df.rename(columns={value_col: f"{key.upper()}_2010"})
        df[f"{key.upper()}_2010"] = pd.to_numeric(df[f"{key.upper()}_2010"], errors="coerce")
        frames[key] = df

        output_name = {
            "totals": "ghg_totals_by_country.csv",
            "capita": "ghg_per_capita_by_country.csv",
            "gdp": "ghg_per_gdp_by_country.csv",
        }[key]
        df.to_csv(OUT_DIR / output_name, index=False)

    return frames


def normalize_country(name: str) -> str:
    """Normaliza nombres de países quitando acentos, puntuación y espacios extras."""
    if pd.isna(name):
        return ""

    text = str(name).strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_latitude(value: object) -> float | None:
    """Convierte valores como 5.63N o 23S a grados absolutos."""
    if pd.isna(value):
        return None

    text = str(value).strip()
    if not text:
        return None

    direction = text[-1].upper()
    number = float(re.sub(r"[^0-9.\-]+", "", text))
    if direction == "S":
        return abs(number) * -1
    if direction == "N":
        return abs(number)
    return number


def load_optional_lulucf_data(root: Path) -> pd.DataFrame:
    """Carga datos LULUCF si existe un archivo compatible en la carpeta del script."""
    candidates = [
        root / "LULUCF_countries.csv",
        root / "LULUCF.csv",
        root / "lulucf_countries.csv",
        root / "LULUCF_countries.xlsx",
    ]

    for path in candidates:
        if not path.exists():
            continue

        if path.suffix.lower() == ".csv":
            df = pd.read_csv(path)
        elif path.suffix.lower() == ".xlsx":
            df = pd.read_excel(path)
        else:
            continue

        df = df.copy()
        df.columns = [str(c).strip() for c in df.columns]

        country_candidates = [c for c in df.columns if c.lower() in {"country", "countries", "entity", "name"}]
        country_col = country_candidates[0] if country_candidates else df.columns[0]

        year_candidates = [c for c in df.columns if str(c).strip() == "2010"]
        if not year_candidates:
            year_candidates = [c for c in df.columns if str(c).strip().isdigit() and int(str(c).strip()) >= 1990]
        if not year_candidates:
            continue

        value_col = year_candidates[0]
        out = df[[country_col, value_col]].copy()
        out = out.rename(columns={country_col: "Country", value_col: "LULUCF_2010"})
        out["Country"] = out["Country"].astype(str).str.strip()
        out["LULUCF_2010"] = pd.to_numeric(out["LULUCF_2010"], errors="coerce")
        return out

    return pd.DataFrame(columns=["Country", "LULUCF_2010"])


def canonicalize_country(name: str, reference_countries: list[str] | None = None) -> str:
    """Normaliza nombres de países usando aliases y coincidencia difusa."""
    alias_map = {
        "burma": "Myanmar",
        "myanmar": "Myanmar",
        "congo democratic republic of the": "Democratic Republic of the Congo",
        "democratic republic of the congo": "Democratic Republic of the Congo",
        "cote d ivoire": "Ivory Coast",
        "ivory coast": "Ivory Coast",
        "curacao": "Curaçao",
        "curaçao": "Curaçao",
        "reunion": "Réunion",
        "réunion": "Réunion",
        "sao tome and principe": "São Tomé and Príncipe",
        "sao tomé and príncipe": "São Tomé and Príncipe",
        "united states": "United States",
        "united states of america": "United States",
        "russia": "Russia",
        "russian federation": "Russia",
        "czechia": "Czechia",
        "czech republic": "Czechia",
        "south korea": "South Korea",
        "korea republic of": "South Korea",
        "republic of korea": "South Korea",
        "north korea": "North Korea",
        "democratic people s republic of korea": "North Korea",
        "iran": "Iran",
        "islamic republic of iran": "Iran",
        "turkiye": "Türkiye",
        "turkey": "Türkiye",
        "türkiye": "Türkiye",
        "bolivia": "Bolivia",
        "plurinational state of bolivia": "Bolivia",
        "vietnam": "Vietnam",
        "viet nam": "Vietnam",
        "moldova": "Moldova",
        "republic of moldova": "Moldova",
        "china": "China",
        "india": "India",
        "brazil": "Brazil",
        "japan": "Japan",
        "germany": "Germany",
        "united kingdom": "United Kingdom",
        "uk": "United Kingdom",
        "great britain": "United Kingdom",
        "france": "France",
        "australia": "Australia",
        "canada": "Canada",
        "mexico": "Mexico",
        "south africa": "South Africa",
        "republic of south africa": "South Africa",
        "indonesia": "Indonesia",
        "saudi arabia": "Saudi Arabia",
        "argentina": "Argentina",
        "chile": "Chile",
        "colombia": "Colombia",
        "egypt": "Egypt",
        "nigeria": "Nigeria",
        "pakistan": "Pakistan",
        "philippines": "Philippines",
        "thailand": "Thailand",
        "ukraine": "Ukraine",
        "poland": "Poland",
        "italy": "Italy",
        "spain": "Spain",
        "netherlands": "Netherlands",
        "sweden": "Sweden",
        "norway": "Norway",
    }

    if pd.isna(name):
        return ""

    norm = normalize_country(name)
    if not norm:
        return ""

    if norm in alias_map:
        return alias_map[norm]

    if reference_countries:
        ref_lookup = {normalize_country(c): c for c in reference_countries if str(c).strip()}
        if norm in ref_lookup:
            return ref_lookup[norm]

        matches = get_close_matches(norm, list(ref_lookup.keys()), n=1, cutoff=0.7)
        if matches:
            return ref_lookup[matches[0]]

    return " ".join(part.capitalize() for part in norm.split())


# 1. Preparar datos de temperatura
try:
    temp = pd.read_csv(TEMP_PATH)
except Exception as exc:
    raise RuntimeError(f"No se pudo leer {TEMP_PATH}: {exc}")

temp["dt"] = pd.to_datetime(temp["dt"], errors="coerce")
temp = temp.dropna(subset=["dt", "AverageTemperature"]).copy()
temp = temp.sort_values(["Country", "City", "dt"]).copy()

# Suavizado MA12 por ciudad, siguiendo la estrategia del script exploratorio.
if "AverageTemperature" in temp.columns:
    temp["MA12"] = (
        temp.groupby(["Country", "City"])["AverageTemperature"]
        .transform(lambda s: s.rolling(12, min_periods=1, center=True).mean())
    )

temp["Temp_Value"] = temp["MA12"].where(temp["MA12"].notna(), temp["AverageTemperature"])
temp["Year"] = temp["dt"].dt.year

if "Latitude" in temp.columns:
    temp["Latitude_Abs"] = temp["Latitude"].apply(parse_latitude).abs()
else:
    temp["Latitude_Abs"] = np.nan

temp_baseline = (
    temp[(temp["Year"] >= 1850) & (temp["Year"] <= 1900)]
    .groupby("Country", as_index=False)["Temp_Value"]
    .mean()
    .rename(columns={"Temp_Value": "BaselineTemp"})
)

temp_window = (
    temp[(temp["Year"] >= 2008) & (temp["Year"] <= 2012)]
    .groupby("Country", as_index=False)["Temp_Value"]
    .mean()
    .rename(columns={"Temp_Value": "Temp_2010"})
)

country_lat = temp.groupby("Country", as_index=False)["Latitude_Abs"].mean()

temp_df = temp_window.merge(temp_baseline, on="Country", how="left").merge(country_lat, on="Country", how="left")
temp_df["Temp_Anomaly_2010"] = temp_df["Temp_2010"] - temp_df["BaselineTemp"]
temp_df = temp_df.dropna(subset=["Temp_Anomaly_2010"])

# 2. Preparar tablas EDGAR y exportar CSV auxiliares
frames = read_edgar_sheets(XLSX_PATH)
merged = frames["totals"].merge(frames["capita"], on="Country", how="inner").merge(frames["gdp"], on="Country", how="inner")
merged = merged.rename(columns={"TOTALS_2010": "GHG_Total", "CAPITA_2010": "GHG_Per_Capita", "GDP_2010": "GHG_Per_GDP"})

# Integración opcional de LULUCF cuando el archivo está disponible.
lulucf = load_optional_lulucf_data(ROOT)
if not lulucf.empty:
    merged = merged.merge(lulucf, on="Country", how="left")
    merged["GHG_Total"] = merged["GHG_Total"].fillna(0) + merged["LULUCF_2010"].fillna(0)

# 3. Unificar nombres de países de forma robusta
reference_countries = sorted(set(temp_df["Country"]).union(set(merged["Country"])))

# Limpiar y normalizar nombres de país antes del cruce
for frame in (temp_df, merged):
    frame["Country"] = frame["Country"].astype(str).str.strip()

# Canonicalizar con un listado de referencia que incluye ambos datasets
temp_df["Country_Match"] = temp_df["Country"].apply(lambda x: canonicalize_country(x, reference_countries))
merged["Country_Match"] = merged["Country"].apply(lambda x: canonicalize_country(x, reference_countries))

master = temp_df.merge(merged[["Country_Match", "GHG_Total", "GHG_Per_Capita", "GHG_Per_GDP"]], on="Country_Match", how="inner")
master = master.dropna(subset=["GHG_Total", "GHG_Per_Capita", "GHG_Per_GDP", "Temp_Anomaly_2010"])

# 4. Preparar matriz para PCA
features = ["Temp_Anomaly_2010", "GHG_Total", "GHG_Per_Capita", "GHG_Per_GDP", "Latitude_Abs"]
if "LULUCF_2010" in master.columns:
    features = ["Temp_Anomaly_2010", "GHG_Total", "GHG_Per_Capita", "GHG_Per_GDP", "Latitude_Abs"]
X = master[features].astype(float).values

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

pca = PCA(n_components=2)
coords = pca.fit_transform(X_scaled)

# 5. Guardar resultados del PCA y graficar biplot
master["PC1"] = coords[:, 0]
master["PC2"] = coords[:, 1]
master.to_csv(OUT_DIR / "pca_master_dataset.csv", index=False)

loadings = pca.components_.T * np.sqrt(pca.explained_variance_)
explained = pca.explained_variance_ratio_

coords_abs_max = max(float(np.max(np.abs(coords[:, 0]))), float(np.max(np.abs(coords[:, 1]))), 1.0)
loadings_abs_max = max(float(np.max(np.abs(loadings[:, 0]))), float(np.max(np.abs(loadings[:, 1]))), 1.0)
vector_scale = coords_abs_max / loadings_abs_max * 0.8

plt.figure(figsize=(11, 8))
plt.axhline(0, color="gray", linestyle="--", linewidth=0.8)
plt.axvline(0, color="gray", linestyle="--", linewidth=0.8)
plt.scatter(master["PC1"], master["PC2"], alpha=0.7, color="teal", edgecolors="k", s=80)

for _, row in master.iterrows():
    if row["Country_Match"] in {"China", "United States", "USA", "India", "Brazil", "Germany", "Japan", "United Kingdom", "France", "Russia", "Canada", "Australia"}:
        plt.text(row["PC1"] + 0.08, row["PC2"] + 0.08, row["Country_Match"], fontsize=10, fontweight="bold", bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.3))

for i, feature in enumerate(features):
    plt.arrow(0, 0, loadings[i, 0] * vector_scale, loadings[i, 1] * vector_scale, color="red", alpha=0.8, head_width=0.15, linewidth=1.4)
    plt.text(loadings[i, 0] * vector_scale * 1.1, loadings[i, 1] * vector_scale * 1.1, feature, color="darkred", fontweight="bold")

plt.xlabel(f"PC1 ({explained[0] * 100:.1f}% var. explicada)")
plt.ylabel(f"PC2 ({explained[1] * 100:.1f}% var. explicada)")
plt.title("Biplot PCA: emisiones, temperatura y latitud por país (2008-2012, MA12)")
plt.grid(True, linestyle=":", alpha=0.6)
plt.tight_layout()
plt.savefig(OUT_DIR / "pca_biplot.png", dpi=300)
plt.close()

print("Archivos preparados:")
for path in sorted(OUT_DIR.glob("*.csv")):
    print(f"- {path.name}")
print("- pca_biplot.png")
print("\nPCA completado con {0} países.".format(len(master)))
print("Varianza explicada por componente:")
print(pd.DataFrame({"Componente": ["PC1", "PC2"], "Varianza": explained}))
print("\nMatriz de cargas (loadings):")
print(pd.DataFrame(loadings, index=features, columns=["PC1", "PC2"]))
