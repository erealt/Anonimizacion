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
    if not ficheros_subidos and "df" in st.session_state:
        st.markdown(f"""
        <div style="
            background: #ffffff;
            border: 1.5px solid #22c55e88;
            border-radius: 12px;
            padding: 16px 20px;
            margin: 12px 0;
            display: flex; align-items: center; gap: 14px;
        ">
            <div style="font-size:24px;">✅</div>
            <div>
                <div style="color:#22c55e; font-size:14px; font-weight:700; margin-bottom:4px;">
                    Dataset ya cargado
                </div>
                <div style="color:#374151; font-size:13px;">
                    📂 {st.session_state['fuente']} ·
                    {len(st.session_state['df'])} registros ·
                    {len(st.session_state['df'].columns)} columnas
                </div>
                <div style="color:#6b7280; font-size:12px; margin-top:4px;">
                    Puedes continuar en las otras pestañas o subir un fichero nuevo.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🗑️ Cargar un fichero diferente"):
            for key in ["df", "fuente", "metodo", "hash_archivos",
                        "nuniques", "qi_sugerido", "sensible_sugerido",
                        "columnas_qi", "columna_sensible"]:
                st.session_state.pop(key, None)
            st.rerun()
        return

    if not ficheros_subidos:
        st.markdown("""
        <div style='text-align:center;padding:3rem 0;color:#6b7280'>
            <div style='font-size:2.5rem;margin-bottom:1rem'>📂</div>
            <div style='font-size:0.8rem;letter-spacing:0.1em'>
                Arrastra aquí tu fichero para comenzar
            </div>
            <div style='font-size:0.75rem;margin-top:0.75rem;color:#9ca3af'>
                CSV · JSON · XML · Excel · DAT · TXT · ASC
            </div>
        </div>""", unsafe_allow_html=True)
        return

    # ── Comprobar si el fichero es nuevo antes de parsear ───────────────
    hash_actual = "-".join(f"{f.name}_{f.size}" for f in ficheros_subidos)

    if st.session_state.get("hash_archivos") != hash_actual:
       
        with st.spinner("Detectando formato y cargando datos..."):
            df_cargado, etiqueta_fuente, metodo, error = carga_automatica(ficheros_subidos)

        if error:
            st.error(f"❌ {error}")
            return

    
        nuniques = {c: int(df_cargado[c].nunique()) for c in df_cargado.columns}
        qi_automatico, sensible_automatico = sugerir_qi_y_sensibles(df_cargado, nuniques)

        st.session_state.update({
            "df":                df_cargado,
            "fuente":            etiqueta_fuente,
            "metodo":            metodo,
            "hash_archivos":     hash_actual,
            "nuniques":          nuniques,
            "qi_sugerido":       qi_automatico,
            "sensible_sugerido": sensible_automatico,
            "columnas_qi":       qi_automatico[:min(5, len(qi_automatico))],
            "columna_sensible":  sensible_automatico[0] if sensible_automatico
                                 else df_cargado.columns[-1],
        })
        st.rerun()  # sincroniza el resto de pestañas con los nuevos datos

    
    df_cargado          = st.session_state["df"]
    etiqueta_fuente     = st.session_state["fuente"]
    metodo              = st.session_state["metodo"]
    nuniques            = st.session_state["nuniques"]
    qi_automatico       = st.session_state["qi_sugerido"]
    sensible_automatico = st.session_state["sensible_sugerido"]

    st.success(f"✅ **{len(df_cargado)} registros · {len(df_cargado.columns)} columnas**")
    st.markdown(f"""
    <div class='info-box'>
    📂 <strong>Fichero:</strong> {etiqueta_fuente}<br>
    🔍 <strong>Método de carga:</strong> {metodo}
    </div>""", unsafe_allow_html=True)

   
    columna1, columna2 = st.columns(2)
    with columna1:
        st.markdown("<div class='section-header'>Vista previa</div>", unsafe_allow_html=True)
        st.dataframe(df_cargado.head(10), use_container_width=True)
    with columna2:
        st.markdown("<div class='section-header'>Sugerencia de columnas</div>", unsafe_allow_html=True)
        st.dataframe(pd.DataFrame({
            "Columna":        df_cargado.columns,
            "Tipo":           df_cargado.dtypes.astype(str).values,
            "Valores únicos": [nuniques[c] for c in df_cargado.columns],
            "Sugerencia":     ["🔑 Cuasi-ID" if c in qi_automatico else "🔒 Sensible"
                               for c in df_cargado.columns],
        }), use_container_width=True)

    if etiqueta_fuente and not etiqueta_fuente.startswith("CSV"):
        bytes_csv = df_cargado.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇ Descargar dataset convertido como CSV",
            bytes_csv,
            file_name="dataset_convertido.csv",
            mime="text/csv",
        )

    # ── Configuración de columnas ────────────────────────────────────────
    st.markdown("---")
    st.markdown("<div class='section-header'>Configura las columnas para este dataset</div>", unsafe_allow_html=True)
    columna_a, columna_b = st.columns(2)

    with columna_a:
        qi_seleccionado = st.multiselect(
            "Cuasi-identificadores (QI)",
            df_cargado.columns.tolist(),
            default=st.session_state["columnas_qi"],
            key="qi_auto",
        )
    with columna_b:
        todas = df_cargado.columns.tolist()
        idx_defecto = todas.index(st.session_state["columna_sensible"]) \
            if st.session_state["columna_sensible"] in todas else 0
        sensible_seleccionado = st.selectbox(
            "Atributo sensible",
            todas,
            index=idx_defecto,
            key="sens_auto",
        )

    # Actualizar session_state solo si el usuario cambió algo
    if (qi_seleccionado       != st.session_state.get("columnas_qi") or
            sensible_seleccionado != st.session_state.get("columna_sensible")):
        st.session_state["columnas_qi"]      = qi_seleccionado
        st.session_state["columna_sensible"] = sensible_seleccionado

    st.info("✅ Configuración guardada. Continúa en el siguiente paso.")

    st.markdown("<br>", unsafe_allow_html=True)
    _, col_btn = st.columns([3, 1])
    with col_btn:
        if st.button("Continuar →", key="continuar_import", use_container_width=True, type="primary"):
            st.session_state["pagina_activa"] = 1
            st.rerun()
