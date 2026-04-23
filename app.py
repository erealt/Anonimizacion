import streamlit as st

from utils.styles import CSS
from tabs import tab_import, tab_original, tab_anonimizacion
from utils.metricas import *

st.set_page_config(
    page_title="Anonimización",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(CSS, unsafe_allow_html=True)

df               = st.session_state.get("df", None)
columnas_qi      = st.session_state.get("columnas_qi", [])
columna_sensible = st.session_state.get("columna_sensible", "")
fuente           = st.session_state.get("fuente", "")

st.markdown("# 🔒 Anonimización")
st.markdown(
    "<p style='color:#6b7280;margin-top:-1rem;margin-bottom:2rem'>"
    "Prototipo de anonimización y evaluación de riesgo residual de reidentificación</p>",
    unsafe_allow_html=True,
)

tab0, tab1, tab2, tab3, tab4 = st.tabs([
    "📥 IMPORTAR DATOS",
    "📊 DATOS ORIGINALES",
    "🔒 DATOS ANONIMIZADOS",
    "📈 MÉTRICAS DE RIESGO",
    "⚖️ COMPARATIVA",
])

with tab0:
    tab_import.render()

with tab1:
    if df is None:
        st.info("👈 Ve a la pestaña **📥 IMPORTAR DATOS** para cargar un dataset.")
    else:
        tab_original.render(df, columnas_qi, fuente)

with tab2:
    tab_anonimizacion.render()
