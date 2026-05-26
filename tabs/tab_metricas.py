import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from utils.metricas import (
    riesgo_maximo, riesgo_medio, tasa_unicidad, k_value, riesgo_label,
    generar_grafico_riesgos, calcular_fscore_revisado,
)

# ── Paleta institucional ──
COLOR_BG      = "#ffffff"
COLOR_CARD    = "#ffffff"
COLOR_BORDER  = "#d1d5db"
COLOR_TEXT    = "#1a2340"
COLOR_MUTED   = "#6b7280"
COLOR_LOW     = "#166534"
COLOR_LOW_BG  = "#dcfce7"
COLOR_LOW_BD  = "#86efac"
COLOR_MED     = "#854d0e"
COLOR_MED_BG  = "#fef9c3"
COLOR_MED_BD  = "#fde047"
COLOR_HIGH    = "#991b1b"
COLOR_HIGH_BG = "#fee2e2"
COLOR_HIGH_BD = "#fca5a5"


def _badge_colors(clase):
    if "bajo" in clase:
        return COLOR_LOW_BG, COLOR_LOW_BD, COLOR_LOW
    elif "medio" in clase:
        return COLOR_MED_BG, COLOR_MED_BD, COLOR_MED
    return COLOR_HIGH_BG, COLOR_HIGH_BD, COLOR_HIGH


