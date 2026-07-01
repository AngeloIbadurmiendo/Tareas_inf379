import re
import unicodedata
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


SCRIPT_DIR = Path(__file__).resolve().parent
TEMPERATURE_FILE = SCRIPT_DIR / "GlobalLandTemperaturesByMajorCity.csv"
GREENHOUSE_FILE = SCRIPT_DIR / "greenhouse.csv"
START_DATE = "1970-01-01"
END_DATE = "2013-12-31"
YEARS = list(range(1970, 2014))
YEAR_COLUMNS = [str(year) for year in YEARS]


def normalize_country(name: str) -> str:
    if pd.isna(name):
        return ""

    text = str(name).strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def canonical_country(name: str) -> str:
    alias_map = {
        "burma": "myanmar",
        "myanmar": "myanmar",
        "congo democratic republic of the": "democratic republic of the congo",
        "democratic republic of the congo": "democratic republic of the congo",
        "united states": "united states of america",
        "united states of america": "united states of america",
        "cote d ivoire": "ivory coast",
        "cote divoire": "ivory coast",
        "ivory coast": "ivory coast",
        "curacao": "curacao",
        "curaçao": "curacao",
        "reunion": "reunion",
        "réunion": "reunion",
        "sao tome and principe": "sao tome and principe",
        "sao tomé and príncipe": "sao tome and principe",
    }

    base_name = normalize_country(name)
    return alias_map.get(base_name, base_name)


def load_temperature_data() -> pd.DataFrame:
    df = pd.read_csv(TEMPERATURE_FILE)

    df["dt"] = pd.to_datetime(df["dt"], errors="coerce")
    df = df[df["dt"].notna()].copy()

    # Corregir valores faltantes por interpolación lineal por ciudad
    cols_to_fill = ["AverageTemperature", "AverageTemperatureUncertainty"]
    cols_to_fill = [col for col in cols_to_fill if col in df.columns]

    if cols_to_fill:
        df[cols_to_fill] = (
            df.groupby("City")[cols_to_fill]
            .apply(lambda s: s.interpolate(method="linear", limit_direction="both"))
            .reset_index(level=0, drop=True)
        )

    # Filtrar desde 1800 para evitar la alta incertidumbre histórica
    df = df[df["dt"].dt.year > 1800].copy()

    # Mantener el rango de años deseado para el análisis
    df = df[df["dt"].between(START_DATE, END_DATE)].copy()

    df = df.sort_values(["Country", "City", "dt"]).copy()
    df["year"] = df["dt"].dt.year.astype(int)
    df["Year"] = df["year"]

    # Promedio móvil de 12 meses por país y ciudad
    if "AverageTemperature" in df.columns:
        df["MA12"] = (
            df.groupby(["Country", "City"])["AverageTemperature"]
            .transform(lambda x: x.rolling(12, min_periods=1, center=True).mean())
        )

    return df


def load_greenhouse_data() -> pd.DataFrame:
    df = pd.read_csv(GREENHOUSE_FILE, delimiter=";")
    if "EDGAR Country Code" in df.columns:
        df = df.drop(columns=["EDGAR Country Code"])

    year_columns = [col for col in YEAR_COLUMNS if col in df.columns]
    for column in year_columns:
        df[column] = (
            df[column]
            .astype(str)
            .str.replace(",", ".", regex=False)
            .str.replace(" ", "", regex=False)
        )

    if year_columns:
        df[year_columns] = df[year_columns].apply(pd.to_numeric, errors="coerce")

    return df[["Country"] + year_columns].copy()


def add_country_normalization(df: pd.DataFrame, country_column: str) -> pd.DataFrame:
    normalized = df.copy()
    normalized["Country_normalized"] = normalized[country_column].apply(canonical_country)
    return normalized


def print_country_differences(temp_df: pd.DataFrame, greenhouse_df: pd.DataFrame) -> None:
    changes_t = (
        temp_df[["Country", "Country_normalized"]]
        .drop_duplicates()
        .query("Country != Country_normalized")
        .sort_values("Country")
    )
    changes_g = (
        greenhouse_df[["Country", "Country_normalized"]]
        .drop_duplicates()
        .query("Country != Country_normalized")
        .sort_values("Country")
    )

    print("Normalizaciones en csv_t (original -> normalizado):")
    print(changes_t.head(50).to_string(index=False))

    print("\nNormalizaciones en csv_g (original -> normalizado):")
    print(changes_g.head(50).to_string(index=False))

    countries_t = set(temp_df["Country_normalized"].dropna().unique())
    countries_g = set(greenhouse_df["Country_normalized"].dropna().unique())

    print("\nPaíses en csv_t que no aparecen en csv_g tras normalizar:")
    print(sorted(countries_t - countries_g))

    print("\nPaíses en csv_g que no aparecen en csv_t tras normalizar:")
    print(sorted(countries_g - countries_t))


