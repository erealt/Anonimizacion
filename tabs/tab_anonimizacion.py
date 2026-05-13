import streamlit as st

from utils.anonimizacion import (
    k_anonimicidad,
    l_diversidad,
    privacidad_diferencial,
)
from utils.exporter import FORMATOS, exportar

# Paleta institucional
COLOR_TEXT = "#1a2340"
COLOR_WARN_BG = "#fffbeb"
COLOR_WARN_BD = "#d97706"


def _resultado_identico(df_original, df_anon):
    """Comprueba si la salida coincide exactamente con la entrada."""
    return df_anon.reset_index(drop=True).equals(df_original.reset_index(drop=True))


def _mensaje_tecnica(tecnica):
    mensajes = {
        "K-Anonimidad": (
            "Agrupa registros parecidos para que cada persona quede mezclada con, "
            "al menos, otras k personas similares."
        ),
        "L-Diversidad": (
            "Ademas de agrupar registros, exige variedad en el dato sensible de cada "
            "grupo para evitar inferencias directas."
        ),
        "Privacidad Diferencial": (
            "Anade ruido matematico a los datos numericos para proteger a cada persona "
            "sin eliminar filas del dataset."
        ),
    }
    return mensajes[tecnica]


def render():
    df = st.session_state.get("df", None)
    columnas_qi = st.session_state.get("columnas_qi", [])
    columna_sensible = st.session_state.get("columna_sensible", "")

    if df is None:
        st.info("Ve a la pestana Importar datos para cargar un dataset.")
        return

    col_controles, col_resultado = st.columns([1, 2.5])

    with col_controles:
        st.markdown("<div class='section-header'>Tecnica de anonimizacion</div>", unsafe_allow_html=True)
        tecnica = st.radio(
            "",
            ["K-Anonimidad", "L-Diversidad", "Privacidad Diferencial"],
            label_visibility="collapsed",
        )
        st.caption(_mensaje_tecnica(tecnica))
        st.markdown("---")
        st.markdown("<div class='section-header'>Parametros</div>", unsafe_allow_html=True)

        if tecnica == "K-Anonimidad":
            k = st.slider(
                "Valor de k",
                2,
                20,
                3,
                help=(
                    "Numero minimo de registros parecidos que debe haber en cada grupo. "
                    "Cuanto mayor sea k, mayor privacidad, pero tambien menor detalle."
                ),
            )
            supp = st.slider(
                "Supresion maxima (%)",
                5,
                80,
                30,
                step=5,
                help=(
                    "Porcentaje maximo de filas que el sistema puede eliminar si es "
                    "necesario para proteger la privacidad."
                ),
            )
            l, epsilon, sensibilidad = 2, 1.0, 1.0
        elif tecnica == "L-Diversidad":
            k = st.slider(
                "Valor de k",
                2,
                20,
                3,
                help=(
                    "Tamano minimo de cada grupo de registros parecidos. "
                    "Es la base sobre la que despues se aplica la diversidad."
                ),
            )
            l = st.slider(
                "Valor de l",
                2,
                10,
                2,
                help=(
                    "Numero minimo de valores sensibles distintos que debe haber dentro "
                    "de cada grupo."
                ),
            )
            supp = st.slider(
                "Supresion maxima (%)",
                5,
                80,
                30,
                step=5,
                help=(
                    "Porcentaje maximo de filas que el sistema puede eliminar para "
                    "alcanzar el nivel de privacidad solicitado."
                ),
            )
            epsilon, sensibilidad = 1.0, 1.0
        else:
            epsilon = st.slider(
                "Epsilon",
                0.01,
                5.0,
                1.0,
                step=0.01,
                help=(
                    "Controla cuanto ruido se anade. Un valor menor da mas privacidad, "
                    "pero tambien menos precision."
                ),
            )
            sensibilidad = st.slider(
                "Sensibilidad",
                0.1,
                10.0,
                1.0,
                step=0.1,
                help=(
                    "Indica cuanto puede influir un solo registro en el resultado. "
                    "A mayor sensibilidad, mas ruido se necesita."
                ),
            )
            k, l, supp = 3, 2, 30

        st.markdown("---")
        ejecutar = st.button("Aplicar anonimización", use_container_width=True)

    with col_resultado:
        if not ejecutar and "df_anonimizado" not in st.session_state:
            st.markdown(
                f"""
                <div style='background:{COLOR_WARN_BG};border-left:3px solid {COLOR_WARN_BD};
                            padding:1.2rem 1rem;border-radius:0 6px 6px 0;
                            font-size:0.88rem;color:{COLOR_TEXT};line-height:1.6;margin-top:2rem'>
                Configura los parametros y pulsa <strong>Aplicar anonimización</strong> para ver el resultado.
                </div>
                """,
                unsafe_allow_html=True,
            )
            return

        if ejecutar:
            if not columnas_qi:
                st.warning("Selecciona cuasi-identificadores en la pestana Importar datos antes de anonimizar.")
                return

            with st.spinner("Aplicando anonimización (anjana · IFCA-CSIC)..."):
                try:
                    if tecnica == "K-Anonimidad":
                        df_anon = k_anonimicidad(df, columnas_qi, k, supp_level=supp)
                    elif tecnica == "L-Diversidad":
                        df_anon = l_diversidad(
                            df, columnas_qi, columna_sensible, k, l, supp_level=supp
                        )
                    else:
                        df_anon = privacidad_diferencial(df, epsilon, sensibilidad)
                except Exception as e:
                    st.error(f"Error durante la anonimización: {e}")
                    return

            if len(df_anon) == 0:
                st.warning(
                    "No se pudo alcanzar el nivel de privacidad solicitado. "
                    "Prueba a bajar k/l o subir el porcentaje de supresion."
                )
                return

            st.session_state["df_anonimizado"] = df_anon
            st.session_state["tecnica_usada"] = tecnica
            st.session_state["params_anon"] = {"k": k, "l": l, "supp": supp}
            st.session_state["attrs_anon"] = dict(df_anon.attrs) if df_anon.attrs else {}

        df_anon = st.session_state.get("df_anonimizado")
        tecnica_usada = st.session_state.get("tecnica_usada", tecnica)

        registros_orig = len(df)
        registros_anon = len(df_anon)
        suprimidos = registros_orig - registros_anon
        retencion = registros_anon / registros_orig if registros_orig > 0 else 0

        st.markdown(
            f"<div class='section-header'>{tecnica_usada} · {registros_anon} registros · {len(df_anon.columns)} columnas</div>",
            unsafe_allow_html=True,
        )

        c1, c2, c3 = st.columns(3)
        c1.metric("Registros originales", registros_orig)
        c2.metric(
            "Registros anonimizados",
            registros_anon,
            delta=f"-{suprimidos}" if suprimidos else None,
            delta_color="inverse",
        )
        c3.metric("Retencion de datos", f"{retencion:.1%}")

        attrs = st.session_state.get("attrs_anon", {})
        salida_identica = bool(
            attrs.get("resultado_identico_original", False)
            or _resultado_identico(df, df_anon)
        )

        if salida_identica:
            st.error(
                "La salida anonimizada es identica al dataset original. "
                "Se bloquea la descarga para evitar exportar datos sin transformar. "
                "Revisa los cuasi-identificadores o sube k/l."
            )

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
            if salida_identica:
                st.button(
                    "Descargar datos anonimizados",
                    disabled=True,
                    use_container_width=True,
                    help="La descarga se bloquea porque el resultado coincide con el dataset original.",
                )
            else:
                with st.spinner(f"Generando {formato}..."):
                    datos, ext, mime = exportar(df_anon, formato)
                st.download_button(
                    f"Descargar datos anonimizados (.{ext})",
                    datos,
                    file_name=f"datos_anonimizados.{ext}",
                    mime=mime,
                    use_container_width=True,
                )
        with col_btn:
            if st.button("Ver metricas", key="continuar_anon", use_container_width=True, type="primary"):
                st.session_state["pagina_activa"] = 3
                st.rerun()
