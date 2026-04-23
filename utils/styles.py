CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
}

/* ── Fondo y contenedor principal ── */
.stApp {
    background-color: #f5f6f8;
    color: #1a2340;
}
.block-container {
    padding-top: 2rem;
    max-width: 1200px;
}

/* ── Título principal ── */
h1 { font-size: 1.6rem !important; font-weight: 700 !important; color: #1a2340 !important; }
h2 { font-size: 1.2rem !important; font-weight: 600 !important; color: #1a2340 !important; }
h3 { font-size: 1rem   !important; font-weight: 600 !important; color: #1a2340 !important; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background-color: #ffffff;
    border-bottom: 2px solid #d1d5db;
    gap: 0;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Inter', sans-serif;
    font-size: 0.8rem;
    font-weight: 500;
    letter-spacing: 0.03em;
    color: #6b7280;
    padding: 0.75rem 1.4rem;
    background: transparent;
    border: none;
    text-transform: uppercase;
}
.stTabs [aria-selected="true"] {
    color: #1a3a6b !important;
    border-bottom: 2px solid #1a3a6b !important;
    font-weight: 600 !important;
}

/* ── Métricas ── */
div[data-testid="metric-container"] {
    background: #ffffff;
    border: 1px solid #d1d5db;
    border-top: 3px solid #1a3a6b;
    border-radius: 6px;
    padding: 1rem 1.2rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
div[data-testid="metric-container"] label {
    font-size: 0.72rem !important;
    color: #6b7280 !important;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    font-weight: 500 !important;
}
div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
    font-size: 1.8rem !important;
    font-weight: 700 !important;
    color: #1a3a6b !important;
}

/* ── Dataframe ── */
.stDataFrame {
    border: 1px solid #d1d5db !important;
    border-radius: 6px;
    background: #ffffff;
}

/* ── Botones ── */
.stButton > button {
    background-color: #1a3a6b;
    color: #ffffff;
    border: none;
    border-radius: 5px;
    font-weight: 600;
    font-size: 0.85rem;
    padding: 0.55rem 1.2rem;
    transition: background 0.2s;
}
.stButton > button:hover {
    background-color: #15305a;
    color: #ffffff;
}

/* ── Inputs / Sliders ── */
.stSlider [data-testid="stSlider"] > div > div { background: #1a3a6b; }
.stRadio label { font-size: 0.88rem; color: #374151; }

/* ── Clases reutilizables ── */
.section-header {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #1a3a6b;
    margin-bottom: 0.5rem;
    padding-bottom: 0.25rem;
    border-bottom: 1px solid #e5e7eb;
}
.info-box {
    background: #eef2fb;
    border-left: 3px solid #1a3a6b;
    padding: 1rem 1.2rem;
    border-radius: 0 6px 6px 0;
    margin: 1rem 0;
    font-size: 0.88rem;
    color: #374151;
    line-height: 1.6;
}
.warn-box {
    background: #fffbeb;
    border-left: 3px solid #d97706;
    padding: 1rem 1.2rem;
    border-radius: 0 6px 6px 0;
    margin: 1rem 0;
    font-size: 0.88rem;
    color: #374151;
    line-height: 1.6;
}
.risk-badge {
    display: inline-block;
    padding: 0.2rem 0.65rem;
    border-radius: 4px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.04em;
}
.risk-low    { background: #dcfce7; color: #166534; border: 1px solid #86efac; }
.risk-medium { background: #fef9c3; color: #854d0e; border: 1px solid #fde047; }
.risk-high   { background: #fee2e2; color: #991b1b; border: 1px solid #fca5a5; }

hr { border-color: #e5e7eb; }
</style>
"""
