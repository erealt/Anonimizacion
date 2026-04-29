import streamlit as st
import streamlit.components.v1 as components

from utils.loader import carga_automatica

@st.cache_data
def generar_csv_cacheado(df):
    return df.to_csv(index=False).encode("utf-8")


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

    # ── Dataset ya cargado (uploader vacío pero hay df en sesión) ────────
    if not ficheros_subidos and "df" in st.session_state:
        st.markdown(f"""
        <div style='background:#ffffff;border:1px solid #d1d5db;border-left:4px solid #166534;
                    border-radius:6px;padding:1.1rem 1.4rem;margin:1rem 0;
                    display:flex;align-items:center;gap:1rem;'>
            <div style='font-size:1.4rem;'>✅</div>
            <div>
                <div style='color:#166534;font-size:0.88rem;font-weight:600;margin-bottom:0.2rem;'>
                    Dataset cargado
                </div>
                <div style='color:#374151;font-size:0.85rem;'>
                    📂 {st.session_state['fuente']} ·
                    {len(st.session_state['df'])} registros ·
                    {len(st.session_state['df'].columns)} columnas
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Cargar un fichero diferente"):
            for key in ["df", "fuente", "metodo", "hash_archivos",
                        "nuniques", "columnas_qi", "columna_sensible"]:
                st.session_state.pop(key, None)
            st.session_state["abrir_dialogo"] = True
            st.rerun()
        return

    # ── Sin fichero ──────────────────────────────────────────────────────
    if not ficheros_subidos:
        # Si venimos de "Cargar un fichero diferente", abrir el diálogo automáticamente
        if st.session_state.pop("abrir_dialogo", False):
            components.html("""
                <script>
                    setTimeout(function() {
                        const inputs = window.parent.document.querySelectorAll('input[type="file"]');
                        if (inputs.length > 0) inputs[0].click();
                    }, 300);
                </script>
            """, height=0)
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

    # ── Parsear solo si el fichero es nuevo ──────────────────────────────
    hash_actual = "-".join(f"{f.name}_{f.size}" for f in ficheros_subidos)

    if st.session_state.get("hash_archivos") != hash_actual:
        with st.spinner("Detectando formato y cargando datos..."):
            df_cargado, etiqueta_fuente, metodo, error = carga_automatica(ficheros_subidos)

        if error:
            st.error(f"❌ {error}")
            return

        st.session_state.update({
            "df":            df_cargado,
            "fuente":        etiqueta_fuente,
            "metodo":        metodo,
            "hash_archivos": hash_actual,
            # Resetear selección manual al cargar nuevo fichero
            "columnas_qi":       [],
            "columna_sensible":  None,
        })
        st.rerun()

    # ── Datos ya en sesión ───────────────────────────────────────────────
    df_cargado      = st.session_state["df"]
    etiqueta_fuente = st.session_state["fuente"]
    metodo          = st.session_state["metodo"]
    todas           = df_cargado.columns.tolist()

    st.success(f"✅ **{len(df_cargado)} registros · {len(df_cargado.columns)} columnas**")
    st.markdown(f"""
    <div class='info-box'>
    📂 <strong>Fichero:</strong> {etiqueta_fuente}<br>
    🔍 <strong>Método de carga:</strong> {metodo}
    </div>""", unsafe_allow_html=True)

    # ── Vista previa ─────────────────────────────────────────────────────
    st.markdown("<div class='section-header'>Vista previa</div>", unsafe_allow_html=True)
    st.dataframe(df_cargado.head(10), use_container_width=True)

    if etiqueta_fuente and not etiqueta_fuente.startswith("CSV"):
        bytes_csv = generar_csv_cacheado(df_cargado)
        st.download_button(
            "⬇ Descargar dataset convertido como CSV",
            bytes_csv,
            file_name="dataset_convertido.csv",
            mime="text/csv",
        )

    # ── Selección manual de columnas ─────────────────────────────────────
    st.markdown("---")
    st.markdown("<div class='section-header'>Selección de columnas</div>", unsafe_allow_html=True)

    col_a, col_b = st.columns(2)

    with col_a:
        qi_seleccionado = st.multiselect(
            "Cuasi-identificadores (QI)",
            todas,
            default=st.session_state.get("columnas_qi", []),
            placeholder="Selecciona una o varias columnas...",
            key="qi_manual",
        )
    with col_b:
        idx_defecto = todas.index(st.session_state["columna_sensible"]) \
            if st.session_state.get("columna_sensible") in todas else None
        sensible_seleccionado = st.selectbox(
            "Atributo sensible",
            [None] + todas,
            index=0 if idx_defecto is None else idx_defecto + 1,
            format_func=lambda x: "Selecciona una columna..." if x is None else x,
            key="sens_manual",
        )

    # Guardar en sesión cuando el usuario selecciona
    st.session_state["columnas_qi"]      = qi_seleccionado
    st.session_state["columna_sensible"] = sensible_seleccionado

    # ── Botón continuar (solo si hay selección mínima) ───────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    listo = bool(qi_seleccionado) and sensible_seleccionado is not None
    _, col_btn = st.columns([3, 1])
    with col_btn:
        if st.button(
            "Continuar →",
            key="continuar_import",
            use_container_width=True,
            type="primary",
            disabled=not listo,
        ):
            st.session_state["pagina_activa"] = 1
            st.rerun()

    if not listo:
        st.caption("Selecciona al menos un cuasi-identificador y un atributo sensible para continuar.")
