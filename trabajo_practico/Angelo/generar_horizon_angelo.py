from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = (
    ROOT
    / "repositorio_tareas"
    / "tarea_1"
    / "Angelo"
    / "data"
    / "GlobalLandTemperaturesByCountry_cleaned.csv"
)
OUT_DIR = Path(__file__).resolve().parent
OUT_IMG = OUT_DIR / "horizon_anomalias_angelo.png"
OUT_CSV = OUT_DIR / "horizon_anomalias_angelo.csv"

BASELINE = (1951, 1980)
COUNTRIES = [
    "Mongolia",
    "Russia",
    "Canada",
    "Iran",
    "Chile",
    "Bangladesh",
    "Timor Leste",
]
DISPLAY_NAMES = {
    "Mongolia": "Mongolia",
    "Russia": "Rusia",
    "Canada": "Canada",
    "Iran": "Iran",
    "Chile": "Chile",
    "Bangladesh": "Bangladesh",
    "Timor Leste": "Timor Leste",
}


def prepare_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    df["dt"] = pd.to_datetime(df["dt"])
    df["year"] = df["dt"].dt.year
    df = df[df["Country"].isin(COUNTRIES)].dropna(subset=["AverageTemperature"])

    annual = (
        df.groupby(["Country", "year"], as_index=False)["AverageTemperature"]
        .mean()
        .rename(columns={"AverageTemperature": "annual_temp"})
    )

    baseline = annual[
        annual["year"].between(BASELINE[0], BASELINE[1])
    ].groupby("Country")["annual_temp"].mean()

    annual["baseline_temp"] = annual["Country"].map(baseline)
    annual = annual.dropna(subset=["baseline_temp"])
    annual["anomaly"] = annual["annual_temp"] - annual["baseline_temp"]
    annual["anomaly_smooth"] = (
        annual.sort_values(["Country", "year"])
        .groupby("Country")["anomaly"]
        .transform(lambda s: s.rolling(5, center=True, min_periods=1).mean())
    )
    return annual


def draw_horizon(df: pd.DataFrame) -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "axes.titleweight": "bold",
            "axes.labelcolor": "#252525",
            "xtick.color": "#4a4a4a",
            "ytick.color": "#252525",
        }
    )

    years = np.arange(int(df["year"].min()), int(df["year"].max()) + 1)
    band_width = 0.4
    row_height = 0.72
    colors_pos = ["#ffd166", "#f78c6b", "#e85d75", "#7b2cbf"]
    colors_neg = ["#9ecae1", "#6baed6", "#3182bd", "#08519c"]

    fig, ax = plt.subplots(figsize=(15, 8.5), facecolor="#fbfaf6")
    ax.set_facecolor("#fbfaf6")

    order = COUNTRIES
    for idx, country in enumerate(order):
        y0 = len(order) - idx - 1
        series = (
            df[df["Country"] == country]
            .set_index("year")["anomaly_smooth"]
            .reindex(years)
            .interpolate(limit_direction="both")
        )
        vals = series.to_numpy()

        ax.axhline(y0, color="#d8d3c8", linewidth=0.9, zorder=1)

        for band in range(4):
            low = band * band_width
            high = (band + 1) * band_width

            pos = np.clip(vals - low, 0, band_width) / band_width
            ax.fill_between(
                years,
                y0,
                y0 + pos * row_height,
                where=pos > 0,
                color=colors_pos[band],
                linewidth=0,
                alpha=0.95,
                zorder=2 + band,
            )

            neg = np.clip((-vals) - low, 0, band_width) / band_width
            ax.fill_between(
                years,
                y0,
                y0 - neg * row_height,
                where=neg > 0,
                color=colors_neg[band],
                linewidth=0,
                alpha=0.92,
                zorder=2 + band,
            )

        recent = df[(df["Country"] == country) & (df["year"].between(1993, 2013))]
        delta = recent["annual_temp"].mean() - df[
            (df["Country"] == country) & (df["year"].between(BASELINE[0], BASELINE[1]))
        ]["annual_temp"].mean()
        label = f"{DISPLAY_NAMES[country]}  {delta:+.2f} C"
        ax.text(
            years[0] - 4,
            y0,
            label,
            ha="right",
            va="center",
            fontsize=11,
            color="#252525",
            fontweight="bold" if country == "Chile" else "normal",
        )

    ax.axvspan(BASELINE[0], BASELINE[1], color="#777777", alpha=0.08, zorder=0)
    ax.text(
        sum(BASELINE) / 2,
        len(order) - 0.28,
        "linea base 1951-1980",
        ha="center",
        va="bottom",
        fontsize=9,
        color="#666666",
    )

    fig.suptitle(
        "La normalidad termica se rompe de forma desigual",
        fontsize=21,
        color="#1f1f1f",
        fontweight="bold",
        y=0.955,
    )
    ax.text(
        0.5,
        0.905,
        "Horizon graph de anomalias anuales suavizadas respecto de 1951-1980. "
        "Los colores calidos muestran anos sobre la normalidad; los azules, anos bajo ella.",
        transform=fig.transFigure,
        ha="center",
        va="top",
        fontsize=11,
        color="#4a4a4a",
    )

    legend = [
        Patch(facecolor=colors_neg[1], label="Bajo la normalidad"),
        Patch(facecolor=colors_pos[0], label="Sobre la normalidad leve"),
        Patch(facecolor=colors_pos[2], label="Sobre la normalidad alta"),
        Patch(facecolor=colors_pos[3], label="Sobre la normalidad extrema"),
    ]
    ax.legend(
        handles=legend,
        ncol=4,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.18),
        frameon=False,
        fontsize=10,
    )

    ax.set_xlim(years[0], years[-1])
    ax.set_ylim(-0.9, len(order) - 0.15)
    ax.set_yticks([])
    ax.set_xlabel("")
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color("#b7b1a4")
    ax.grid(axis="x", color="#e7e0d3", linewidth=0.8, alpha=0.85)

    source = (
        "Fuente: Berkeley Earth Surface Temperature Data (Kaggle), "
        "archivo GlobalLandTemperaturesByCountry_cleaned.csv. "
        "Procesamiento: Angelo Ibaceta."
    )
    ax.text(
        0,
        -0.27,
        source,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=8.5,
        color="#6a665e",
    )

    plt.tight_layout(rect=[0.08, 0.14, 0.98, 0.86])
    fig.savefig(OUT_IMG, dpi=300, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    df = prepare_data()
    df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    draw_horizon(df)

    summary = (
        df[df["year"].between(1993, 2013)]
        .groupby("Country")["anomaly"]
        .mean()
        .reindex(COUNTRIES)
    )
    print("[OK] Visualizacion generada:", OUT_IMG)
    print("[OK] Datos procesados:", OUT_CSV)
    print("\nAnomalia media 1993-2013 vs 1951-1980:")
    for country, value in summary.items():
        print(f"- {country}: {value:+.3f} C")


if __name__ == "__main__":
    main()
