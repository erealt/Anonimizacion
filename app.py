import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io

st.set_page_config(page_title="AnonRisk · Prototipo TFG", page_icon="🔒", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
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
""", unsafe_allow_html=True)

# ── SIDEBAR ──
with st.sidebar:
    st.markdown("## 🔒 AnonRisk")
    st.markdown("<p style='color:#6b7280;font-size:0.8rem'>Prototipo TFG · Anonimización y Riesgo de Reidentificación</p>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<div class='section-header'>Técnica de anonimización</div>", unsafe_allow_html=True)
    technique = st.radio("", ["K-Anonimato", "L-Diversidad", "Privacidad Diferencial"], label_visibility="collapsed")
    st.markdown("---")
    st.markdown("<div class='section-header'>Parámetros</div>", unsafe_allow_html=True)
    if technique == "K-Anonimato":
        k = st.slider("Valor de k", 2, 20, 3); l, epsilon, sensitivity = 2, 1.0, 1.0
    elif technique == "L-Diversidad":
        k = st.slider("Valor de k", 2, 20, 3); l = st.slider("Valor de l", 2, 10, 2); epsilon, sensitivity = 1.0, 1.0
    else:
        epsilon = st.slider("Epsilon (ε)", 0.01, 5.0, 1.0, step=0.01); sensitivity = st.slider("Sensibilidad (Δf)", 0.1, 10.0, 1.0, step=0.1); k, l = 3, 2
    st.markdown("---")
    run = st.button("▶ Aplicar anonimización", use_container_width=True)

# ── HELPERS: DETECCIÓN ──
QI_KEYWORDS = ["edad","age","sexo","sex","genero","cp","postal","municipio","provincia","region","comunidad","pais","nacionalidad","estudios","educacion","ocupacion","empleo","civil","EDAD","SEXO","CCAA","PROVRES","ESTUDIOS","ECIVIL"]
SENSITIVE_KEYWORDS = ["diagnostico","enfermedad","patologia","medicacion","medicamento","tratamiento","ingreso","salud","health","disease","diagnosis","DIAG","ENFER","MEDIC","TRATA"]

def suggest_qi_and_sensitive(df):
    cols = df.columns.tolist()
    qi, sens = [], []
    for col in cols:
        cl = col.lower()
        if any(kw.lower() in cl for kw in SENSITIVE_KEYWORDS): sens.append(col)
        elif any(kw.lower() in cl for kw in QI_KEYWORDS): qi.append(col)
        elif df[col].dtype == object or df[col].nunique() < 25: qi.append(col)
        else: sens.append(col)
    if not sens and cols: sens = [cols[-1]]
    return qi, sens

def decode_bytes(content):
    for enc in ["utf-8", "latin-1", "cp1252"]:
        try: return content.decode(enc), enc
        except UnicodeDecodeError: continue
    return None, None

def detect_separator(text):
    for sep, nombre in [(",","coma"),(";","punto y coma"),("\t","tabulador"),("|","pipe")]:
        try:
            df_try = pd.read_csv(io.StringIO(text), sep=sep, engine="python", nrows=5)
            if len(df_try.columns) > 1: return sep, nombre
        except Exception: continue
    return None, None

def parse_ine_design(design_file):
    try:
        xl = pd.ExcelFile(design_file)
        raw = xl.parse(xl.sheet_names[0], header=None)
        header_row = 0
        for i, row in raw.iterrows():
            row_str = " ".join(str(v).lower() for v in row.values)
            if any(w in row_str for w in ["inicio","posici","variable","nombre"]):
                header_row = i; break
        df_d = xl.parse(xl.sheet_names[0], header=header_row)
        df_d.columns = [str(c).strip().lower() for c in df_d.columns]
        df_d = df_d.dropna(how="all")
        col_map = {}
        for col in df_d.columns:
            if any(w in col for w in ["nombre","variable","name"]): col_map["name"] = col
            elif any(w in col for w in ["inicio","start","pos_ini"]): col_map["start"] = col
            elif any(w in col for w in ["fin","end","pos_fin","final"]): col_map["end"] = col
            elif any(w in col for w in ["longitud","length","ancho","tam"]): col_map["length"] = col
            elif any(w in col for w in ["descrip","etiqueta","label"]): col_map["desc"] = col
        if "name" not in col_map or "start" not in col_map:
            return None, "No se encontraron columnas de nombre/posición en el diseño."
        variables = []
        for _, row in df_d.iterrows():
            name = str(row[col_map["name"]]).strip()
            if not name or name.lower() in ["nan","variable","nombre"]: continue
            try: start = int(float(row[col_map["start"]])) - 1
            except: continue
            if "end" in col_map:
                try: end = int(float(row[col_map["end"]]))
                except: end = start + 1
            elif "length" in col_map:
                try: end = start + int(float(row[col_map["length"]]))
                except: end = start + 1
            else: end = start + 1
            desc = str(row[col_map["desc"]]).strip() if "desc" in col_map else ""
            variables.append({"name": name, "start": start, "end": end, "description": desc})
        return variables, None
    except Exception as e:
        return None, f"Error leyendo diseño: {e}"

def parse_ine_microdata(txt_file, variables):
    try:
        content = txt_file.read() if hasattr(txt_file, "read") else open(txt_file, "rb").read()
        text, enc = decode_bytes(content)
        if text is None: return None, "No se pudo decodificar el fichero."
        lines = [l.rstrip("\n").rstrip("\r") for l in text.splitlines() if l.strip()]
        records = []
        for line in lines:
            record = {}
            for var in variables:
                record[var["name"]] = line[var["start"]:var["end"]].strip() if var["end"] <= len(line) else ""
            records.append(record)
        df = pd.DataFrame(records)
        for col in df.columns:
            try: df[col] = pd.to_numeric(df[col])
            except: pass
        return df, None
    except Exception as e:
        return None, f"Error parseando microdatos: {e}"

def auto_load(files):
    """Detecta automáticamente el formato y carga los ficheros."""
    if not files: return None, None, None, None

    ext_map = {}
    for f in files:
        ext = f.name.rsplit(".", 1)[-1].lower() if "." in f.name else "sin_ext"
        ext_map[ext] = f

    # CSV
    if "csv" in ext_map:
        f = ext_map["csv"]
        try:
            content = f.read(); text, enc = decode_bytes(content)
            sep, sep_nombre = detect_separator(text)
            df = pd.read_csv(io.StringIO(text), sep=sep or ",", engine="python")
            return df, f"CSV · {f.name}", f"CSV (separador: {sep_nombre or 'coma'}, codificación: {enc})", None
        except Exception as e: return None, None, None, f"Error leyendo CSV: {e}"

    # Excel tabular (solo 1 fichero)
    if "xlsx" in ext_map and len(files) == 1:
        f = ext_map["xlsx"]
        try:
            df = pd.read_excel(f)
            return df, f"Excel · {f.name}", "Excel tabular directo", None
        except Exception as e: return None, None, None, f"Error leyendo Excel: {e}"

    # JSON
    if "json" in ext_map:
        f = ext_map["json"]
        try:
            content = f.read(); text, enc = decode_bytes(content)
            df = pd.read_json(io.StringIO(text))
            return df, f"JSON · {f.name}", f"JSON directo (codificación: {enc})", None
        except Exception as e: return None, None, None, f"Error leyendo JSON: {e}"

    # XML
    if "xml" in ext_map:
        f = ext_map["xml"]
        try:
            content = f.read(); text, enc = decode_bytes(content)
            df = pd.read_xml(io.StringIO(text))
            return df, f"XML · {f.name}", f"XML directo (codificación: {enc})", None
        except Exception as e: return None, None, None, f"Error leyendo XML: {e}"

    # ASCII fijo (.dat / .txt / .asc / sin extensión)
    ascii_exts = ["dat", "txt", "asc", "mic", "sin_ext"]
    ascii_file = next((ext_map[e] for e in ascii_exts if e in ext_map), None)

    if ascii_file:
        content = ascii_file.read(); text, enc = decode_bytes(content)
        if text is None: return None, None, None, "No se pudo decodificar el fichero ASCII."

        design_file = ext_map.get("xlsx") or ext_map.get("xls")

        if design_file:
            variables, err = parse_ine_design(design_file)
            if err: return None, None, None, f"Error en diseño de registro: {err}"
            # Resetear posición del fichero
            ascii_file.seek(0)
            df, err2 = parse_ine_microdata(ascii_file, variables)
            if err2: return None, None, None, err2
            return df, f"Microdatos · {ascii_file.name}", f"ASCII ancho fijo + diseño Excel ({len(variables)} variables, codificación: {enc})", None
        else:
            sep, sep_nombre = detect_separator(text)
            if sep:
                try:
                    df = pd.read_csv(io.StringIO(text), sep=sep, engine="python")
                    return df, f"Microdatos · {ascii_file.name}", f"ASCII con separador '{sep_nombre}' detectado (codificación: {enc})", None
                except Exception as e: return None, None, None, f"Error: {e}"
            else:
                return None, None, None, (
                    "⚠️ El fichero parece ser ASCII de ancho fijo sin separadores.\n"
                    "Sube también el **Excel de diseño de registro** junto a este fichero para poder convertirlo."
                )

    return None, None, None, "Formato no reconocido. Formatos soportados: CSV, JSON, XML, Excel, DAT/TXT/ASC (con o sin diseño de registro)."

# ── HELPERS: ANONIMIZACIÓN ──
def generalize_column(series, bins=5):
    if pd.api.types.is_numeric_dtype(series):
        try: return pd.cut(series, bins=bins).astype(str)
        except: return series.astype(str)
    else: return series.astype(str).apply(lambda x: x[:-1]+"*" if len(x)>1 else "*")

def apply_k_anonymity(df, qi_cols, k):
    anon = df.copy()
    for col in qi_cols: anon[col] = generalize_column(anon[col])
    sizes = anon.groupby(qi_cols, dropna=False).transform("count").iloc[:,0]
    return anon[sizes >= k].reset_index(drop=True)

def apply_l_diversity(df, qi_cols, sensitive_col, k, l):
    anon = df.copy()
    for col in qi_cols: anon[col] = generalize_column(anon[col])
    return anon.groupby(qi_cols, group_keys=False, dropna=False).filter(
        lambda g: len(g) >= k and g[sensitive_col].nunique() >= l).reset_index(drop=True)

def apply_differential_privacy(df, epsilon, sensitivity):
    anon = df.copy(); scale = sensitivity / epsilon
    for col in df.select_dtypes(include=[np.number]).columns:
        anon[col] = anon[col] + np.random.laplace(0, scale, len(df))
    return anon

# ── HELPERS: MÉTRICAS ──
def compute_prosecutor_risk(df, qi_cols):
    if not qi_cols: return 0.0
    return float((1/df.groupby(qi_cols, dropna=False).size()).max())
def compute_journalist_risk(df, qi_cols):
    if not qi_cols: return 0.0
    return float((1/df.groupby(qi_cols, dropna=False).size()).mean())
def compute_marketer_risk(df, qi_cols):
    if not qi_cols: return 0.0
    sizes = df.groupby(qi_cols, dropna=False).transform("size")
    return float((sizes==1).sum()/len(df))
def compute_k_value(df, qi_cols):
    if not qi_cols: return len(df)
    return int(df.groupby(qi_cols, dropna=False).size().min())
def risk_label(value):
    if value < 0.2: return "BAJO","risk-low"
    elif value < 0.5: return "MEDIO","risk-medium"
    else: return "ALTO","risk-high"

def render_risk_chart(pr_orig, jr_orig, mr_orig, pr_anon, jr_anon, mr_anon):
    fig, ax = plt.subplots(figsize=(8,3.5))
    fig.patch.set_facecolor("#0d0f14"); ax.set_facecolor("#12151c")
    x = np.arange(3); w = 0.35
    b1 = ax.bar(x-w/2,[pr_orig,jr_orig,mr_orig],w,label="Original",color="#ff4d4d",alpha=0.85)
    b2 = ax.bar(x+w/2,[pr_anon,jr_anon,mr_anon],w,label="Anonimizado",color="#00e5a0",alpha=0.85)
    ax.set_xticks(x); ax.set_xticklabels(["Fiscal","Periodístico","Marketing"],color="#a0aec0",fontsize=10)
    ax.set_ylabel("Riesgo",color="#6b7280",fontsize=9); ax.set_ylim(0,1.1); ax.tick_params(colors="#6b7280")
    for s in ax.spines.values(): s.set_edgecolor("#1e2330")
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    ax.legend(facecolor="#12151c",edgecolor="#1e2330",labelcolor="#a0aec0",fontsize=9)
    for bar,c in zip(list(b1)+list(b2),["#ff4d4d"]*3+["#00e5a0"]*3):
        ax.text(bar.get_x()+bar.get_width()/2,bar.get_height()+0.02,f"{bar.get_height():.1%}",ha="center",va="bottom",color=c,fontsize=8)
    plt.tight_layout(); return fig

# ── MAIN ──
st.markdown("# 🔒 AnonRisk")
st.markdown("<p style='color:#6b7280;margin-top:-1rem;margin-bottom:2rem'>Prototipo de anonimización y evaluación de riesgo residual de reidentificación</p>", unsafe_allow_html=True)

tab0, tab1, tab2, tab3, tab4 = st.tabs(["📥 IMPORTAR DATOS","📊 DATOS ORIGINALES","🔒 DATOS ANONIMIZADOS","📈 MÉTRICAS DE RIESGO","⚖️ COMPARATIVA"])

# ══════════════════════════════════════════════
# TAB 0 — IMPORTAR DATOS (detector automático)
# ══════════════════════════════════════════════
with tab0:
    st.markdown("<div class='section-header'>Importar datos</div>", unsafe_allow_html=True)
    st.markdown("""
    <div class='info-box'>
    Sube uno o varios ficheros y la app detectará automáticamente el formato.<br><br>
    <strong>Formatos soportados:</strong> CSV · JSON · XML · Excel · DAT/TXT/ASC (ASCII fijo)<br>
    <strong>Para microdatos del INE</strong> (ASCII fijo): sube el <code>.dat</code>/<code>.txt</code> 
    <em>y</em> el Excel de diseño de registro a la vez y se procesarán solos.
    </div>""", unsafe_allow_html=True)

    uploaded_files = st.file_uploader(
        "Arrastra aquí tu(s) fichero(s)",
        accept_multiple_files=True,
        type=None,
        key="auto_upload"
    )

    if uploaded_files:
        with st.spinner("Detectando formato y cargando datos..."):
            df_loaded, source_label, metodo, error = auto_load(uploaded_files)

        if error:
            st.error(f"❌ {error}")
        else:
            st.success(f"✅ **{len(df_loaded)} registros · {len(df_loaded.columns)} columnas**")
            st.markdown(f"""
            <div class='info-box'>
            📂 <strong>Fichero:</strong> {source_label}<br>
            🔍 <strong>Método de carga:</strong> {metodo}
            </div>""", unsafe_allow_html=True)

            st.session_state["df"] = df_loaded
            st.session_state["source"] = source_label
            qi_auto, sens_auto = suggest_qi_and_sensitive(df_loaded)

            c1, c2 = st.columns(2)
            with c1:
                st.markdown("<div class='section-header'>Vista previa</div>", unsafe_allow_html=True)
                st.dataframe(df_loaded.head(10), use_container_width=True)
            with c2:
                st.markdown("<div class='section-header'>Sugerencia de columnas</div>", unsafe_allow_html=True)
                st.dataframe(pd.DataFrame({
                    "Columna":        df_loaded.columns,
                    "Tipo":           df_loaded.dtypes.astype(str).values,
                    "Valores únicos": [df_loaded[c].nunique() for c in df_loaded.columns],
                    "Sugerencia":     ["🔑 Cuasi-ID" if c in qi_auto else "🔒 Sensible" for c in df_loaded.columns]
                }), use_container_width=True)

            # Descargar como CSV si el formato original no era CSV
            if source_label and not source_label.startswith("CSV"):
                csv_bytes = df_loaded.to_csv(index=False).encode("utf-8")
                st.download_button("⬇ Descargar dataset convertido como CSV", csv_bytes,
                                   file_name="dataset_convertido.csv", mime="text/csv")

            st.markdown("---")
            st.markdown("<div class='section-header'>Configura las columnas para este dataset</div>", unsafe_allow_html=True)
            col_a, col_b = st.columns(2)
            with col_a:
                qi_sel = st.multiselect("Cuasi-identificadores (QI)", df_loaded.columns.tolist(),
                                        default=qi_auto[:min(5, len(qi_auto))], key="qi_auto")
            with col_b:
                default_idx = df_loaded.columns.tolist().index(sens_auto[0]) if sens_auto else 0
                sens_sel = st.selectbox("Atributo sensible", df_loaded.columns.tolist(),
                                        index=default_idx, key="sens_auto")
            st.session_state["qi_cols"] = qi_sel
            st.session_state["sensitive_col"] = sens_sel
            st.info("✅ Configuración guardada. Continúa en las pestañas siguientes.")
    else:
        st.markdown("""
        <div style='text-align:center;padding:3rem 0;color:#6b7280'>
            <div style='font-size:2.5rem;margin-bottom:1rem'>📂</div>
            <div style='font-family:Space Mono,monospace;font-size:0.8rem;letter-spacing:0.1em'>
                Arrastra aquí tu fichero para comenzar
            </div>
            <div style='font-size:0.75rem;margin-top:0.75rem;color:#4b5563'>
                CSV · JSON · XML · Excel · DAT · TXT · ASC
            </div>
        </div>""", unsafe_allow_html=True)

# ── Estado sesión ──
df            = st.session_state.get("df", None)
qi_cols       = st.session_state.get("qi_cols", [])
sensitive_col = st.session_state.get("sensitive_col", "")
source        = st.session_state.get("source", "")

# ══════════════════════════════════════════════
# TAB 1 — DATOS ORIGINALES
# ══════════════════════════════════════════════
with tab1:
    if df is None:
        st.info("👈 Ve a la pestaña **📥 IMPORTAR DATOS** para cargar un dataset.")
    else:
        st.markdown(f"<div class='section-header'>{source} · {len(df)} registros · {len(df.columns)} columnas</div>", unsafe_allow_html=True)
        st.dataframe(df, use_container_width=True, height=350)
        c1,c2,c3 = st.columns(3)
        c1.metric("Registros", len(df)); c2.metric("Columnas", len(df.columns)); c3.metric("Cuasi-identificadores", len(qi_cols))
        if qi_cols:
            st.markdown("---")
            st.markdown("<div class='section-header'>Riesgo base (sin anonimizar)</div>", unsafe_allow_html=True)
            r1,r2,r3 = st.columns(3)
            r1.metric("Riesgo Fiscal", f"{compute_prosecutor_risk(df,qi_cols):.2%}")
            r2.metric("Riesgo Periodístico", f"{compute_journalist_risk(df,qi_cols):.2%}")
            r3.metric("Riesgo Marketing", f"{compute_marketer_risk(df,qi_cols):.2%}")

# ══════════════════════════════════════════════
# TAB 2 — DATOS ANONIMIZADOS
# ══════════════════════════════════════════════
with tab2:
    if df is None: st.info("👈 Ve a la pestaña **📥 IMPORTAR DATOS** para cargar un dataset.")
    elif not run: st.info("Configura los parámetros en el panel lateral y pulsa **▶ Aplicar anonimización**.")
    else:
        with st.spinner("Aplicando anonimización..."):
            try:
                if technique == "K-Anonimato": anon_df = apply_k_anonymity(df,qi_cols,k); params_str=f"k={k}"
                elif technique == "L-Diversidad": anon_df = apply_l_diversity(df,qi_cols,sensitive_col,k,l); params_str=f"k={k}, l={l}"
                else: anon_df = apply_differential_privacy(df,epsilon,sensitivity); params_str=f"ε={epsilon}, Δf={sensitivity}"
                st.session_state["anon_df"]=anon_df; st.session_state["technique"]=technique; st.session_state["params_str"]=params_str
            except Exception as e: st.error(f"Error: {e}"); st.stop()
        st.markdown(f"<div class='section-header'>{technique} · {params_str} · {len(anon_df)} registros retenidos</div>", unsafe_allow_html=True)
        st.dataframe(anon_df, use_container_width=True, height=350)
        c1,c2,c3 = st.columns(3)
        c1.metric("Registros retenidos", len(anon_df))
        c2.metric("Retención", f"{len(anon_df)/len(df)*100:.1f}%")
        c3.metric("Eliminados", len(df)-len(anon_df))
        st.download_button("⬇ Descargar dataset anonimizado", anon_df.to_csv(index=False).encode("utf-8"), file_name="dataset_anonimizado.csv", mime="text/csv")

# ══════════════════════════════════════════════
# TAB 3 — MÉTRICAS DE RIESGO
# ══════════════════════════════════════════════
with tab3:
    if df is None: st.info("👈 Ve a la pestaña **📥 IMPORTAR DATOS** para cargar un dataset.")
    elif "anon_df" not in st.session_state: st.info("Aplica primero una técnica de anonimización.")
    else:
        anon_df = st.session_state["anon_df"]; technique = st.session_state.get("technique", technique)
        pr_orig=compute_prosecutor_risk(df,qi_cols); jr_orig=compute_journalist_risk(df,qi_cols); mr_orig=compute_marketer_risk(df,qi_cols)
        if technique != "Privacidad Diferencial" and qi_cols:
            pr_anon=compute_prosecutor_risk(anon_df,qi_cols); jr_anon=compute_journalist_risk(anon_df,qi_cols)
            mr_anon=compute_marketer_risk(anon_df,qi_cols); k_val=compute_k_value(anon_df,qi_cols)
        else:
            pr_anon=min(1.0,epsilon/10); jr_anon=min(1.0,epsilon/15); mr_anon=0.0; k_val=None
        st.markdown("<div class='section-header'>Métricas de riesgo de reidentificación</div>", unsafe_allow_html=True)
        col1,col2,col3,col4 = st.columns(4)
        col1.metric("Riesgo Fiscal", f"{pr_anon:.2%}", delta=f"{pr_anon-pr_orig:.2%}", delta_color="inverse")
        col2.metric("Riesgo Periodístico", f"{jr_anon:.2%}", delta=f"{jr_anon-jr_orig:.2%}", delta_color="inverse")
        col3.metric("Riesgo Marketing", f"{mr_anon:.2%}", delta=f"{mr_anon-mr_orig:.2%}", delta_color="inverse")
        if k_val is not None: col4.metric("k efectivo", k_val)
        st.markdown("---")
        st.markdown("<div class='section-header'>Nivel de riesgo residual</div>", unsafe_allow_html=True)
        bc1,bc2,bc3 = st.columns(3)
        for col_ui,val,label in zip([bc1,bc2,bc3],[pr_anon,jr_anon,mr_anon],["Fiscal","Periodístico","Marketing"]):
            rl,rc = risk_label(val)
            col_ui.markdown(f"<div style='text-align:center;margin-top:0.5rem'><div style='color:#6b7280;font-size:0.75rem;margin-bottom:0.3rem'>{label}</div><span class='risk-badge {rc}'>{rl}</span></div>", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("<div class='section-header'>Comparativa visual</div>", unsafe_allow_html=True)
        st.pyplot(render_risk_chart(pr_orig,jr_orig,mr_orig,pr_anon,jr_anon,mr_anon))

# ══════════════════════════════════════════════
# TAB 4 — COMPARATIVA
# ══════════════════════════════════════════════
with tab4:
    if df is None: st.info("👈 Ve a la pestaña **📥 IMPORTAR DATOS** para cargar un dataset.")
    elif not qi_cols: st.warning("Selecciona al menos un cuasi-identificador.")
    else:
        st.markdown("<div class='section-header'>Comparativa entre técnicas</div>", unsafe_allow_html=True)
        st.markdown("<div class='info-box'>Simula las tres técnicas con parámetros estándar para comparar privacidad vs utilidad.</div>", unsafe_allow_html=True)
        with st.spinner("Calculando..."):
            try:
                df_k=apply_k_anonymity(df,qi_cols,3); df_l=apply_l_diversity(df,qi_cols,sensitive_col,3,2)
                results = {
                    "K-Anonimato (k=3)":       {"Retención (%)":len(df_k)/len(df)*100,"Riesgo Fiscal":compute_prosecutor_risk(df_k,qi_cols),"Riesgo Periodístico":compute_journalist_risk(df_k,qi_cols),"k efectivo":compute_k_value(df_k,qi_cols)},
                    "L-Diversidad (k=3,l=2)":  {"Retención (%)":len(df_l)/len(df)*100,"Riesgo Fiscal":compute_prosecutor_risk(df_l,qi_cols),"Riesgo Periodístico":compute_journalist_risk(df_l,qi_cols),"k efectivo":compute_k_value(df_l,qi_cols)},
                    "Priv. Diferencial (ε=1)": {"Retención (%)":100.0,"Riesgo Fiscal":0.10,"Riesgo Periodístico":0.067,"k efectivo":"N/A"},
                }
                comp_df = pd.DataFrame(results).T
                st.dataframe(comp_df.style.format({"Retención (%)":"{:.1f}%","Riesgo Fiscal":"{:.2%}","Riesgo Periodístico":"{:.2%}"}), use_container_width=True)
                st.markdown("---")
                fig2,axes = plt.subplots(1,2,figsize=(10,3.5)); fig2.patch.set_facecolor("#0d0f14")
                techs=list(results.keys()); colors=["#4da6ff","#f5a623","#00e5a0"]
                for ax_i,key,title in zip(axes,["Riesgo Fiscal","Retención (%)"],["Riesgo Fiscal","Retención de datos (%)"]):
                    ax_i.set_facecolor("#12151c"); vals=[results[t][key] for t in techs]
                    bars=ax_i.bar(range(len(techs)),vals,color=colors,alpha=0.85,width=0.5)
                    ax_i.set_xticks(range(len(techs))); ax_i.set_xticklabels([t.split(" ")[0] for t in techs],color="#a0aec0",fontsize=9)
                    ax_i.set_title(title,color="#a0aec0",fontsize=10); ax_i.set_ylim(0,max(vals)*1.3+0.01)
                    ax_i.spines["top"].set_visible(False); ax_i.spines["right"].set_visible(False)
                    for s in ax_i.spines.values(): s.set_edgecolor("#1e2330")
                    ax_i.tick_params(colors="#6b7280")
                    for bar,val in zip(bars,vals):
                        ax_i.text(bar.get_x()+bar.get_width()/2,bar.get_height()+max(vals)*0.02,
                                  f"{val:.1%}" if key=="Riesgo Fiscal" else f"{val:.1f}%",ha="center",va="bottom",color="white",fontsize=8)
                plt.tight_layout(); st.pyplot(fig2)
            except Exception as e: st.error(f"Error: {e}")