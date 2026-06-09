import re
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
from utils.metricas import (
    riesgo_maximo, riesgo_medio, tasa_unicidad, k_value,
    riesgo_label, generar_grafico_riesgos,
)

# ── Paleta institucional ──────────────────────────────────────────────────────
COLOR_TEXT    = "#1a2340"
COLOR_MUTED   = "#6b7280"
COLOR_CARD    = "#ffffff"
COLOR_BORDER  = "#d1d5db"
COLOR_PRIMARY = "#1a3a6b"
COLOR_LOW     = "#166534"
COLOR_LOW_BG  = "#dcfce7"
COLOR_LOW_BD  = "#86efac"
COLOR_MED     = "#854d0e"
COLOR_MED_BG  = "#fef9c3"
COLOR_MED_BD  = "#fde047"
COLOR_HIGH    = "#991b1b"
COLOR_HIGH_BG = "#fee2e2"
COLOR_HIGH_BD = "#fca5a5"


# ═════════════════════════════════════════════════════════════════════════════
# NCP — PÉRDIDA DE INFORMACIÓN
# ═════════════════════════════════════════════════════════════════════════════

_INTERVAL_RE = re.compile(r"^\[(-?\d+\.?\d*),\s*(-?\d+\.?\d*)\)")

def _calcular_il(df_orig, df_anon, qi_cols):
    """
    Normalized Certainty Penalty (NCP) — Sweeney & Samarati.

    NCP_col = anchura_intervalo_generalizado / (max_orig - min_orig)

    · Numéricas : anjana escribe intervalos '[a, b)';
                  NCP = (b - a) / (max - min) del dataset original.
    · Categóricas: '*' → 1.0  |  'XXX*' (truncado) → 0.5  |  sin cambio → 0.0.

    Se promedia sobre todos los registros y columnas QI. Devuelve float en [0, 1].
    """
    il_cols = []
    for col in qi_cols:
        if col not in df_anon.columns or col not in df_orig.columns:
            continue

        if pd.api.types.is_numeric_dtype(df_orig[col]):
            rango = float(df_orig[col].max() - df_orig[col].min())
            if rango == 0:
                il_cols.append(0.0)
                continue
            vals = []
            for v in df_anon[col]:
                m = _INTERVAL_RE.match(str(v))
                if m:
                    vals.append(min((float(m.group(2)) - float(m.group(1))) / rango, 1.0))
                elif str(v) == "*":
                    vals.append(1.0)
                else:
                    vals.append(0.0)
            il_cols.append(float(np.mean(vals)) if vals else 0.0)
        else:
            vals = []
            for v in df_anon[col]:
                s = str(v)
                if s == "*":
                    vals.append(1.0)
                elif s.endswith("*"):
                    vals.append(0.5)
                else:
                    vals.append(0.0)
            il_cols.append(float(np.mean(vals)) if vals else 0.0)

    return float(np.mean(il_cols)) if il_cols else 0.0


# ═════════════════════════════════════════════════════════════════════════════
# CURVAS DE TRADE-OFF  (cached — no se recomputan en cada rerun de Streamlit)
# ═════════════════════════════════════════════════════════════════════════════

@st.cache_data(show_spinner=False)
def _curva_k(df, qi_cols_tuple, supp_level=30):
    """Métricas para k = 2..15 con los mismos QI y nivel de supresión."""
    from utils.anonimizacion import k_anonimicidad
    from utils.metricas import riesgo_maximo as _rmax

    qi_cols = list(qi_cols_tuple)
    n_orig  = len(df)
    filas   = []
    for k in range(2, 16):
        try:
            df_anon = k_anonimicidad(df, qi_cols, k=k, supp_level=supp_level)
            r    = _rmax(df_anon, qi_cols)
            ret  = len(df_anon) / n_orig if n_orig > 0 else 0.0
            priv = max(0.0, 1.0 - r)
            fs   = 2 * priv * ret / (priv + ret) if (priv + ret) > 0 else 0.0
            il   = _calcular_il(df, df_anon, qi_cols)
            filas.append({"k": k, "riesgo": r, "retencion": ret,
                          "fscore": fs, "suprimidos": n_orig - len(df_anon), "il": il})
        except Exception:
            filas.append({"k": k, "riesgo": None, "retencion": None,
                          "fscore": None, "suprimidos": None, "il": None})
    return filas