def print_example_equivalences() -> None:
    examples = [
        ("Côte D'Ivoire", "Cote D'Ivoire"),
        ("Curaçao", "Curacao"),
        ("Réunion", "Reunion"),
        ("São Tomé and Príncipe", "Sao Tome and Principe"),
        ("Burma", "Myanmar"),
        ("Congo (Democratic Republic Of The)", "Democratic Republic of the Congo"),
        ("United States", "United States of America"),
    ]

    print("Ejemplos de equivalencias por normalización:")
    for left, right in examples:
        print(f"{left} <-> {right} => {canonical_country(left) == canonical_country(right)}")


def run_exploratory_pca(temperature_df: pd.DataFrame, greenhouse_df: pd.DataFrame, output_path: Path | None = None) -> pd.DataFrame:
    temp_agg = (
        temperature_df.groupby(["Country_normalized", "Year"], as_index=False)["MA12"]
        .mean()
        .rename(columns={"MA12": "Temperature"})
    )

    greenhouse_long = (
        greenhouse_df.melt(
            id_vars=["Country_normalized"],
            value_vars=YEAR_COLUMNS,
            var_name="Year",
            value_name="Greenhouse",
        )
        .assign(Year=lambda df: df["Year"].astype(int))
    )

    pca_df = temp_agg.merge(greenhouse_long, on=["Country_normalized", "Year"], how="inner")
    if pca_df.empty:
        print("No hay suficiente solape entre temperatura y emisiones para hacer PCA.")
        return pca_df

    pca_df = pca_df.sort_values(["Country_normalized", "Year"]).copy()
    pca_df["Year_centered"] = pca_df["Year"] - 1970

    pca_df["Temperature_anomaly"] = (
        pca_df.groupby("Country_normalized")["Temperature"]
        .transform(lambda x: x - x.iloc[0])
    )
    pca_df["Greenhouse_anomaly"] = (
        pca_df.groupby("Country_normalized")["Greenhouse"]
        .transform(lambda x: np.log1p(x) - np.log1p(x.iloc[0]))
    )

    features = ["Year_centered", "Temperature_anomaly", "Greenhouse_anomaly"]
    X = pca_df[features].dropna()

    if len(X) < 3:
        print("No hay suficientes observaciones para ejecutar PCA.")
        return pca_df

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    pca = PCA(n_components=2)
    components = pca.fit_transform(X_scaled)

    pca_df.loc[X.index, "PC1"] = components[:, 0]
    pca_df.loc[X.index, "PC2"] = components[:, 1]

    explained_variance = pca.explained_variance_ratio_
    print("\nPCA exploratorio (temperatura vs emisiones):")
    print(f"Varianza explicada por PC1: {explained_variance[0]:.2%}")
    print(f"Varianza explicada por PC2: {explained_variance[1]:.2%}")

    if output_path is None:
        output_path = SCRIPT_DIR / "pca_exploratorio.png"

    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(8, 5))
    scatter = ax.scatter(
        pca_df["PC1"],
        pca_df["PC2"],
        c=pca_df["Year"],
        s=40 + pca_df["Greenhouse_anomaly"].abs() * 20,
        cmap="viridis",
        alpha=0.8,
    )
    ax.set_title("PCA exploratorio: temperatura y emisiones por país-año")
    ax.set_xlabel("PC1")
    ax.set_ylabel("PC2")
    plt.colorbar(scatter, ax=ax, label="Año")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close(fig)

    print(f"Gráfico guardado en: {output_path}")
    return pca_df


def main() -> None:
    print(f"Rango de años en csv_t: {START_DATE[:4]}-{END_DATE[:4]}")

    temperature_df = load_temperature_data()
    greenhouse_df = load_greenhouse_data()

    temperature_df = add_country_normalization(temperature_df, "Country")
    greenhouse_df = add_country_normalization(greenhouse_df, "Country")

    print(f"Rango de años en csv_t: {temperature_df['Year'].min()}-{temperature_df['Year'].max()}")
    print(f"Años disponibles en csv_g: {min(YEARS)}-{max(YEARS)}")

    print_country_differences(temperature_df, greenhouse_df)
    print_example_equivalences()

    countries_t = set(temperature_df["Country_normalized"].dropna().unique())
    countries_g = set(greenhouse_df["Country_normalized"].dropna().unique())
    common_countries = sorted(countries_t & countries_g)

    temp_filtered = temperature_df[temperature_df["Country_normalized"].isin(common_countries)].copy()
    greenhouse_filtered = greenhouse_df[greenhouse_df["Country_normalized"].isin(common_countries)].copy()

    print(f"\nPaíses comunes tras normalización: {len(common_countries)}")
    print(f"Filas en csv_t después del filtrado: {len(temp_filtered)}")
    print(f"Filas en csv_g después del filtrado: {len(greenhouse_filtered)}")
    print(f"Ciudades únicas en csv_t (después de filtrar países): {temp_filtered['City'].nunique()}")

    temp_filtered = temp_filtered[["dt", "AverageTemperature", "City", "Country", "Country_normalized", "Year", "MA12"]].copy()
    greenhouse_filtered = greenhouse_filtered[["Country", "Country_normalized"] + YEAR_COLUMNS].copy()

    run_exploratory_pca(temp_filtered, greenhouse_filtered, SCRIPT_DIR / "pca_exploratorio.png")

    print("Listo para comparar ambos datasets con nombres de país unificados.")


if __name__ == "__main__":
    main()
