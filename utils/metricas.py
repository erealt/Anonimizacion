import numpy as np
import matplotlib.pyplot as plt


def riesgo_maximo(df, qi_cols):
    if not qi_cols:
        return 0.0
    return float((1 / df.groupby(qi_cols, dropna=False).size()).max())

def riesgo_medio(df,qi_cols):
    if not qi_cols:
        return 0.0
    return float((1/df.groupby(qi_cols,dropna=False).size()).mean())

def tasa_unicidad(df,qi_cols):
    if not qi_cols:
        return 0.0
    size = df.groupby(qi_cols,dropna=False).transform("size")
    return float((size==1).sum() / len(df))

def k_value(df,qi_cols):
    if not qi_cols:
        return len(df)
    return int(df.groupby(qi_cols, dropna=False).size().min())

def calcular_riesgo_global_armonico(r_fiscal, r_periodista, r_marketing):
    """
    Calcula la media armónica de los tres riesgos. 
    Se ignoran los riesgos muy cercanos a 0 para evitar divisiones por cero.
    """
    riesgos = [r for r in [r_fiscal, r_periodista, r_marketing] if r > 0.0001]
    
    if not riesgos:
        return 0.0
        
    suma_inversos = sum(1.0 / r for r in riesgos)
    return len(riesgos) / suma_inversos

def riesgo_label(value):
    if value < 0.2:
        return "BAJO", "riesgo-bajo"
    elif value < 0.5:
        return "MEDIO", "riego-medio"
    else:
        return "ALTO", "riesgo-alto"

def generar_grafico_riesgos(pr_orig, jr_orig, mr_orig, pr_anon, jr_anon, mr_anon):
    fig, ax = plt.subplots(figsize=(8, 3.5))
    fig.patch.set_facecolor("#0d0f14")
    ax.set_facecolor("#12151c")
    x = np.arange(3)
    w = 0.35
    b1 = ax.bar(x - w / 2, [pr_orig, jr_orig, mr_orig], w, label="Original", color="#ff4d4d", alpha=0.85)
    b2 = ax.bar(x + w / 2, [pr_anon, jr_anon, mr_anon], w, label="Anonimizado", color="#00e5a0", alpha=0.85)
    ax.set_xticks(x)
    ax.set_xticklabels(["Fiscal", "Periodístico", "Marketing"], color="#a0aec0", fontsize=10)
    ax.set_ylabel("Riesgo", color="#6b7280", fontsize=9)
    ax.set_ylim(0, 1.1)
    ax.tick_params(colors="#6b7280")
    for s in ax.spines.values():
        s.set_edgecolor("#1e2330")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(facecolor="#12151c", edgecolor="#1e2330", labelcolor="#a0aec0", fontsize=9)
    for bar, c in zip(list(b1) + list(b2), ["#ff4d4d"] * 3 + ["#00e5a0"] * 3):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.02,
            f"{bar.get_height():.1%}",
            ha="center", va="bottom", color=c, fontsize=8,
        )
    plt.tight_layout()
    return fig

   






