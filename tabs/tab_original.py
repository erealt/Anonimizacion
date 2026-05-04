import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from utils.metricas import riesgo_maximo,riesgo_medio,generar_grafico_riesgos,riesgo_label

# ── Paleta institucional ──
COLOR_BG        = "#ffffff"
COLOR_BG_PAGE   = "#f5f6f8"
COLOR_CARD      = "#ffffff"
COLOR_BORDER    = "#d1d5db"
COLOR_PRIMARY   = "#1a3a6b"
COLOR_TEXT      = "#1a2340"
COLOR_MUTED     = "#6b7280"
COLOR_LOW       = "#166534"
COLOR_LOW_BG    = "#dcfce7"
COLOR_LOW_BD    = "#86efac"
COLOR_MED       = "#854d0e"
COLOR_MED_BG    = "#fef9c3"
COLOR_MED_BD    = "#fde047"
COLOR_HIGH      = "#991b1b"
COLOR_HIGH_BG   = "#fee2e2"
COLOR_HIGH_BD   = "#fca5a5"


def _badge_colors(clase):
    if "bajo" in clase or "low" in clase:
        return COLOR_LOW_BG, COLOR_LOW_BD, COLOR_LOW
    elif "medio" in clase or "medium" in clase:
        return COLOR_MED_BG, COLOR_MED_BD, COLOR_MED
    else:
        return COLOR_HIGH_BG, COLOR_HIGH_BD, COLOR_HIGH


