import pandas as pd
import streamlit as st

from utils.loader import auto_load
from utils.detector import suggest_qi_and_sensitive


def render():
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
        key="auto_upload",
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
                    "Sugerencia":     ["🔑 Cuasi-ID" if c in qi_auto else "🔒 Sensible" for c in df_loaded.columns],
                }), use_container_width=True)

            if source_label and not source_label.startswith("CSV"):
                csv_bytes = df_loaded.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "⬇ Descargar dataset convertido como CSV",
                    csv_bytes,
                    file_name="dataset_convertido.csv",
                    mime="text/csv",
                )

            st.markdown("---")
            st.markdown("<div class='section-header'>Configura las columnas para este dataset</div>", unsafe_allow_html=True)
            col_a, col_b = st.columns(2)
            with col_a:
                qi_sel = st.multiselect(
                    "Cuasi-identificadores (QI)",
                    df_loaded.columns.tolist(),
                    default=qi_auto[:min(5, len(qi_auto))],
                    key="qi_auto",
                )
            with col_b:
                default_idx = df_loaded.columns.tolist().index(sens_auto[0]) if sens_auto else 0
                sens_sel = st.selectbox(
                    "Atributo sensible",
                    df_loaded.columns.tolist(),
                    index=default_idx,
                    key="sens_auto",
                )
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