@st.cache_data(show_spinner=False)
def _curva_ldiv(df, qi_cols_tuple, col_sensible, l_value, supp_level=30):
    """Métricas para k = 2..15 con l fijo."""
    from utils.anonimizacion import l_diversidad
    from utils.metricas import riesgo_maximo as _rmax

    qi_cols = list(qi_cols_tuple)
    n_orig  = len(df)
    filas   = []
    for k in range(2, 16):
        try:
            df_anon = l_diversidad(df, qi_cols, col_sensible,
                                   k=k, l=l_value, supp_level=supp_level)
            r    = _rmax(df_anon, qi_cols)
            ret  = len(df_anon) / n_orig if n_orig > 0 else 0.0
            priv = max(0.0, 1.0 - r)
            fs   = 2 * priv * ret / (priv + ret) if (priv + ret) > 0 else 0.0
            il   = _calcular_il(df, df_anon, qi_cols)
            filas.append({"k": k, "riesgo": r, "retencion": ret,
                          "fscore": fs, "suprimidos": n_orig - len(df_anon), "il": il})
        except Exception:
            filas.append({"k": k, "riesgo": None, "retencion": None,
                          "fscore": None, "suprimidos": None, "il": None})
    return filas


@st.cache_data(show_spinner=False)
def _curva_dp(df, sensibilidad=1.0):
    """Métricas para ε ∈ {0.1, 0.3, 0.5, 1, 2, 5, 10}."""
    from utils.anonimizacion import privacidad_diferencial

    epsilons = [0.1, 0.3, 0.5, 1.0, 2.0, 5.0, 10.0]
    cols_num = df.select_dtypes(include=[np.number]).columns.tolist()
    filas    = []
    for eps in epsilons:
        try:
            df_anon = privacidad_diferencial(df, eps, sensibilidad)
            if cols_num:
                mae   = float(np.mean([np.abs(df[c] - df_anon[c]).mean() for c in cols_num]))
                rango = float(np.mean([df[c].max() - df[c].min() for c in cols_num]))
                util  = max(0.0, 1.0 - mae / rango) if rango > 0 else 0.0
            else:
                mae, util = 0.0, 1.0
            priv = 1.0 / (1.0 + eps)
            fs   = 2 * priv * util / (priv + util) if (priv + util) > 0 else 0.0
            filas.append({"epsilon": eps, "privacidad": priv,
                          "utilidad": util, "fscore": fs, "mae": mae})
        except Exception:
            filas.append({"epsilon": eps, "privacidad": None,
                          "utilidad": None, "fscore": None, "mae": None})
    return filas


# ═════════════════════════════════════════════════════════════════════════════
# GRÁFICOS
# ═════════════════════════════════════════════════════════════════════════════

def _fig_curva_k(filas, k_actual):
    filas_ok = [f for f in filas if f["fscore"] is not None]
    if not filas_ok:
        return None

    ks     = [f["k"]          for f in filas_ok]
    riesgo = [f["riesgo"]     for f in filas_ok]
    ret    = [f["retencion"]  for f in filas_ok]
    fs     = [f["fscore"]     for f in filas_ok]
    il     = [f.get("il") or 0 for f in filas_ok]
    k_opt  = filas_ok[int(np.argmax(fs))]["k"]

    fig, ax = plt.subplots(figsize=(9, 4.5))
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#ffffff")

    ax.plot(ks, riesgo, color="#991b1b", linewidth=1.8, linestyle="--",
            marker="o", markersize=4, label="Riesgo máximo")
    ax.plot(ks, ret,    color="#1a3a6b", linewidth=1.8, linestyle="--",
            marker="o", markersize=4, label="Retención")
    ax.plot(ks, il,     color="#d97706", linewidth=1.8, linestyle=":",
            marker="s", markersize=4, label="Pérd. información")
    ax.plot(ks, fs,     color="#166534", linewidth=2.5,
            marker="o", markersize=5,  label="F-Score")

    if k_actual in ks:
        ax.axvline(k_actual, color="#6b7280", linewidth=1.2, linestyle=":",
                   label=f"k actual ({k_actual})")
        idx_act = ks.index(k_actual)
        ax.annotate(
            f"{fs[idx_act]:.0%}",
            xy=(k_actual, fs[idx_act]),
            xytext=(k_actual + 0.35, fs[idx_act] + 0.05),
            fontsize=8, color="#166534", fontweight="bold",
        )

    if k_opt != k_actual:
        ax.axvline(k_opt, color="#166534", linewidth=1.2, linestyle=":",
                   label=f"k óptimo ({k_opt})")

    ax.set_xlabel("Valor de k", color="#6b7280", fontsize=10)
    ax.set_ylabel("Valor de la métrica", color="#6b7280", fontsize=10)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=1, decimals=0))
    ax.set_xticks(ks)
    ax.set_ylim(-0.05, 1.15)
    ax.tick_params(colors="#6b7280", labelsize=9)
    ax.grid(True, alpha=0.3, color="#d1d5db")
    for spine in ax.spines.values():
        spine.set_edgecolor("#d1d5db")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(fontsize=9, framealpha=0.9, facecolor="#ffffff",
              edgecolor="#d1d5db", labelcolor="#374151", loc="upper right")
    plt.tight_layout()
    return fig


