import streamlit as st
import matplotlib.pyplot as plt
from utils.metricas import (
    riesgo_maximo, riesgo_medio, tasa_unicidad, k_value,
    riesgo_label, generar_grafico_riesgos,
)

# Paleta institucional
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


def render():
    df               = st.session_state.get("df")
    df_anon          = st.session_state.get("df_anonimizado")
    columnas_qi      = st.session_state.get("columnas_qi", [])
    tecnica          = st.session_state.get("tecnica_usada", "")
    params           = st.session_state.get("params_anon", {})
    attrs            = st.session_state.get("attrs_anon", {})

    if df is None or df_anon is None:
        st.info("Primero importa datos y aplica una tecnica de anonimizacion.")
        return

    st.markdown(
        f"<div class='section-header'>Comparativa - Original vs {tecnica}</div>",
        unsafe_allow_html=True,
    )

    registros_orig = len(df)
    registros_anon = len(df_anon)
    suprimidos     = registros_orig - registros_anon
    retencion      = registros_anon / registros_orig if registros_orig > 0 else 0

    # Parametros aplicados
    if tecnica == "K-Anonimidad":
        params_text = f"k = {params.get('k', '?')}"
    elif tecnica == "L-Diversidad":
        params_text = f"k = {params.get('k', '?')}, l = {params.get('l', '?')}"
    elif tecnica == "Privacidad Diferencial":
        params_text = f"eps = {attrs.get('epsilon_total', '?')}"
    else:
        params_text = ""

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
                    {registros_orig} -> {registros_anon} registros
                    ({suprimidos} suprimidos, retencion {retencion:.1%})
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Metricas lado a lado ────────────────────────────────────────────
    if columnas_qi and tecnica != "Privacidad Diferencial":
        st.markdown("### Metricas de riesgo: antes y despues")

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
                    icono = f"<span style='color:{COLOR_LOW};font-weight:600;'>Baja {mejora:.1%}</span>"
                elif mejora < -0.01:
                    icono = f"<span style='color:{COLOR_HIGH};font-weight:600;'>Sube {abs(mejora):.1%}</span>"
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

        filas = (
            _fila("Riesgo maximo (fiscal)",       r_max_orig,  r_max_anon)
            + _fila("Riesgo medio (periodista)",   r_med_orig,  r_med_anon)
            + _fila("Tasa de unicidad (marketer)", t_unic_orig, t_unic_anon)
            + _fila("K-anonimidad (k minimo)",     k_orig,      k_anon,     es_pct=False)
        )

        st.markdown(f"""
        <div style='background:{COLOR_CARD};border:1px solid {COLOR_BORDER};border-radius:6px;
                    overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.06);margin-bottom:1.5rem;'>
            <table style='width:100%;border-collapse:collapse;'>
                <thead>
                    <tr style='background:#f8f9fb;'>
                        <th style='padding:0.7rem 1rem;text-align:left;color:{COLOR_MUTED};font-size:0.75rem;
                                   text-transform:uppercase;border-bottom:2px solid {COLOR_BORDER};'>Metrica</th>
                        <th style='padding:0.7rem 1rem;text-align:center;color:{COLOR_HIGH};font-size:0.75rem;
                                   text-transform:uppercase;border-bottom:2px solid {COLOR_BORDER};'>Original</th>
                        <th style='padding:0.7rem 1rem;text-align:center;color:{COLOR_PRIMARY};font-size:0.75rem;
                                   text-transform:uppercase;border-bottom:2px solid {COLOR_BORDER};'>Anonimizado</th>
                        <th style='padding:0.7rem 1rem;text-align:center;color:{COLOR_MUTED};font-size:0.75rem;
                                   text-transform:uppercase;border-bottom:2px solid {COLOR_BORDER};'>Cambio</th>
                    </tr>
                </thead>
                <tbody>{filas}</tbody>
            </table>
        </div>
        """, unsafe_allow_html=True)

        # Grafico comparativo
        st.markdown("### Grafico comparativo")
        fig = generar_grafico_riesgos(
            r_max_orig, r_med_orig, t_unic_orig,
            r_max_anon, r_med_anon, t_unic_anon,
        )
        st.pyplot(fig)
        plt.close(fig)

        # Alerta de balance
        st.markdown("---")
        privacidad_anon = max(0.0, 1.0 - r_max_anon)
        fscore = 2 * (privacidad_anon * retencion) / (privacidad_anon + retencion) if (privacidad_anon + retencion) > 0 else 0

        if fscore >= 0.80:
            bg_c, bd_c, tx_c = COLOR_LOW_BG, COLOR_LOW_BD, COLOR_LOW
            icono, nivel = "OK", "OPTIMO"
        elif fscore >= 0.50:
            bg_c, bd_c, tx_c = COLOR_MED_BG, COLOR_MED_BD, COLOR_MED
            icono, nivel = "~", "ACEPTABLE"
        else:
            bg_c, bd_c, tx_c = COLOR_HIGH_BG, COLOR_HIGH_BD, COLOR_HIGH
            icono, nivel = "!", "INSUFICIENTE"

        st.markdown(f"""
        <div style='background:{bg_c};border:1px solid {bd_c};border-radius:6px;padding:1.2rem 1.5rem;'>
            <strong style='color:{tx_c};font-size:1rem;'>Balance Privacidad / Utilidad: {nivel}</strong>
            <p style='margin:0.4rem 0 0;color:{COLOR_TEXT};font-size:0.88rem;'>
                F-Score: <strong style='color:{tx_c}'>{fscore:.1%}</strong>
                (privacidad {privacidad_anon:.1%} x retencion {retencion:.1%})
            </p>
        </div>
        """, unsafe_allow_html=True)

    elif tecnica == "Privacidad Diferencial":
        st.markdown("### Impacto de la privacidad diferencial")

        eps = attrs.get("epsilon_total", 0)
        n_cols = attrs.get("n_columnas_ruido", 0)

        if eps <= 0.5:
            nivel_priv, color_priv = "MUY ALTA", COLOR_LOW
            desc_priv = "Mucho ruido anadido. Alta proteccion, pero los valores pueden diferir de los originales."
        elif eps <= 2.0:
            nivel_priv, color_priv = "MODERADA", COLOR_MED
            desc_priv = "Buen equilibrio entre privacidad y precision."
        else:
            nivel_priv, color_priv = "BAJA", COLOR_HIGH
            desc_priv = "Poco ruido. Datos precisos, pero proteccion limitada."

        st.markdown(f"""
        <div style='background:{COLOR_CARD};border:1px solid {COLOR_BORDER};border-left:4px solid {color_priv};
                    border-radius:6px;padding:1.2rem 1.5rem;'>
            <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem;'>
                <strong style='color:{COLOR_TEXT};'>Nivel de privacidad: {nivel_priv}</strong>
                <span style='color:{color_priv};font-weight:700;font-size:1.1rem;'>eps = {eps:.2f}</span>
            </div>
            <p style='color:{COLOR_MUTED};font-size:0.88rem;margin:0;'>{desc_priv}</p>
            <p style='color:{COLOR_MUTED};font-size:0.82rem;margin:0.4rem 0 0;'>
                Ruido en {n_cols} columnas numericas - Mecanismo Laplace (diffprivlib IBM).
            </p>
        </div>
        """, unsafe_allow_html=True)

    # ── Vista previa lado a lado ────────────────────────────────────────
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
