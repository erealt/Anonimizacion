import numpy as np
import matplotlib.pyplot as plt
from pycanon import anonymity



# ═══════════════════════════════════════════════════════════════════════════════
# MÉTRICAS DE PRIVACIDAD (pycanon — IFCA-CSIC)
# ═══════════════════════════════════════════════════════════════════════════════

def calcular_metricas_pycanon(df, qi_cols, sa_cols):
    if not qi_cols or not sa_cols or len(df) == 0:
        return {}

    # sa_cols debe ser lista
    if isinstance(sa_cols, str):
        sa_cols = [sa_cols]

    resultado = {}

    try:
        resultado["k_anonymity"] = int(anonymity.k_anonymity(df, qi_cols))
    except Exception:
        resultado["k_anonymity"] = None

    try:
        alpha, k = anonymity.alpha_k_anonymity(df, qi_cols, sa_cols)
        resultado["alpha_k_anonymity"] = (float(alpha), int(k))
    except Exception:
        resultado["alpha_k_anonymity"] = None

    try:
        resultado["l_diversity"] = int(anonymity.l_diversity(df, qi_cols, sa_cols))
    except Exception:
        resultado["l_diversity"] = None

    try:
        resultado["entropy_l_diversity"] = int(anonymity.entropy_l_diversity(df, qi_cols, sa_cols))
    except Exception:
        resultado["entropy_l_diversity"] = None

    try:
        resultado["basic_beta_likeness"] = float(anonymity.basic_beta_likeness(df, qi_cols, sa_cols))
    except Exception:
        resultado["basic_beta_likeness"] = None

    try:
        resultado["enhanced_beta_likeness"] = float(anonymity.enhanced_beta_likeness(df, qi_cols, sa_cols))
    except Exception:
        resultado["enhanced_beta_likeness"] = None

    try:
        resultado["t_closeness"] = float(anonymity.t_closeness(df, qi_cols, sa_cols))
    except Exception:
        resultado["t_closeness"] = None

    try:
        resultado["delta_disclosure"] = float(anonymity.delta_disclosure(df, qi_cols, sa_cols))
    except Exception:
        resultado["delta_disclosure"] = None

    return resultado


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

