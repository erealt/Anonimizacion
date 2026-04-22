import streamlit as st

from utils.styles import CSS
from tabs import tab_import, tab_original

st.set_page_config(
    page_title="Anonimización",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(CSS, unsafe_allow_html=True)

# ── Barra lateral ──
with st.sidebar:
    st.markdown("## 🔒 Anonimización")
    st.markdown(
        "<p style='color:#6b7280;font-size:0.8rem'> Anonimización y Riesgo de Reidentificación</p>",
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.markdown("<div class='section-header'>Técnica de anonimización</div>", unsafe_allow_html=True)
    tecnica = st.radio("", ["K-Anonimato", "L-Diversidad", "Privacidad Diferencial"], label_visibility="collapsed")
    st.markdown("---")
    st.markdown("<div class='section-header'>Parámetros</div>", unsafe_allow_html=True)
    if tecnica == "K-Anonimato":
        k = st.slider("Valor de k", 2, 20, 3)
        l, epsilon, sensibilidad = 2, 1.0, 1.0
    elif tecnica == "L-Diversidad":
        k = st.slider("Valor de k", 2, 20, 3)
        l = st.slider("Valor de l", 2, 10, 2)
        epsilon, sensibilidad = 1.0, 1.0
    else:
        epsilon = st.slider("Epsilon (ε)", 0.01, 5.0, 1.0, step=0.01)
        sensibilidad = st.slider("Sensibilidad (Δf)", 0.1, 10.0, 1.0, step=0.1)
        k, l = 3, 2
    st.markdown("---")
    ejecutar = st.button("▶ Aplicar anonimización", use_container_width=True)

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
    tab_original.render(df, columnas_qi, fuente)
