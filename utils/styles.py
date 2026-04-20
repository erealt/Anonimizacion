CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;700&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
h1, h2, h3 { font-family: 'Space Mono', monospace !important; }
.stApp { background-color: #0d0f14; color: #e8eaf0; }
section[data-testid="stSidebar"] { background-color: #12151c; border-right: 1px solid #1e2330; }
.block-container { padding-top: 2rem; }
div[data-testid="metric-container"] { background: #12151c; border: 1px solid #1e2330; border-radius: 8px; padding: 1rem 1.2rem; }
div[data-testid="metric-container"] label { font-family: 'Space Mono', monospace !important; font-size: 0.7rem !important; color: #6b7280 !important; letter-spacing: 0.08em; text-transform: uppercase; }
div[data-testid="metric-container"] div[data-testid="stMetricValue"] { font-family: 'Space Mono', monospace !important; font-size: 1.8rem !important; color: #00e5a0 !important; }
.stDataFrame { border: 1px solid #1e2330 !important; border-radius: 8px; }
.stTabs [data-baseweb="tab-list"] { background-color: #12151c; border-bottom: 1px solid #1e2330; gap: 0; }
.stTabs [data-baseweb="tab"] { font-family: 'Space Mono', monospace; font-size: 0.75rem; letter-spacing: 0.05em; color: #6b7280; padding: 0.7rem 1.5rem; background: transparent; border: none; }
.stTabs [aria-selected="true"] { color: #00e5a0 !important; border-bottom: 2px solid #00e5a0 !important; }
.risk-badge { display: inline-block; padding: 0.25rem 0.75rem; border-radius: 4px; font-family: 'Space Mono', monospace; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.05em; }
.risk-low    { background: #0d2e1f; color: #00e5a0; border: 1px solid #00e5a0; }
.risk-medium { background: #2e2500; color: #f5a623; border: 1px solid #f5a623; }
.risk-high   { background: #2e0d0d; color: #ff4d4d; border: 1px solid #ff4d4d; }
.info-box { background: #12151c; border-left: 3px solid #00e5a0; padding: 1rem 1.2rem; border-radius: 0 8px 8px 0; margin: 1rem 0; font-size: 0.88rem; color: #a0aec0; line-height: 1.6; }
.warn-box { background: #1a1400; border-left: 3px solid #f5a623; padding: 1rem 1.2rem; border-radius: 0 8px 8px 0; margin: 1rem 0; font-size: 0.88rem; color: #a0aec0; line-height: 1.6; }
.section-header { font-family: 'Space Mono', monospace; font-size: 0.7rem; letter-spacing: 0.15em; text-transform: uppercase; color: #00e5a0; margin-bottom: 0.5rem; }
hr { border-color: #1e2330; }
</style>
"""
