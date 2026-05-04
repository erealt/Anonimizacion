import streamlit as st
from utils.anonimizacion import k_anonimicidad, l_diversidad, privacidad_diferencial
from utils.exporter import FORMATOS, exportar

COLOR_PRIMARY = "#1a3a6b"
COLOR_BORDER  = "#d1d5db"
COLOR_TEXT    = "#1a2340"
COLOR_MUTED   = "#6b7280"
COLOR_WARN_BG = "#fffbeb"
COLOR_WARN_BD = "#d97706"


def render():
    df               = st.session_state.get("df", None)
    columnas_qi      = st.session_state.get("columnas_qi", [])
    columna_sensible = st.session_state.get("columna_sensible", "")

    if df is None:
        st.info("👈 Ve a la pestaña **📥 IMPORTAR DATOS** para cargar un dataset.")
        return

    col_controles, col_resultado = st.columns([1, 2.5])

    with col_controles:
        st.markdown("<div class='section-header'>Técnica de anonimización</div>", unsafe_allow_html=True)
        tecnica = st.radio("", ["K-Anonimidad", "L-Diversidad", "Privacidad Diferencial"], label_visibility="collapsed")
        st.markdown("---")
        st.markdown("<div class='section-header'>Parámetros</div>", unsafe_allow_html=True)

        if tecnica == "K-Anonimidad":
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

    with col_resultado:
        if not ejecutar and "df_anonimizado" not in st.session_state:
            st.markdown(
                f"""
                <div style='background:{COLOR_WARN_BG};border-left:3px solid {COLOR_WARN_BD};
                            padding:1.2rem 1rem;border-radius:0 6px 6px 0;
                            font-size:0.88rem;color:{COLOR_TEXT};line-height:1.6;margin-top:2rem'>
                ⚙️ Configura los parámetros y pulsa <strong>Aplicar anonimización</strong> para ver el resultado.
                </div>
                """,
                unsafe_allow_html=True,
            )
            return

        if ejecutar:
            if not columnas_qi:
                st.warning("⚠️ Selecciona Cuasi-Identificadores en la pestaña **Importar datos** antes de anonimizar.")
                return

            with st.spinner("Aplicando anonimización..."):
                if tecnica == "K-Anonimidad":
                    df_anon = k_anonimicidad(df, columnas_qi, k)
                elif tecnica == "L-Diversidad":
                    df_anon = l_diversidad(df, columnas_qi, columna_sensible, k, l)
                else:
                    df_anon = privacidad_diferencial(df, epsilon, sensibilidad)

            st.session_state["df_anonimizado"] = df_anon
            st.session_state["tecnica_usada"]  = tecnica

        df_anon      = st.session_state.get("df_anonimizado")
        tecnica_usada = st.session_state.get("tecnica_usada", tecnica)

        registros_orig = len(df)
        registros_anon = len(df_anon)
        suprimidos     = registros_orig - registros_anon
        retencion      = registros_anon / registros_orig if registros_orig > 0 else 0

        st.markdown(
            f"<div class='section-header'>{tecnica_usada} · {registros_anon} registros · {len(df_anon.columns)} columnas</div>",
            unsafe_allow_html=True,
        )

        c1, c2, c3 = st.columns(3)
        c1.metric("Registros originales", registros_orig)
        c2.metric(
            "Registros anonimizados", registros_anon,
            delta=f"-{suprimidos}" if suprimidos else None,
            delta_color="inverse",
        )
        c3.metric("Retención de datos", f"{retencion:.1%}")

        st.dataframe(df_anon.head(100), use_container_width=True, height=350)
        if len(df_anon) > 100:
            st.caption(f"Vista previa de las primeras 100 filas (total: {registros_anon}).")

        col_fmt, col_dl, col_btn = st.columns([1, 2, 1])
        with col_fmt:
            formato = st.selectbox(
                "Formato",
                list(FORMATOS.keys()),
                key="formato_export_anon",
                label_visibility="collapsed",
            )
        with col_dl:
            with st.spinner(f"Generando {formato}..."):
                datos, ext, mime = exportar(df_anon, formato)
            st.download_button(
                f"⬇ Descargar datos anonimizados (.{ext})",
                datos,
                file_name=f"datos_anonimizados.{ext}",
                mime=mime,
                use_container_width=True,
            )
        with col_btn:
            if st.button("Ver métricas →", key="continuar_anon", use_container_width=True, type="primary"):
                st.session_state["pagina_activa"] = 3
                st.rerun()