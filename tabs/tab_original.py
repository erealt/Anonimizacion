import streamlit as st

from utils.metrics import compute_prosecutor_risk, compute_journalist_risk, compute_marketer_risk


def render(df, qi_cols, source):
    if df is None:
        st.info("👈 Ve a la pestaña **📥 IMPORTAR DATOS** para cargar un dataset.")
        return

    st.markdown(
        f"<div class='section-header'>{source} · {len(df)} registros · {len(df.columns)} columnas</div>",
        unsafe_allow_html=True,
    )
    st.dataframe(df, use_container_width=True, height=350)
    c1, c2, c3 = st.columns(3)
    c1.metric("Registros", len(df))
    c2.metric("Columnas", len(df.columns))
    c3.metric("Cuasi-identificadores", len(qi_cols))

    if qi_cols:
        st.markdown("---")
        st.markdown("<div class='section-header'>Riesgo base (sin anonimizar)</div>", unsafe_allow_html=True)
        r1, r2, r3 = st.columns(3)
        r1.metric("Riesgo Fiscal", f"{compute_prosecutor_risk(df, qi_cols):.2%}")
        r2.metric("Riesgo Periodístico", f"{compute_journalist_risk(df, qi_cols):.2%}")
        r3.metric("Riesgo Marketing", f"{compute_marketer_risk(df, qi_cols):.2%}")
