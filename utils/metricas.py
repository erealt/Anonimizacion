import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ═══════════════════════════════════════════════════════════════════════════════
# MÉTRICAS DE RIESGO DE RE-IDENTIFICACIÓN
# (basadas en tamaño de grupos de equivalencia)
# ═══════════════════════════════════════════════════════════════════════════════

def riesgo_maximo(df, qi_cols):
    """Riesgo del fiscal: 1 / tamaño del grupo más pequeño."""
    if not qi_cols or len(df) == 0:
        return 0.0
    return float((1 / df.groupby(qi_cols, dropna=False).size()).max())


def riesgo_medio(df, qi_cols):
    """Riesgo del periodista: media de 1/tamaño por registro."""
    if not qi_cols or len(df) == 0:
        return 0.0
    sizes = df.groupby(qi_cols, dropna=False)[df.columns[0]].transform("size")
    return float((1 / sizes).mean())


def tasa_unicidad(df, qi_cols):
    """Riesgo del marketer: % de registros en grupos de tamaño 1."""
    if not qi_cols or len(df) == 0:
        return 0.0
    sizes = df.groupby(qi_cols, dropna=False)[df.columns[0]].transform("size")
    return float((sizes == 1).sum() / len(df))


def k_value(df, qi_cols):
    """Valor mínimo de k real en el dataset."""
    if not qi_cols or len(df) == 0:
        return len(df)
    return int(df.groupby(qi_cols, dropna=False).size().min())


# ═══════════════════════════════════════════════════════════════════════════════
# UTILIDADES DE PRESENTACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

def riesgo_label(value):
    """Devuelve (etiqueta, clase_css) según el nivel de riesgo."""
    if value < 0.2:
        return "BAJO", "riesgo-bajo"
    elif value < 0.5:
        return "MEDIO", "riesgo-medio"
    else:
        return "ALTO", "riesgo-alto"


# ═══════════════════════════════════════════════════════════════════════════════
# F-SCORE CON NCP (utilidad ajustada por generalización)
# ═══════════════════════════════════════════════════════════════════════════════

def calcular_ncp(df_original, df_anonimizado, qi_cols):
    """
    NCP medio sobre los QIs numéricos generalizados a intervalos.

    Para cada columna numérica en qi_cols mide qué fracción del dominio
    original ocupa el intervalo generalizado de cada registro.
    Si la columna no fue generalizada (sigue siendo numérica), NCP = 0.
    """
    ncps = []

    for col in qi_cols:
        if col not in df_original.columns or col not in df_anonimizado.columns:
            continue
        if not pd.api.types.is_numeric_dtype(df_original[col]):
            continue

        dominio = df_original[col].dropna()
        if dominio.empty:
            continue

        amplitud_dominio = float(dominio.max() - dominio.min())
        if amplitud_dominio == 0:
            continue

        col_anon = df_anonimizado[col]

        if pd.api.types.is_object_dtype(col_anon):
            # Anjana generaliza a strings del tipo "[a, b)"
            amplitudes = []
            for val in col_anon:
                try:
                    partes = str(val).strip("[]()").split(",")
                    a, b = float(partes[0].strip()), float(partes[1].strip())
                    amplitudes.append(abs(b - a))
                except Exception:
                    amplitudes.append(amplitud_dominio)
            ncp_col = float(np.mean(amplitudes)) / amplitud_dominio
        else:
            # Columna numérica sin generalizar → NCP = 0
            ncp_col = 0.0

        ncps.append(min(ncp_col, 1.0))

    return float(np.mean(ncps)) if ncps else 0.0


def calcular_fscore_revisado(df_original, df_anonimizado, qi_cols):
    """
    F-Score revisado: Utilidad = Retención × (1 - NCP_medio).

    Devuelve un dict con todas las componentes para mostrarlas en la UI.
    """
    n_orig = len(df_original)
    n_anon = len(df_anonimizado)
    retencion = n_anon / n_orig if n_orig > 0 else 0.0

    ncp = calcular_ncp(df_original, df_anonimizado, qi_cols)
    utilidad = retencion * (1.0 - ncp)

    r_max = riesgo_maximo(df_anonimizado, qi_cols)
    privacidad = max(0.0, 1.0 - r_max)

    fscore = (
        2 * (privacidad * utilidad) / (privacidad + utilidad)
        if (privacidad + utilidad) > 0 else 0.0
    )

    return {
        "privacidad": privacidad,
        "retencion":  retencion,
        "ncp":        ncp,
        "utilidad":   utilidad,
        "fscore":     fscore,
        "riesgo_max": r_max,
    }


def generar_grafico_riesgos(r_maximo_orig, r_medio_orig, t_unicidad_orig,
                            r_maximo_anon, r_medio_anon, t_unicidad_anon):
    """Gráfico comparativo de métricas de riesgo: original vs anonimizado."""
    COLOR_BG      = "#ffffff"
    COLOR_ORIG    = "#991b1b"
    COLOR_ANON    = "#1a3a6b"
    COLOR_MUTED   = "#6b7280"
    COLOR_BORDER  = "#d1d5db"

    etiquetas = ["Riesgo máximo", "Riesgo medio", "Tasa de unicidad"]
    vals_orig = [r_maximo_orig, r_medio_orig, t_unicidad_orig]
    vals_anon = [r_maximo_anon, r_medio_anon, t_unicidad_anon]

    x = np.arange(len(etiquetas))
    w = 0.32

    fig, ax = plt.subplots(figsize=(8, 4))
    fig.patch.set_facecolor(COLOR_BG)
    ax.set_facecolor(COLOR_BG)

    b1 = ax.bar(x - w / 2, vals_orig, w, label="Original",     color=COLOR_ORIG, alpha=0.85)
    b2 = ax.bar(x + w / 2, vals_anon, w, label="Anonimizado",  color=COLOR_ANON, alpha=0.85)

    ax.set_xticks(x)
    ax.set_xticklabels(etiquetas, color=COLOR_MUTED, fontsize=10)
    ax.set_ylabel("Valor de la métrica", color=COLOR_MUTED, fontsize=9)
    ax.set_ylim(0, 1.15)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax.tick_params(colors=COLOR_MUTED)

    for s in ax.spines.values():
        s.set_edgecolor(COLOR_BORDER)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.legend(facecolor=COLOR_BG, edgecolor=COLOR_BORDER,
              labelcolor=COLOR_MUTED, fontsize=9, loc="upper right")

    for bar, color in zip(list(b1) + list(b2), [COLOR_ORIG] * 3 + [COLOR_ANON] * 3):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.02,
            f"{bar.get_height():.1%}",
            ha="center", va="bottom", color=color, fontsize=8, fontweight="600",
        )

    plt.tight_layout()
    return fig

