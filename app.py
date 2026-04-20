import streamlit as st

from utils.styles import CSS
from tabs import tab_import, tab_original, tab_anonymized, tab_metrics, tab_comparison

st.set_page_config(
    page_title="AnonRisk · Prototipo TFG",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(CSS, unsafe_allow_html=True)

# ── Sidebar ──
with st.sidebar:
    st.markdown("## 🔒 AnonRisk")
    st.markdown(
        "<p style='color:#6b7280;font-size:0.8rem'>Prototipo TFG · Anonimización y Riesgo de Reidentificación</p>",
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.markdown("<div class='section-header'>Técnica de anonimización</div>", unsafe_allow_html=True)
    technique = st.radio("", ["K-Anonimato", "L-Diversidad", "Privacidad Diferencial"], label_visibility="collapsed")
    st.markdown("---")
    st.markdown("<div class='section-header'>Parámetros</div>", unsafe_allow_html=True)
    if technique == "K-Anonimato":
        k = st.slider("Valor de k", 2, 20, 3)
        l, epsilon, sensitivity = 2, 1.0, 1.0
    elif technique == "L-Diversidad":
        k = st.slider("Valor de k", 2, 20, 3)
        l = st.slider("Valor de l", 2, 10, 2)
        epsilon, sensitivity = 1.0, 1.0
    else:
        epsilon = st.slider("Epsilon (ε)", 0.01, 5.0, 1.0, step=0.01)
        sensitivity = st.slider("Sensibilidad (Δf)", 0.1, 10.0, 1.0, step=0.1)
        k, l = 3, 2
    st.markdown("---")
    run = st.button("▶ Aplicar anonimización", use_container_width=True)

# ── Session state ──
df            = st.session_state.get("df", None)
qi_cols       = st.session_state.get("qi_cols", [])
sensitive_col = st.session_state.get("sensitive_col", "")
source        = st.session_state.get("source", "")

# ── Main header ──
st.markdown("# 🔒 AnonRisk")
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
    tab_original.render(df, qi_cols, source)

with tab2:
    tab_anonymized.render(df, qi_cols, sensitive_col, technique, k, l, epsilon, sensitivity, run)

with tab3:
    tab_metrics.render(df, qi_cols, technique, epsilon)

with tab4:
    tab_comparison.render(df, qi_cols, sensitive_col)