def _fig_curva_dp(filas, eps_actual):
    filas_ok = [f for f in filas if f["fscore"] is not None]
    if not filas_ok:
        return None

    eps  = [f["epsilon"]   for f in filas_ok]
    priv = [f["privacidad"] for f in filas_ok]
    util = [f["utilidad"]   for f in filas_ok]
    fs   = [f["fscore"]     for f in filas_ok]

    fig, ax = plt.subplots(figsize=(9, 4.5))
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#ffffff")

    ax.plot(eps, priv, color="#991b1b", linewidth=1.8, linestyle="--",
            marker="o", markersize=4, label="Score privacidad (1/(1+ε))")
    ax.plot(eps, util, color="#1a3a6b", linewidth=1.8, linestyle="--",
            marker="o", markersize=4, label="Utilidad (1 − MAE/rango)")
    ax.plot(eps, fs,   color="#166534", linewidth=2.5,
            marker="o", markersize=5,  label="F-Score")

    eps_vals = [f["epsilon"] for f in filas_ok]
    if any(abs(e - eps_actual) < 1e-6 for e in eps_vals):
        ax.axvline(eps_actual, color="#6b7280", linewidth=1.2, linestyle=":",
                   label=f"ε actual ({eps_actual:.2f})")

    ax.set_xlabel("Epsilon (ε)", color="#6b7280", fontsize=10)
    ax.set_ylabel("Valor de la métrica", color="#6b7280", fontsize=10)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=1, decimals=0))
    ax.set_xticks(eps)
    ax.set_xticklabels([str(e) for e in eps], fontsize=8)
    ax.set_ylim(-0.05, 1.15)
    ax.tick_params(colors="#6b7280", labelsize=9)
    ax.grid(True, alpha=0.3, color="#d1d5db")
    for spine in ax.spines.values():
        spine.set_edgecolor("#d1d5db")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(fontsize=9, framealpha=0.9, facecolor="#ffffff",
              edgecolor="#d1d5db", labelcolor="#374151", loc="upper right")
    plt.tight_layout()
    return fig


# ═════════════════════════════════════════════════════════════════════════════
# TABLAS HTML
# ═════════════════════════════════════════════════════════════════════════════

