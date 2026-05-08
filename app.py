import streamlit as st

from utils.styles import CSS
from tabs import tab_import, tab_original, tab_anonimizacion, tab_metricas, tab_comparativa

st.set_page_config(
    page_title="Anonimización de Datos",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(CSS, unsafe_allow_html=True)

# ── Estado de navegación ─────────────────────────────────────────────────────
if "pagina_activa" not in st.session_state:
    st.session_state["pagina_activa"] = 0

df      = st.session_state.get("df")
df_anon = st.session_state.get("df_anonimizado")

PAGINAS = [
    "Importar datos",
    "Datos originales",
    "Anonimizar datos",
    "Métricas de riesgo",
    "Comparativa",
]

def pagina_disponible(i):
    if i <= 0:  return True
    if i <= 2:  return df is not None
    return df_anon is not None

# Corregir si la página activa ya no está disponible
pagina = st.session_state["pagina_activa"]
if not pagina_disponible(pagina):
    pagina = 0
    st.session_state["pagina_activa"] = 0

def ir_a(n):
    st.session_state["pagina_activa"] = n
    

# ── Cabecera ─────────────────────────────────────────────────────────────────
st.markdown("## 🔒 Sistema de Anonimización de Datos")
st.markdown(
    "<p style='color:#6b7280;margin-top:-0.5rem;margin-bottom:1.5rem;font-size:0.92rem;'>"
    "Herramienta de anonimización y evaluación del riesgo residual de reidentificación</p>",
    unsafe_allow_html=True,
)


def stepper():
    pasos_html = ""
    for i, nombre in enumerate(PAGINAS):
        disponible = pagina_disponible(i)
        activo     = (i == pagina)
        completado = (i < pagina) and disponible

        if activo:
            circulo_bg, circulo_color, circulo_borde = "#1a3a6b", "#ffffff", "#1a3a6b"
            texto_color, font_weight = "#1a3a6b", "600"
            simbolo = str(i + 1)
        elif completado:
            circulo_bg, circulo_color, circulo_borde = "#166534", "#ffffff", "#166534"
            texto_color, font_weight = "#374151", "400"
            simbolo = "✓"
        elif disponible:
            circulo_bg, circulo_color, circulo_borde = "#ffffff", "#6b7280", "#d1d5db"
            texto_color, font_weight = "#6b7280", "400"
            simbolo = str(i + 1)
        else:
            circulo_bg, circulo_color, circulo_borde = "#f5f6f8", "#d1d5db", "#e5e7eb"
            texto_color, font_weight = "#d1d5db", "400"
            simbolo = "🔒"

        pasos_html += f"""
        <div style='display:flex;flex-direction:column;align-items:center;gap:0.4rem;min-width:100px;'>
            <div style='width:32px;height:32px;border-radius:50%;background:{circulo_bg};
                        border:2px solid {circulo_borde};display:flex;align-items:center;
                        justify-content:center;font-size:0.8rem;font-weight:700;color:{circulo_color};'>
                {simbolo}
            </div>
            <span style='font-size:0.72rem;font-weight:{font_weight};color:{texto_color};
                         text-align:center;line-height:1.3;'>{nombre}</span>
        </div>"""

        if i < len(PAGINAS) - 1:
            linea_color = "#166534" if i < pagina else "#e5e7eb"
            pasos_html += f"""
            <div style='flex:1;height:2px;background:{linea_color};margin-top:-1rem;
                        align-self:flex-start;margin-top:15px;'></div>"""

    st.markdown(
        f"<div style='display:flex;align-items:flex-start;gap:0;margin-bottom:1.5rem;"
        f"background:#ffffff;border:1px solid #e5e7eb;border-radius:8px;padding:1.2rem 1.5rem;'>"
        f"{pasos_html}</div>",
        unsafe_allow_html=True,
    )

stepper()

# ── Barra de navegación ──────────────────────────────────────────────────────
cols_nav = st.columns(len(PAGINAS))
for i, (col, nombre) in enumerate(zip(cols_nav, PAGINAS)):
    with col:
        st.button(
            nombre,
            key=f"nav_{i}",
            use_container_width=True,
            type="primary" if i == pagina else "secondary",
            disabled=not pagina_disponible(i),
            on_click=ir_a,
            args=(i,),
        )

st.markdown("<div style='margin-bottom:1.5rem'></div>", unsafe_allow_html=True)

columnas_qi      = st.session_state.get("columnas_qi", [])
columna_sensible = st.session_state.get("columna_sensible", "")
fuente           = st.session_state.get("fuente", "")

if pagina == 0:
    tab_import.render()

elif pagina == 1:
    tab_original.render(df, columnas_qi, fuente)

elif pagina == 2:
    tab_anonimizacion.render()

elif pagina == 3:
    tab_metricas.render()

elif pagina == 4:
    tab_comparativa.render()