def render():
    df               = st.session_state.get("df")
    df_anon          = st.session_state.get("df_anonimizado")
    columnas_qi      = st.session_state.get("columnas_qi", [])
    tecnica          = st.session_state.get("tecnica_usada", "")
    params           = st.session_state.get("params_anon", {})
    attrs            = st.session_state.get("attrs_anon", {})

    if df_anon is None:
        st.info("👈 Ve a la pestaña **🔒 ANONIMIZAR DATOS** para aplicar una técnica primero.")
        return

    # ── Cabecera ────────────────────────────────────────────────────────
    registros_orig = len(df) if df is not None else 0
    registros_anon = len(df_anon)
    suprimidos     = registros_orig - registros_anon
    retencion      = registros_anon / registros_orig if registros_orig > 0 else 0

    st.markdown(
        f"<div class='section-header'>Métricas de riesgo · {tecnica} · {registros_anon} registros</div>",
        unsafe_allow_html=True,
    )

    # ═════════════════════════════════════════════════════════════════════
    # SECCIÓN 1: RIESGO DE RE-IDENTIFICACIÓN (K-ANON / L-DIV)
    # ═════════════════════════════════════════════════════════════════════
    if columnas_qi and tecnica != "Privacidad Diferencial":

        # ── Métricas anonimizadas ───────────────────────────────────────
        r_max_anon  = riesgo_maximo(df_anon, columnas_qi)
        r_med_anon  = riesgo_medio(df_anon, columnas_qi)
        t_unic_anon = tasa_unicidad(df_anon, columnas_qi)
        k_anon      = k_value(df_anon, columnas_qi)

        # ── Métricas originales (para comparar) ────────────────────────
        r_max_orig  = riesgo_maximo(df, columnas_qi) if df is not None else 1.0
        r_med_orig  = riesgo_medio(df, columnas_qi)  if df is not None else 1.0
        t_unic_orig = tasa_unicidad(df, columnas_qi) if df is not None else 1.0

        label_f, class_f = riesgo_label(r_max_anon)
        label_p, class_p = riesgo_label(r_med_anon)
        label_m, class_m = riesgo_label(t_unic_anon)

        # ── Alerta global (F-Score con NCP) ────────────────────────────
        m = calcular_fscore_revisado(df, df_anon, columnas_qi)
        privacidad = m["privacidad"]
        fscore     = m["fscore"]
        utilidad   = m["utilidad"]
        ncp        = m["ncp"]

        if fscore >= 0.80:
            bg_c, bd_c, tx_c = COLOR_LOW_BG, COLOR_LOW_BD, COLOR_LOW
            icono, nivel = "✅", "ÓPTIMO"
        elif fscore >= 0.50:
            bg_c, bd_c, tx_c = COLOR_MED_BG, COLOR_MED_BD, COLOR_MED
            icono, nivel = "⚖️", "ACEPTABLE"
        else:
            bg_c, bd_c, tx_c = COLOR_HIGH_BG, COLOR_HIGH_BD, COLOR_HIGH
            icono, nivel = "⚠️", "INSUFICIENTE"

        texto = (f"F-Score: <strong style='color:{tx_c}'>{fscore:.1%}</strong> · "
                 f"Privacidad {privacidad:.1%} · Utilidad ajustada {utilidad:.1%}")
        detalle = (f"Retención: {retencion:.1%} · "
                   f"NCP (pérdida por generalización): {ncp:.1%} → "
                   f"Utilidad = {retencion:.1%} × (1 − {ncp:.1%}) = {utilidad:.1%}")

        st.markdown(f"""
        <div style='background:{bg_c};border:1px solid {bd_c};border-radius:6px;padding:1.2rem 1.5rem;margin-bottom:1.5rem;'>
            <div style='display:flex;align-items:center;gap:1rem;'>
                <div style='font-size:1.5rem;'>{icono}</div>
                <div>
                    <strong style='color:{tx_c};font-size:1rem;'>Balance Privacidad / Utilidad: {nivel}</strong>
                    <p style='margin:0.4rem 0 0;color:{COLOR_TEXT};font-size:0.88rem;'>{texto}</p>
                    <p style='margin:0.3rem 0 0;color:{COLOR_MUTED};font-size:0.80rem;'>{detalle}</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Tarjetas de riesgo ──────────────────────────────────────────
        st.markdown("### Riesgo de re-identificación (datos anonimizados)")

        c1, c2, c3 = st.columns(3)

        def tarjeta(titulo, porcentaje, etiqueta, clase, orig):
            bg_b, bd_b, col_b = _badge_colors(clase)
            delta = orig - porcentaje
            if delta > 0.01:
                delta_html = f"<span style='color:{COLOR_LOW};font-size:0.78rem;'>▼ {delta:.1%} vs original</span>"
            else:
                delta_html = f"<span style='color:{COLOR_MUTED};font-size:0.78rem;'>≈ sin cambio</span>"
            return f"""
            <div style='background:{COLOR_CARD};border:1px solid {COLOR_BORDER};border-top:3px solid {col_b};
                        border-radius:6px;padding:1.4rem;box-shadow:0 1px 3px rgba(0,0,0,0.06);height:100%;'>
                <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:0.8rem;'>
                    <strong style='color:{COLOR_MUTED};font-size:0.85rem;'>{titulo}</strong>
                    <span style='background:{bg_b};color:{col_b};border:1px solid {bd_b};
                                 padding:0.2rem 0.6rem;border-radius:4px;font-size:0.72rem;font-weight:600;'>{etiqueta}</span>
                </div>
                <div style='font-size:2.4rem;font-weight:700;color:{col_b};line-height:1;margin-bottom:0.3rem;'>
                    {porcentaje:.1%}
                </div>
                {delta_html}
            </div>"""

        with c1:
            st.markdown(tarjeta("Riesgo Máximo (Fiscal)", r_max_anon, label_f, class_f, r_max_orig), unsafe_allow_html=True)
        with c2:
            st.markdown(tarjeta("Riesgo Medio (Periodista)", r_med_anon, label_p, class_p, r_med_orig), unsafe_allow_html=True)
        with c3:
            st.markdown(tarjeta("Tasa de Unicidad (Marketer)", t_unic_anon, label_m, class_m, t_unic_orig), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── K-Anonimidad alcanzada ──────────────────────────────────────
        color_k = COLOR_LOW if k_anon >= 3 else COLOR_HIGH
        st.markdown(f"""
        <div style='background:{COLOR_CARD};border:1px solid {COLOR_BORDER};border-radius:6px;
                    padding:1.2rem 1.5rem;display:flex;justify-content:space-between;align-items:center;
                    box-shadow:0 1px 3px rgba(0,0,0,0.06);'>
            <div>
                <strong style='color:{COLOR_TEXT};font-size:1rem;'>Nivel de K-Anonimidad Alcanzado</strong><br>
                <span style='color:{COLOR_MUTED};font-size:0.88rem;'>Tamaño mínimo de grupo en los datos anonimizados</span>
            </div>
            <div style='font-size:2.8rem;font-weight:700;color:{color_k};line-height:1;'>k = {k_anon}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Gráficos ───────────────────────────────────────────────────
        col_g1, col_g2 = st.columns(2)

        with col_g1:
            st.markdown("**Distribución de Grupos (anonimizado)**")
            sizes   = df_anon.groupby(columnas_qi, dropna=False).size()
            k1      = int((sizes == 1).sum())
            k2      = int((sizes == 2).sum())
            k3_plus = int((sizes >= 3).sum())

            fig1, ax1 = plt.subplots(figsize=(2.8, 2.8))
            fig1.patch.set_facecolor(COLOR_BG)

            valores   = [k1, k2, k3_plus]
            etiquetas = [f"k=1 (únicos): {k1}", f"k=2: {k2}", f"k≥3: {k3_plus}"]
            colores   = [COLOR_HIGH, "#d97706", COLOR_LOW]

            val_f = [v for v in valores if v > 0]
            etq_f = [e for v, e in zip(valores, etiquetas) if v > 0]
            col_f = [c for v, c in zip(valores, colores) if v > 0]

            if val_f:
                wedges, texts = ax1.pie(
                    val_f, labels=etq_f, colors=col_f,
                    startangle=90, wedgeprops={"edgecolor": COLOR_BG, "linewidth": 1.5},
                )
                for t, c in zip(texts, col_f):
                    t.set_color(c)
                    t.set_fontsize(8)
            plt.tight_layout()
            st.pyplot(fig1)
            plt.close(fig1)

        with col_g2:
            st.markdown("**Comparativa de riesgo: Original vs Anonimizado**")
            fig2 = generar_grafico_riesgos(
                r_max_orig, r_med_orig, t_unic_orig,
                r_max_anon, r_med_anon, t_unic_anon,
            )
            st.pyplot(fig2)
            plt.close(fig2)

    # ═════════════════════════════════════════════════════════════════════
    # SECCIÓN 1-BIS: PRIVACIDAD DIFERENCIAL
    # ═════════════════════════════════════════════════════════════════════
    elif tecnica == "Privacidad Diferencial":
        eps_total = attrs.get("epsilon_total", 0)
        eps_col   = attrs.get("epsilon_por_columna", 0)
        n_cols    = attrs.get("n_columnas_ruido", 0)
        eps_gast  = attrs.get("epsilon_gastado", 0)

        # Alerta de nivel de privacidad
        if eps_total <= 0.5:
            bg_c, bd_c, tx_c = COLOR_LOW_BG, COLOR_LOW_BD, COLOR_LOW
            icono, nivel = "✅", "MUY ALTA"
            texto = "Ruido elevado. Alta protección, pero los valores pueden diferir significativamente de los originales."
        elif eps_total <= 2.0:
            bg_c, bd_c, tx_c = COLOR_MED_BG, COLOR_MED_BD, COLOR_MED
            icono, nivel = "⚖️", "MODERADA"
            texto = "Buen equilibrio entre privacidad y precisión de los datos."
        else:
            bg_c, bd_c, tx_c = COLOR_HIGH_BG, COLOR_HIGH_BD, COLOR_HIGH
            icono, nivel = "⚠️", "BAJA"
            texto = "Poco ruido añadido. Los datos son más precisos, pero la protección es limitada."

        st.markdown(f"""
        <div style='background:{bg_c};border:1px solid {bd_c};border-radius:6px;padding:1.2rem 1.5rem;margin-bottom:1.5rem;'>
            <div style='display:flex;align-items:center;gap:1rem;'>
                <div style='font-size:1.5rem;'>{icono}</div>
                <div>
                    <strong style='color:{tx_c};font-size:1rem;'>Nivel de Privacidad: {nivel}</strong>
                    <p style='margin:0.4rem 0 0;color:{COLOR_TEXT};font-size:0.88rem;'>{texto}</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        c1.metric("Epsilon total (ε)", f"{eps_total:.2f}")
        c2.metric("ε por columna", f"{eps_col:.3f}")
        c3.metric("Columnas con ruido", n_cols)

        st.markdown("<br>", unsafe_allow_html=True)

        # Barra de presupuesto
        pct = min(eps_gast / eps_total, 1.0) if eps_total > 0 else 0
        color_bar = COLOR_LOW if pct < 0.8 else COLOR_HIGH
        st.markdown(f"""
        <div style='background:{COLOR_CARD};border:1px solid {COLOR_BORDER};border-radius:6px;
                    padding:1.2rem 1.5rem;box-shadow:0 1px 3px rgba(0,0,0,0.06);'>
            <div style='display:flex;justify-content:space-between;margin-bottom:0.5rem;'>
                <strong style='color:{COLOR_TEXT};font-size:0.92rem;'>Presupuesto de privacidad consumido</strong>
                <span style='color:{color_bar};font-weight:600;'>{pct:.0%}</span>
            </div>
            <div style='background:#e5e7eb;border-radius:4px;height:12px;overflow:hidden;'>
                <div style='background:{color_bar};height:100%;width:{pct*100:.0f}%;border-radius:4px;
                            transition:width 0.3s;'></div>
            </div>
            <div style='color:{COLOR_MUTED};font-size:0.78rem;margin-top:0.4rem;'>
                ε gastado: {eps_gast:.3f} / {eps_total:.2f} · Mecanismo: Laplace (diffprivlib IBM)
            </div>
        </div>
        """, unsafe_allow_html=True)

    else:
        st.warning("⚠️ Selecciona cuasi-identificadores en la pestaña de importar para ver métricas de riesgo.")

    # ── Botón continuar ─────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    _, col_btn = st.columns([3, 1])
    with col_btn:
        if st.button("Ver comparativa →", key="continuar_metricas", use_container_width=True, type="primary"):
            st.session_state["pagina_activa"] = 4
            st.rerun()