def _tabla_k_html(filas, k_actual):
    filas_ok = [f for f in filas if f["fscore"] is not None]
    fs_max   = max((f["fscore"] for f in filas_ok), default=0)
    # Solo el primer k que alcanza el máximo (el menos restrictivo suficiente)
    k_opt    = next((f["k"] for f in filas_ok if f["fscore"] == fs_max), None)

    cabecera = f"""
    <div style='background:{COLOR_CARD};border:1px solid {COLOR_BORDER};border-radius:6px;
                overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.06);'>
    <table style='width:100%;border-collapse:collapse;font-size:0.875rem;'>
        <thead>
            <tr style='background:#f8f9fb;'>
                <th style='padding:0.6rem 1rem;text-align:left;color:{COLOR_MUTED};font-size:0.72rem;
                           text-transform:uppercase;border-bottom:2px solid {COLOR_BORDER};'>k</th>
                <th style='padding:0.6rem 1rem;text-align:center;color:{COLOR_MUTED};font-size:0.72rem;
                           text-transform:uppercase;border-bottom:2px solid {COLOR_BORDER};'>Riesgo máx.</th>
                <th style='padding:0.6rem 1rem;text-align:center;color:{COLOR_MUTED};font-size:0.72rem;
                           text-transform:uppercase;border-bottom:2px solid {COLOR_BORDER};'>Retención</th>
                <th style='padding:0.6rem 1rem;text-align:center;color:{COLOR_MUTED};font-size:0.72rem;
                           text-transform:uppercase;border-bottom:2px solid {COLOR_BORDER};'>Suprimidos</th>
                <th style='padding:0.6rem 1rem;text-align:center;color:{COLOR_MUTED};font-size:0.72rem;
                           text-transform:uppercase;border-bottom:2px solid {COLOR_BORDER};'>Pérd. info.</th>
                <th style='padding:0.6rem 1rem;text-align:center;color:{COLOR_MUTED};font-size:0.72rem;
                           text-transform:uppercase;border-bottom:2px solid {COLOR_BORDER};'>F-Score</th>
            </tr>
        </thead>
        <tbody>"""

    filas_html = ""
    for f in filas:
        es_actual = (f["k"] == k_actual)
        es_optimo = (f["k"] == k_opt)

        if f["fscore"] is None:
            filas_html += f"""
            <tr style='border-bottom:1px solid {COLOR_BORDER};opacity:0.45;'>
                <td style='padding:0.5rem 1rem;color:{COLOR_TEXT};'>k = {f["k"]}</td>
                <td colspan='5' style='padding:0.5rem 1rem;text-align:center;
                   color:{COLOR_MUTED};font-size:0.8rem;'>
                   No alcanzable con este dataset</td>
            </tr>"""
            continue

        fs = f["fscore"]
        if fs >= 0.80:
            fs_bg, fs_col = COLOR_LOW_BG, COLOR_LOW
        elif fs >= 0.50:
            fs_bg, fs_col = COLOR_MED_BG, COLOR_MED
        else:
            fs_bg, fs_col = COLOR_HIGH_BG, COLOR_HIGH

        row_bg = "#eef2fb" if es_actual else COLOR_CARD
        font_w = "700"     if es_actual else "400"

        badges = ""
        if es_actual:
            badges += (f"&nbsp;<span style='background:{COLOR_PRIMARY};color:#fff;"
                       f"font-size:0.62rem;padding:0.1rem 0.4rem;border-radius:3px;"
                       f"font-weight:600;'>actual</span>")
        if es_optimo and not es_actual:
            badges += (f"&nbsp;<span style='background:{COLOR_LOW};color:#fff;"
                       f"font-size:0.62rem;padding:0.1rem 0.4rem;border-radius:3px;"
                       f"font-weight:600;'>óptimo</span>")

        filas_html += f"""
        <tr style='background:{row_bg};border-bottom:1px solid {COLOR_BORDER};'>
            <td style='padding:0.5rem 1rem;font-weight:{font_w};
                       color:{COLOR_PRIMARY if es_actual else COLOR_TEXT};'>
                k = {f["k"]}{badges}
            </td>
            <td style='padding:0.5rem 1rem;text-align:center;
                       color:{COLOR_HIGH};font-weight:{font_w};'>
                {f["riesgo"]:.1%}
            </td>
            <td style='padding:0.5rem 1rem;text-align:center;
                       color:{COLOR_PRIMARY};font-weight:{font_w};'>
                {f["retencion"]:.1%}
            </td>
            <td style='padding:0.5rem 1rem;text-align:center;color:{COLOR_MUTED};'>
                {f["suprimidos"]}
            </td>
            <td style='padding:0.5rem 1rem;text-align:center;'>
                <span style='color:{"#854d0e" if (f["il"] or 0) > 0.4 else ("#166534" if (f["il"] or 0) < 0.2 else "#1a3a6b")};
                             font-weight:600;font-size:0.85rem;'>
                    {f["il"]:.1%}
                </span>
            </td>
            <td style='padding:0.5rem 1rem;text-align:center;'>
                <span style='background:{fs_bg};color:{fs_col};padding:0.2rem 0.6rem;
                             border-radius:4px;font-weight:700;font-size:0.85rem;'>
                    {fs:.1%}
                </span>
            </td>
        </tr>"""

    return cabecera + filas_html + "</tbody></table></div>"


