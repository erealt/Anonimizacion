import numpy as np
import matplotlib.pyplot as plt


def riesgo_maximo(df, qi_cols):
    if not qi_cols:
        return 0.0
    return float((1 / df.groupby(qi_cols, dropna=False).size()).max())

def riesgo_medio(df, qi_cols):
    """Journalist risk: riesgo medio de re-identificación promediado por REGISTRO.

    Cada individuo aporta 1/tamaño_de_su_grupo. Promediar por grupo (en lugar
    de por registro) infraestima el peso de los grupos grandes y sobrestima
    el de los pequeños, dando un valor distorsionado.
    """
    if not qi_cols:
        return 0.0
    sizes = df.groupby(qi_cols, dropna=False)[df.columns[0]].transform("size")
    return float((1 / sizes).mean())

def tasa_unicidad(df,qi_cols):
    if not qi_cols:
        return 0.0
    size = df.groupby(qi_cols,dropna=False).transform("size")
    return float((size==1).sum() / len(df))

def k_value(df,qi_cols):
    if not qi_cols:
        return len(df)
    return int(df.groupby(qi_cols, dropna=False).size().min())

def riesgo_label(value):
    if value < 0.2:
        return "BAJO", "riesgo-bajo"
    elif value < 0.5:
        return "MEDIO", "riesgo-medio"
    else:
        return "ALTO", "riesgo-alto"

# Reservado para tab 5 - Comparativa
def generar_grafico_riesgos(r_maximo_orig, r_medio_orig, t_unicidad_orig,
                            r_maximo_anon, r_medio_anon, t_unicidad_anon):
    """Gráfico de barras agrupadas original vs anonimizado para las tres métricas principales.

    IMPORTANTE: el llamador debe hacer ``plt.close(fig)`` tras pintarla con
    ``st.pyplot(fig)`` para evitar fugas de memoria al re-ejecutarse el script.
    """
    COLOR_BG      = "#ffffff"
    COLOR_ORIG    = "#991b1b"   # rojo institucional — datos originales (más riesgo)
    COLOR_ANON    = "#1a3a6b"   # azul institucional  — datos anonimizados
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

   






