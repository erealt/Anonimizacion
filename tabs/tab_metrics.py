import streamlit as st

from utils.metrics import (
    compute_prosecutor_risk,
    compute_journalist_risk,
    compute_marketer_risk,
    compute_k_value,
    risk_label,
    render_risk_chart,
)


def render(df, qi_cols, technique, epsilon):
    if df is None:
        st.info("👈 Ve a la pestaña **📥 IMPORTAR DATOS** para cargar un dataset.")
        return
    if "anon_df" not in st.session_state:
        st.info("Aplica primero una técnica de anonimización.")
        return

    anon_df = st.session_state["anon_df"]
    technique = st.session_state.get("technique", technique)

    pr_orig = compute_prosecutor_risk(df, qi_cols)
    jr_orig = compute_journalist_risk(df, qi_cols)
    mr_orig = compute_marketer_risk(df, qi_cols)

    if technique != "Privacidad Diferencial" and qi_cols:
        pr_anon = compute_prosecutor_risk(anon_df, qi_cols)
        jr_anon = compute_journalist_risk(anon_df, qi_cols)
        mr_anon = compute_marketer_risk(anon_df, qi_cols)
        k_val = compute_k_value(anon_df, qi_cols)
    else:
        pr_anon = min(1.0, epsilon / 10)
        jr_anon = min(1.0, epsilon / 15)
        mr_anon = 0.0
        k_val = None

    st.markdown("<div class='section-header'>Métricas de riesgo de reidentificación</div>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Riesgo Fiscal", f"{pr_anon:.2%}", delta=f"{pr_anon - pr_orig:.2%}", delta_color="inverse")
    col2.metric("Riesgo Periodístico", f"{jr_anon:.2%}", delta=f"{jr_anon - jr_orig:.2%}", delta_color="inverse")
    col3.metric("Riesgo Marketing", f"{mr_anon:.2%}", delta=f"{mr_anon - mr_orig:.2%}", delta_color="inverse")
    if k_val is not None:
        col4.metric("k efectivo", k_val)

    st.markdown("---")
    st.markdown("<div class='section-header'>Nivel de riesgo residual</div>", unsafe_allow_html=True)
    bc1, bc2, bc3 = st.columns(3)
    for col_ui, val, label in zip([bc1, bc2, bc3], [pr_anon, jr_anon, mr_anon], ["Fiscal", "Periodístico", "Marketing"]):
        rl, rc = risk_label(val)
        col_ui.markdown(
            f"<div style='text-align:center;margin-top:0.5rem'>"
            f"<div style='color:#6b7280;font-size:0.75rem;margin-bottom:0.3rem'>{label}</div>"
            f"<span class='risk-badge {rc}'>{rl}</span></div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown("<div class='section-header'>Comparativa visual</div>", unsafe_allow_html=True)
    st.pyplot(render_risk_chart(pr_orig, jr_orig, mr_orig, pr_anon, jr_anon, mr_anon))