def _tabla_dp_html(filas, eps_actual):
    filas_ok = [f for f in filas if f["fscore"] is not None]
    fs_max   = max((f["fscore"] for f in filas_ok), default=0)
    # Solo el primer epsilon que alcanza el máximo
    eps_opt  = next((f["epsilon"] for f in filas_ok if f["fscore"] == fs_max), None)

    cabecera = f"""
    <div style='background:{COLOR_CARD};border:1px solid {COLOR_BORDER};border-radius:6px;
                overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.06);'>
    <table style='width:100%;border-collapse:collapse;font-size:0.875rem;'>
        <thead>
            <tr style='background:#f8f9fb;'>
                <th style='padding:0.6rem 1rem;text-align:left;color:{COLOR_MUTED};font-size:0.72rem;
                           text-transform:uppercase;border-bottom:2px solid {COLOR_BORDER};'>ε (epsilon)</th>
                <th style='padding:0.6rem 1rem;text-align:center;color:{COLOR_MUTED};font-size:0.72rem;
                           text-transform:uppercase;border-bottom:2px solid {COLOR_BORDER};'>Privacidad</th>
                <th style='padding:0.6rem 1rem;text-align:center;color:{COLOR_MUTED};font-size:0.72rem;
                           text-transform:uppercase;border-bottom:2px solid {COLOR_BORDER};'>Utilidad</th>
                <th style='padding:0.6rem 1rem;text-align:center;color:{COLOR_MUTED};font-size:0.72rem;
                           text-transform:uppercase;border-bottom:2px solid {COLOR_BORDER};'>MAE medio</th>
                <th style='padding:0.6rem 1rem;text-align:center;color:{COLOR_MUTED};font-size:0.72rem;
                           text-transform:uppercase;border-bottom:2px solid {COLOR_BORDER};'>F-Score</th>
            </tr>
        </thead>
        <tbody>"""

    filas_html = ""
    for f in filas:
        es_actual = any(abs(f["epsilon"] - eps_actual) < 1e-6 for _ in [0])
        es_optimo = (f["epsilon"] == eps_opt)

        if f["fscore"] is None:
            filas_html += f"""
            <tr style='border-bottom:1px solid {COLOR_BORDER};opacity:0.45;'>
                <td style='padding:0.5rem 1rem;'>ε = {f["epsilon"]}</td>
                <td colspan='4' style='padding:0.5rem 1rem;text-align:center;
                   color:{COLOR_MUTED};font-size:0.8rem;'>Error de cálculo</td>
            </tr>"""
            continue

        fs = f["fscore"]
        if fs >= 0.80:
            fs_bg, fs_col = COLOR_LOW_BG, COLOR_LOW
        elif fs >= 0.50:
            fs_bg, fs_col = COLOR_MED_BG, COLOR_MED
        else:
            fs_bg, fs_col = COLOR_HIGH_BG, COLOR_HIGH

        priv = f["privacidad"]
        priv_col = COLOR_LOW if priv >= 0.67 else (COLOR_MED if priv >= 0.33 else COLOR_HIGH)

        row_bg = "#eef2fb" if es_actual else COLOR_CARD
        font_w = "700"     if es_actual else "400"

        badges = ""
        if es_actual:
            badges += (f"&nbsp;<span style='background:{COLOR_PRIMARY};color:#fff;"
                       f"font-size:0.62rem;padding:0.1rem 0.4rem;border-radius:3px;"
                       f"font-weight:600;'>actual</span>")
        if es_optimo and not es_actual:
            badges += (f"&nbsp;<span style='background:{COLOR_LOW};color:#fff;"
                       f"font-size:0.62rem;padding:0.1rem 0.4rem;border-radius:3px;"
                       f"font-weight:600;'>óptimo</span>")

        filas_html += f"""
        <tr style='background:{row_bg};border-bottom:1px solid {COLOR_BORDER};'>
            <td style='padding:0.5rem 1rem;font-weight:{font_w};
                       color:{COLOR_PRIMARY if es_actual else COLOR_TEXT};'>
                ε = {f["epsilon"]}{badges}
            </td>
            <td style='padding:0.5rem 1rem;text-align:center;
                       color:{priv_col};font-weight:{font_w};'>
                {priv:.1%}
            </td>
            <td style='padding:0.5rem 1rem;text-align:center;
                       color:{COLOR_PRIMARY};font-weight:{font_w};'>
                {f["utilidad"]:.1%}
            </td>
            <td style='padding:0.5rem 1rem;text-align:center;color:{COLOR_MUTED};'>
                {f["mae"]:.3f}
            </td>
            <td style='padding:0.5rem 1rem;text-align:center;'>
                <span style='background:{fs_bg};color:{fs_col};padding:0.2rem 0.6rem;
                             border-radius:4px;font-weight:700;font-size:0.85rem;'>
                    {fs:.1%}
                </span>
            </td>
        </tr>"""

    return cabecera + filas_html + "</tbody></table></div>"


# ═════════════════════════════════════════════════════════════════════════════
# RENDER PRINCIPAL
# ═════════════════════════════════════════════════════════════════════════════

