import pandas as pd
import streamlit as st

from utils.loader import carga_automatica
from utils.detector import sugerir_qi_y_sensibles


def render():
    st.markdown("<div class='section-header'>Importar datos</div>", unsafe_allow_html=True)
    st.markdown("""
    <div class='info-box'>
    Sube uno o varios ficheros y la app detectará automáticamente el formato.<br><br>
    <strong>Formatos soportados:</strong> CSV · JSON · XML · Excel · DAT/TXT/ASC (ASCII fijo)<br>
    <strong>Para microdatos del INE</strong> (ASCII fijo): sube el <code>.dat</code>/<code>.txt</code>
    <em>y</em> el Excel de diseño de registro a la vez y se procesarán solos.
    </div>""", unsafe_allow_html=True)

    ficheros_subidos = st.file_uploader(
        "Arrastra aquí tu(s) fichero(s)",
        accept_multiple_files=True,
        type=None,
        key="auto_upload",
    )

    if ficheros_subidos:
        with st.spinner("Detectando formato y cargando datos..."):
            df_cargado, etiqueta_fuente, metodo, error = carga_automatica(ficheros_subidos)

        if error:
            st.error(f"❌ {error}")
        else:
            st.success(f"✅ **{len(df_cargado)} registros · {len(df_cargado.columns)} columnas**")
            st.markdown(f"""
            <div class='info-box'>
            📂 <strong>Fichero:</strong> {etiqueta_fuente}<br>
            🔍 <strong>Método de carga:</strong> {metodo}
            </div>""", unsafe_allow_html=True)

            primera_carga = "df" not in st.session_state
            st.session_state["df"] = df_cargado
            st.session_state["fuente"] = etiqueta_fuente
            qi_automatico, sensible_automatico = sugerir_qi_y_sensibles(df_cargado)

            columna1, columna2 = st.columns(2)
            with columna1:
                st.markdown("<div class='section-header'>Vista previa</div>", unsafe_allow_html=True)
                st.dataframe(df_cargado.head(10), use_container_width=True)
            with columna2:
                st.markdown("<div class='section-header'>Sugerencia de columnas</div>", unsafe_allow_html=True)
                st.dataframe(pd.DataFrame({
                    "Columna":        df_cargado.columns,
                    "Tipo":           df_cargado.dtypes.astype(str).values,
                    "Valores únicos": [df_cargado[c].nunique() for c in df_cargado.columns],
                    "Sugerencia":     ["🔑 Cuasi-ID" if c in qi_automatico else "🔒 Sensible" for c in df_cargado.columns],
                }), use_container_width=True)

            if etiqueta_fuente and not etiqueta_fuente.startswith("CSV"):
                bytes_csv = df_cargado.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "⬇ Descargar dataset convertido como CSV",
                    bytes_csv,
                    file_name="dataset_convertido.csv",
                    mime="text/csv",
                )

            st.markdown("---")
            st.markdown("<div class='section-header'>Configura las columnas para este dataset</div>", unsafe_allow_html=True)
            columna_a, columna_b = st.columns(2)
            with columna_a:
                qi_seleccionado = st.multiselect(
                    "Cuasi-identificadores (QI)",
                    df_cargado.columns.tolist(),
                    default=qi_automatico[:min(5, len(qi_automatico))],
                    key="qi_auto",
                )
            with columna_b:
                indice_defecto = df_cargado.columns.tolist().index(sensible_automatico[0]) if sensible_automatico else 0
                sensible_seleccionado = st.selectbox(
                    "Atributo sensible",
                    df_cargado.columns.tolist(),
                    index=indice_defecto,
                    key="sens_auto",
                )
            st.session_state["columnas_qi"] = qi_seleccionado
            st.session_state["columna_sensible"] = sensible_seleccionado
            st.info("✅ Configuración guardada. Continúa en las pestañas siguientes.")

            # Forzar un rerun solo en la primera carga para que el sidebar
            # se desbloquee inmediatamente (lee session_state antes que este tab)
            if primera_carga:
                st.rerun()
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