def render(df, qi_cols, source):
    if df is None:
        st.info("👈 Ve a la pestaña **📥 IMPORTAR DATOS** para cargar un dataset.")
        return

    st.markdown(
        f"<div class='section-header'>{source} · {len(df)} registros · {len(df.columns)} columnas</div>",
        unsafe_allow_html=True,
    )
    st.dataframe(df.head(100), use_container_width=True, height=250)
    st.caption(f"Vista previa de las primeras 100 filas (total: {len(df)}).")

    if not qi_cols:
        st.warning("⚠️ Selecciona Cuasi-Identificadores en la pestaña de Importar para ver el análisis de riesgo.")
        return

    st.markdown("---")
    st.markdown("### Análisis de Riesgo Original")
    st.markdown(
        "<p style='color:#6b7280;font-size:0.9rem;'>Evaluación del riesgo de re-identificación en los datos sin anonimizar.</p>",
        unsafe_allow_html=True,
    )

    r_maximo   = riesgo_maximo(df, qi_cols)
    r_medio    = riesgo_medio(df, qi_cols)
    t_unicidad = tasa_unicidad(df, qi_cols)
    k_actual   = k_value(df, qi_cols)

    label_m, class_m = riesgo_label(t_unicidad)
    label_f, class_f = riesgo_label(r_maximo)
    label_p, class_p = riesgo_label(r_medio)

    # ── Alerta global (F-Score) ──
    utilidad   = 1.0
    privacidad = max(0.0, 1.0 - r_maximo)
    riesgo_global = (
        2 * (privacidad * utilidad) / (privacidad + utilidad)
        if (privacidad + utilidad) > 0 else 0.0
    )

    if riesgo_global < 0.50:
        bg_c, bd_c, tx_c = COLOR_HIGH_BG, COLOR_HIGH_BD, COLOR_HIGH
        icono, nivel = "⚠️", "CRÍTICO"
        texto = f"El Índice Global (F-Score) es <strong style='color:{tx_c}'>{riesgo_global:.1%}</strong>. La privacidad ({privacidad:.1%}) es inaceptable."
    elif riesgo_global < 0.80:
        bg_c, bd_c, tx_c = COLOR_MED_BG, COLOR_MED_BD, COLOR_MED
        icono, nivel = "⚖️", "MEJORABLE"
        texto = f"El Índice Global es <strong style='color:{tx_c}'>{riesgo_global:.1%}</strong>. Se recomienda aplicar anonimización."
    else:
        bg_c, bd_c, tx_c = COLOR_LOW_BG, COLOR_LOW_BD, COLOR_LOW
        icono, nivel = "✅", "ÓPTIMO"
        texto = f"El Índice Global es <strong style='color:{tx_c}'>{riesgo_global:.1%}</strong>. El balance privacidad/utilidad es adecuado."

    st.markdown(f"""
    <div style='background:{bg_c};border:1px solid {bd_c};border-radius:6px;padding:1.2rem 1.5rem;margin-bottom:1.5rem;'>
        <div style='display:flex;align-items:center;gap:1rem;'>
            <div style='font-size:1.5rem;'>{icono}</div>
            <div>
                <strong style='color:{tx_c};font-size:1rem;'>Balance Privacidad/Utilidad: {nivel}</strong>
                <p style='margin:0.4rem 0 0;color:{COLOR_TEXT};font-size:0.88rem;'>{texto}</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Tarjetas de riesgo ──
    c1, c2, c3 = st.columns(3)

    def tarjeta(titulo, porcentaje, etiqueta, clase):
        bg_b, bd_b, col_b = _badge_colors(clase)
        col_num = col_b
        return f"""
        <div style='background:{COLOR_CARD};border:1px solid {COLOR_BORDER};border-top:3px solid {col_num};
                    border-radius:6px;padding:1.4rem;box-shadow:0 1px 3px rgba(0,0,0,0.06);height:100%;'>
            <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;'>
                <strong style='color:{COLOR_MUTED};font-size:0.88rem;'>{titulo}</strong>
                <span style='background:{bg_b};color:{col_b};border:1px solid {bd_b};
                             padding:0.2rem 0.6rem;border-radius:4px;font-size:0.72rem;font-weight:600;'>{etiqueta}</span>
            </div>
            <div style='font-size:2.6rem;font-weight:700;color:{col_num};line-height:1;margin-bottom:0.2rem;'>
                {porcentaje:.1%}
            </div>
        </div>"""

    with c1:
        st.markdown(tarjeta("Riesgo Máximo", r_maximo, label_f, class_f), unsafe_allow_html=True)
    with c2:
        st.markdown(tarjeta("Riesgo Medio", r_medio, label_p, class_p), unsafe_allow_html=True)
    with c3:
        st.markdown(tarjeta("Tasa de Unicidad", t_unicidad, label_m, class_m), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── K-Anonimidad actual ──
    color_k = COLOR_HIGH if k_actual < 3 else COLOR_LOW
    st.markdown(f"""
    <div style='background:{COLOR_CARD};border:1px solid {COLOR_BORDER};border-radius:6px;
                padding:1.2rem 1.5rem;display:flex;justify-content:space-between;align-items:center;
                box-shadow:0 1px 3px rgba(0,0,0,0.06);'>
        <div>
            <strong style='color:{COLOR_TEXT};font-size:1rem;'>Nivel de K-Anonimidad Actual</strong><br>
            <span style='color:{COLOR_MUTED};font-size:0.88rem;'>Tamaño mínimo de grupo encontrado en el dataset</span>
        </div>
        <div style='font-size:2.8rem;font-weight:700;color:{color_k};line-height:1;'>k = {k_actual}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Gráficos ──
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.markdown("**Distribución de Grupos**")
        sizes   = df.groupby(qi_cols, dropna=False).size()
        k1      = (sizes == 1).sum()
        k2      = (sizes == 2).sum()
        k3_plus = (sizes >= 3).sum()

        fig1, ax1 = plt.subplots(figsize=(2.8, 2.8))
        fig1.patch.set_facecolor(COLOR_BG)

        valores   = [k1, k2, k3_plus]
        etiquetas = [f"k=1 (únicos): {k1}", f"k=2: {k2}", f"k≥3: {k3_plus}"]
        colores   = [COLOR_HIGH, "#d97706", COLOR_LOW]

        val_f  = [v for v in valores if v > 0]
        etq_f  = [e for v, e in zip(valores, etiquetas) if v > 0]
        col_f  = [c for v, c in zip(valores, colores) if v > 0]

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

    with col_g2:
        st.markdown("**Riesgo por Atributo (Aislamiento)**")
        st.caption("Muestra si alguna columna por sí sola hace únicos a los individuos.")

        riesgos_attr = []
        for col in qi_cols:
            unicos = (df[col].value_counts(dropna=False) == 1).sum()
            riesgos_attr.append((str(col), (unicos / len(df)) * 100))
        riesgos_attr.sort(key=lambda x: x[1], reverse=True)

        cols_names   = [x[0][:12] + ".." if len(x[0]) > 12 else x[0] for x in riesgos_attr]
        riesgos_vals = [x[1] for x in riesgos_attr]

        fig2, ax2 = plt.subplots(figsize=(5, 3.5))
        fig2.patch.set_facecolor(COLOR_BG)
        ax2.set_facecolor(COLOR_BG)

        ax2.bar(cols_names, riesgos_vals, color=COLOR_PRIMARY, alpha=0.85)
        ax2.set_ylim(0, max(10, (max(riesgos_vals) if riesgos_vals else 0) * 1.3))
        ax2.tick_params(colors=COLOR_MUTED, labelsize=8)
        ax2.set_xticks(range(len(cols_names)))
        ax2.set_xticklabels(cols_names, rotation=45, ha="right", fontsize=8)
        for s in ax2.spines.values():
            s.set_edgecolor(COLOR_BORDER)
        ax2.spines["top"].set_visible(False)
        ax2.spines["right"].set_visible(False)
        for bar, val in zip(ax2.patches, riesgos_vals):
            ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                     f"{val:.1f}%", ha="center", color=COLOR_MUTED, fontsize=8)
        plt.tight_layout()
        st.pyplot(fig2)

    st.markdown("<br>", unsafe_allow_html=True)
    _, col_btn = st.columns([3, 1])
    with col_btn:
        if st.button("Continuar →", key="continuar_original", use_container_width=True, type="primary"):
            st.session_state["pagina_activa"] = 2
            st.rerun()