def render():
    df               = st.session_state.get("df")
    df_anon          = st.session_state.get("df_anonimizado")
    df_base          = st.session_state.get("df_base", df)
    columnas_qi      = st.session_state.get("columnas_qi", [])
    tecnica          = st.session_state.get("tecnica_usada", "")
    params           = st.session_state.get("params_anon", {})
    attrs            = st.session_state.get("attrs_anon", {})
    col_sensible     = st.session_state.get("columna_sensible", "")

    if df is None or df_anon is None:
        st.info("Primero importa datos y aplica una tecnica de anonimizacion.")
        return

    registros_orig = len(df)
    registros_anon = len(df_anon)
    suprimidos     = registros_orig - registros_anon
    retencion      = registros_anon / registros_orig if registros_orig > 0 else 0

    # Parámetros aplicados
    if tecnica == "K-Anonimidad":
        params_text = f"k = {params.get('k', '?')}"
    elif tecnica == "L-Diversidad":
        params_text = f"k = {params.get('k', '?')}, l = {params.get('l', '?')}"
    elif tecnica == "Privacidad Diferencial":
        params_text = f"ε = {attrs.get('epsilon_total', '?')}"
    else:
        params_text = ""

    st.markdown(
        f"<div class='section-header'>Comparativa - Original vs {tecnica}</div>",
        unsafe_allow_html=True,
    )

    st.markdown(f"""
    <div style='background:#eef2fb;border:1px solid #b8c9e8;border-radius:6px;
                padding:1.2rem 1.5rem;margin-bottom:1.5rem;'>
        <div style='display:flex;align-items:center;gap:1rem;'>
            <div style='font-size:1.3rem;'>📊</div>
            <div>
                <strong style='color:{COLOR_PRIMARY};font-size:0.95rem;'>
                    {tecnica} ({params_text})
                </strong>
                <p style='margin:0.3rem 0 0;color:{COLOR_TEXT};font-size:0.88rem;'>
                    {registros_orig} → {registros_anon} registros
                    ({suprimidos} suprimidos · retención {retencion:.1%})
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Métricas puntuales (técnicas basadas en QI) ──────────────────────────
    if columnas_qi and tecnica != "Privacidad Diferencial":
        st.markdown("### Métricas de riesgo: antes y después")

        r_max_orig  = riesgo_maximo(df, columnas_qi)
        r_med_orig  = riesgo_medio(df, columnas_qi)
        t_unic_orig = tasa_unicidad(df, columnas_qi)
        k_orig      = k_value(df, columnas_qi)

        r_max_anon  = riesgo_maximo(df_anon, columnas_qi)
        r_med_anon  = riesgo_medio(df_anon, columnas_qi)
        t_unic_anon = tasa_unicidad(df_anon, columnas_qi)
        k_anon      = k_value(df_anon, columnas_qi)

        def _fila(nombre, v_orig, v_anon, es_pct=True):
            if es_pct:
                s_orig, s_anon = f"{v_orig:.1%}", f"{v_anon:.1%}"
                mejora = v_orig - v_anon
                if mejora > 0.01:
                    icono = f"<span style='color:{COLOR_LOW};font-weight:600;'>▼ {mejora:.1%}</span>"
                elif mejora < -0.01:
                    icono = f"<span style='color:{COLOR_HIGH};font-weight:600;'>▲ {abs(mejora):.1%}</span>"
                else:
                    icono = f"<span style='color:{COLOR_MUTED};'>Sin cambio</span>"
            else:
                s_orig, s_anon = str(v_orig), str(v_anon)
                mejora = v_anon - v_orig
                if mejora > 0:
                    icono = f"<span style='color:{COLOR_LOW};font-weight:600;'>+{int(mejora)}</span>"
                elif mejora < 0:
                    icono = f"<span style='color:{COLOR_HIGH};font-weight:600;'>{int(mejora)}</span>"
                else:
                    icono = f"<span style='color:{COLOR_MUTED};'>Sin cambio</span>"

            return f"""
            <tr>
                <td style='padding:0.7rem 1rem;font-weight:500;color:{COLOR_TEXT};font-size:0.9rem;
                           border-bottom:1px solid {COLOR_BORDER};'>{nombre}</td>
                <td style='padding:0.7rem 1rem;text-align:center;color:{COLOR_HIGH};font-weight:600;
                           font-size:0.95rem;border-bottom:1px solid {COLOR_BORDER};'>{s_orig}</td>
                <td style='padding:0.7rem 1rem;text-align:center;color:{COLOR_PRIMARY};font-weight:700;
                           font-size:0.95rem;border-bottom:1px solid {COLOR_BORDER};'>{s_anon}</td>
                <td style='padding:0.7rem 1rem;text-align:center;font-size:0.85rem;
                           border-bottom:1px solid {COLOR_BORDER};'>{icono}</td>
            </tr>"""

        filas_html = (
            _fila("Riesgo máximo (fiscal)",       r_max_orig,  r_max_anon)
            + _fila("Riesgo medio (periodista)",  r_med_orig,  r_med_anon)
            + _fila("Tasa de unicidad (marketer)",t_unic_orig, t_unic_anon)
            + _fila("K-anonimidad (k mínimo)",    k_orig,      k_anon, es_pct=False)
        )

        st.markdown(f"""
        <div style='background:{COLOR_CARD};border:1px solid {COLOR_BORDER};border-radius:6px;
                    overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.06);margin-bottom:1.5rem;'>
            <table style='width:100%;border-collapse:collapse;'>
                <thead>
                    <tr style='background:#f8f9fb;'>
                        <th style='padding:0.7rem 1rem;text-align:left;color:{COLOR_MUTED};font-size:0.75rem;
                                   text-transform:uppercase;border-bottom:2px solid {COLOR_BORDER};'>Métrica</th>
                        <th style='padding:0.7rem 1rem;text-align:center;color:{COLOR_HIGH};font-size:0.75rem;
                                   text-transform:uppercase;border-bottom:2px solid {COLOR_BORDER};'>Original</th>
                        <th style='padding:0.7rem 1rem;text-align:center;color:{COLOR_PRIMARY};font-size:0.75rem;
                                   text-transform:uppercase;border-bottom:2px solid {COLOR_BORDER};'>Anonimizado</th>
                        <th style='padding:0.7rem 1rem;text-align:center;color:{COLOR_MUTED};font-size:0.75rem;
                                   text-transform:uppercase;border-bottom:2px solid {COLOR_BORDER};'>Cambio</th>
                    </tr>
                </thead>
                <tbody>{filas_html}</tbody>
            </table>
        </div>
        """, unsafe_allow_html=True)

        # Gráfico comparativo puntual
        st.markdown("### Gráfico comparativo")
        fig_bar = generar_grafico_riesgos(
            r_max_orig, r_med_orig, t_unic_orig,
            r_max_anon, r_med_anon, t_unic_anon,
        )
        st.pyplot(fig_bar)
        plt.close(fig_bar)

        # F-Score puntual
        st.markdown("---")
        privacidad_anon = max(0.0, 1.0 - r_max_anon)
        fscore = (2 * privacidad_anon * retencion / (privacidad_anon + retencion)
                  if (privacidad_anon + retencion) > 0 else 0.0)

        if fscore >= 0.80:
            bg_c, bd_c, tx_c = COLOR_LOW_BG, COLOR_LOW_BD, COLOR_LOW
            nivel = "ÓPTIMO"
        elif fscore >= 0.50:
            bg_c, bd_c, tx_c = COLOR_MED_BG, COLOR_MED_BD, COLOR_MED
            nivel = "ACEPTABLE"
        else:
            bg_c, bd_c, tx_c = COLOR_HIGH_BG, COLOR_HIGH_BD, COLOR_HIGH
            nivel = "INSUFICIENTE"

        st.markdown(f"""
        <div style='background:{bg_c};border:1px solid {bd_c};border-radius:6px;
                    padding:1.2rem 1.5rem;'>
            <strong style='color:{tx_c};font-size:1rem;'>Balance Privacidad / Utilidad: {nivel}</strong>
            <p style='margin:0.4rem 0 0;color:{COLOR_TEXT};font-size:0.88rem;'>
                F-Score: <strong style='color:{tx_c}'>{fscore:.1%}</strong>
                (privacidad {privacidad_anon:.1%} × retención {retencion:.1%})
            </p>
        </div>
        """, unsafe_allow_html=True)

    elif tecnica == "Privacidad Diferencial":
        eps     = attrs.get("epsilon_total", 0)
        n_cols  = attrs.get("n_columnas_ruido", 0)

        if eps <= 0.5:
            nivel_priv, color_priv = "MUY ALTA", COLOR_LOW
            desc_priv = "Mucho ruido añadido. Alta protección, pero los valores pueden diferir de los originales."
        elif eps <= 2.0:
            nivel_priv, color_priv = "MODERADA", COLOR_MED
            desc_priv = "Buen equilibrio entre privacidad y precisión."
        else:
            nivel_priv, color_priv = "BAJA", COLOR_HIGH
            desc_priv = "Poco ruido. Datos precisos, pero protección limitada."

        st.markdown(f"""
        <div style='background:{COLOR_CARD};border:1px solid {COLOR_BORDER};border-left:4px solid {color_priv};
                    border-radius:6px;padding:1.2rem 1.5rem;'>
            <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem;'>
                <strong style='color:{COLOR_TEXT};'>Nivel de privacidad: {nivel_priv}</strong>
                <span style='color:{color_priv};font-weight:700;font-size:1.1rem;'>ε = {eps:.2f}</span>
            </div>
            <p style='color:{COLOR_MUTED};font-size:0.88rem;margin:0;'>{desc_priv}</p>
            <p style='color:{COLOR_MUTED};font-size:0.82rem;margin:0.4rem 0 0;'>
                Ruido en {n_cols} columnas numéricas — Mecanismo Laplace (diffprivlib IBM).
            </p>
        </div>
        """, unsafe_allow_html=True)

    # ═════════════════════════════════════════════════════════════════════════
    # ANÁLISIS COMPARATIVO SISTEMÁTICO
    # ═════════════════════════════════════════════════════════════════════════
    st.markdown("---")

    if columnas_qi and tecnica in ("K-Anonimidad", "L-Diversidad"):
        st.markdown(
            "<div class='section-header'>Análisis comparativo: curva de trade-off</div>",
            unsafe_allow_html=True,
        )
        supp_level = params.get("supp", 30)
        k_actual   = params.get("k", 3)
        l_value    = params.get("l", 2)

        subtitulo = (
            f"Cómo evoluciona el equilibrio privacidad/utilidad a medida que varía k "
            f"(supresión máxima fija al {supp_level}%"
            + (f", l = {l_value}" if tecnica == "L-Diversidad" else "")
            + f"). El <strong>F-Score</strong> integra ambas dimensiones en un único indicador."
        )
        st.markdown(
            f"<p style='color:{COLOR_MUTED};font-size:0.88rem;margin-bottom:1.2rem;'>{subtitulo}</p>",
            unsafe_allow_html=True,
        )

        with st.spinner("Calculando curva de trade-off para k = 2…15 (solo la primera vez)…"):
            if tecnica == "K-Anonimidad":
                filas = _curva_k(df_base, tuple(columnas_qi), supp_level=supp_level)
            else:
                filas = _curva_ldiv(
                    df_base, tuple(columnas_qi), col_sensible,
                    l_value=l_value, supp_level=supp_level,
                )

        st.markdown(_tabla_k_html(filas, k_actual), unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        fig_curva = _fig_curva_k(filas, k_actual)
        if fig_curva:
            st.pyplot(fig_curva)
            plt.close(fig_curva)

        # Tarjeta de recomendación
        filas_ok = [f for f in filas if f["fscore"] is not None]
        if filas_ok:
            mejor = max(filas_ok, key=lambda f: f["fscore"])
            actual_rows = [f for f in filas_ok if f["k"] == k_actual]
            if mejor["k"] != k_actual and actual_rows:
                actual_fs = actual_rows[0]["fscore"]
                st.markdown(f"""
                <div style='background:{COLOR_LOW_BG};border:1px solid {COLOR_LOW_BD};
                            border-radius:6px;padding:1rem 1.5rem;margin-top:0.8rem;'>
                    <strong style='color:{COLOR_LOW};'>Recomendación: </strong>
                    <span style='color:{COLOR_TEXT};font-size:0.9rem;'>
                        k = {mejor["k"]} maximiza el F-Score ({mejor["fscore"]:.1%}),
                        con riesgo {mejor["riesgo"]:.1%} y retención {mejor["retencion"]:.1%}.
                        Con k = {k_actual} (el valor actual) el F-Score es {actual_fs:.1%}.
                    </span>
                </div>
                """, unsafe_allow_html=True)

    elif tecnica == "Privacidad Diferencial":
        st.markdown(
            "<div class='section-header'>Análisis comparativo: curva ε vs utilidad</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<p style='color:{COLOR_MUTED};font-size:0.88rem;margin-bottom:1.2rem;'>"
            f"Cómo evoluciona el equilibrio privacidad/utilidad a medida que varía ε. "
            f"La <strong>utilidad</strong> se mide como 1 − MAE/rango sobre las columnas numéricas.</p>",
            unsafe_allow_html=True,
        )

        eps_actual   = attrs.get("epsilon_total", 1.0)
        sensibilidad = params.get("sensibilidad", 1.0)

        with st.spinner("Calculando curva de trade-off para distintos valores de ε…"):
            filas_dp = _curva_dp(df_base, sensibilidad=sensibilidad)

        st.markdown(_tabla_dp_html(filas_dp, eps_actual), unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        fig_dp = _fig_curva_dp(filas_dp, eps_actual)
        if fig_dp:
            st.pyplot(fig_dp)
            plt.close(fig_dp)

        # Tarjeta de recomendación
        filas_ok = [f for f in filas_dp if f["fscore"] is not None]
        if filas_ok:
            mejor = max(filas_ok, key=lambda f: f["fscore"])
            if abs(mejor["epsilon"] - eps_actual) > 1e-6:
                st.markdown(f"""
                <div style='background:{COLOR_LOW_BG};border:1px solid {COLOR_LOW_BD};
                            border-radius:6px;padding:1rem 1.5rem;margin-top:0.8rem;'>
                    <strong style='color:{COLOR_LOW};'>Recomendación: </strong>
                    <span style='color:{COLOR_TEXT};font-size:0.9rem;'>
                        ε = {mejor["epsilon"]} maximiza el F-Score ({mejor["fscore"]:.1%}),
                        con privacidad {mejor["privacidad"]:.1%} y utilidad {mejor["utilidad"]:.1%}.
                        Con ε = {eps_actual:.2f} (el valor actual) el F-Score es
                        {next((f["fscore"] for f in filas_ok if abs(f["epsilon"] - eps_actual) < 1e-6), 0.0):.1%}.
                    </span>
                </div>
                """, unsafe_allow_html=True)

    # ── Vista previa lado a lado ─────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Vista previa: Original vs Anonimizado")

    col_o, col_a = st.columns(2)
    with col_o:
        st.markdown(f"<div class='section-header'>Original - {registros_orig} registros</div>",
                    unsafe_allow_html=True)
        st.dataframe(df.head(20), use_container_width=True, height=300)
    with col_a:
        st.markdown(f"<div class='section-header'>Anonimizado - {registros_anon} registros</div>",
                    unsafe_allow_html=True)
        st.dataframe(df_anon.head(20), use_container_width=True, height=300)
