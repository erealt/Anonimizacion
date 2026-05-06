import streamlit as st
from utils.anonimizacion import k_anonimicidad, l_diversidad, privacidad_diferencial
from utils.exporter import FORMATOS, exportar

# Paleta institucional (constantes compartidas)
COLOR_TEXT    = "#1a2340"
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
        tecnica = st.radio(
            "", ["K-Anonimidad", "L-Diversidad", "Privacidad Diferencial"],
            label_visibility="collapsed",
        )
        st.markdown("---")
        st.markdown("<div class='section-header'>Parámetros</div>", unsafe_allow_html=True)

        if tecnica == "K-Anonimidad":
            k = st.slider("Valor de k", 2, 20, 3,
                          help="Tamaño mínimo de cada grupo de equivalencia. "
                               "Cada combinación de cuasi-identificadores debe aparecer "
                               "al menos k veces. Valores más altos = más privacidad, "
                               "pero más registros suprimidos.")
            l, t_max, epsilon, sensibilidad = 2, 0.3, 1.0, 1.0
        elif tecnica == "L-Diversidad":
            k = st.slider("Valor de k", 2, 20, 3,
                          help="Tamaño mínimo de cada grupo de equivalencia "
                               "(se aplica k-anonimidad como base).")
            l = st.slider("Valor de l", 2, 10, 2,
                          help="Número mínimo de valores distintos del atributo sensible "
                               "en cada grupo. Protege contra ataques de homogeneidad: "
                               "si todos en un grupo tienen el mismo valor sensible, "
                               "un atacante lo infiere directamente.")
            t_max, epsilon, sensibilidad = 0.3, 1.0, 1.0
        # elif tecnica == "T-Closeness":
        #     k = st.slider("Valor de k", 2, 20, 3,
        #                   help="Tamaño mínimo de cada grupo de equivalencia "
        #                        "(se aplica k-anonimidad como base).")
        #     t_max = st.slider("Umbral t", 0.05, 1.0, 0.3, step=0.05,
        #                       help="Distancia máxima (EMD) entre la distribución del "
        #                            "atributo sensible en cada grupo y la distribución "
        #                            "global. Valores más bajos = más privacidad, "
        #                            "pero más grupos suprimidos.")
        #     l, epsilon, sensibilidad = 2, 1.0, 1.0
        else:
            epsilon = st.slider("Epsilon (ε)", 0.01, 5.0, 1.0, step=0.01,
                                help="Presupuesto de privacidad. Controla cuánto ruido "
                                     "se añade: ε bajo = mucho ruido (más privacidad, "
                                     "menos precisión); ε alto = poco ruido (menos "
                                     "privacidad, más precisión). Valores típicos: "
                                     "0.1 (muy privado) a 2.0 (moderado).")
            sensibilidad = st.slider("Sensibilidad (Δf)", 0.1, 10.0, 1.0, step=0.1,
                                     help="Máximo cambio que puede causar un solo registro "
                                          "en el resultado de la consulta. Determina la "
                                          "escala del ruido Laplace: a mayor sensibilidad, "
                                          "más ruido se necesita para la misma ε.")
            k, l, t_max = 3, 2, 0.3

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
                # elif tecnica == "T-Closeness":
                #     df_anon = t_closeness(df, columnas_qi, columna_sensible, k, t_max)
                else:
                    df_anon = privacidad_diferencial(df, epsilon, sensibilidad)

            st.session_state["df_anonimizado"] = df_anon
            st.session_state["tecnica_usada"]  = tecnica
            st.session_state["params_anon"]    = {"k": k, "l": l, "t_max": t_max}
            st.session_state["attrs_anon"] = dict(df_anon.attrs) if df_anon.attrs else {}

            # Verificación contextual con pycanon (solo lo que aplica)
            if len(df_anon) > 0 and columnas_qi and tecnica != "Privacidad Diferencial":
                with st.spinner("Verificando con pycanon..."):
                    from pycanon import anonymity
                    verif = {}
                    verif["k_anonymity"] = int(anonymity.k_anonymity(df_anon, columnas_qi))
                    if tecnica in ("L-Diversidad") and columna_sensible:
                        sa = [columna_sensible]
                        verif["l_diversity"] = int(anonymity.l_diversity(df_anon, columnas_qi, sa))
                    # if tecnica == "T-Closeness" and columna_sensible:
                    #     sa = [columna_sensible]
                    #     verif["t_closeness"] = float(anonymity.t_closeness(df_anon, columnas_qi, sa))
                    st.session_state["verificacion_pycanon"] = verif
                    st.session_state["verificacion_tecnica"] = tecnica
            else:
                st.session_state["verificacion_pycanon"] = {}
                st.session_state["verificacion_tecnica"] = tecnica

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

        # ── Verificación formal (pycanon / diffprivlib) ─────────────────
        verif = st.session_state.get("verificacion_pycanon", {})
        attrs = st.session_state.get("attrs_anon", {})

        if verif or attrs:
            st.markdown("---")
            st.markdown("<div class='section-header'>Verificación formal (pycanon · IFCA-CSIC)</div>", unsafe_allow_html=True)

            badges = []
            if verif.get("k_anonymity") is not None:
                badges.append(f"✅ **k-anonimidad**: k = {verif['k_anonymity']}")
            if verif.get("l_diversity") is not None:
                badges.append(f"✅ **l-diversidad**: l = {verif['l_diversity']}")
            # if verif.get("t_closeness") is not None:
            #     badges.append(f"✅ **t-closeness**: t = {verif['t_closeness']:.4f}")

            # Metadatos de diffprivlib
            if "epsilon_total" in attrs:
                badges.append(
                    f"🔒 **Privacidad diferencial** (diffprivlib IBM): "
                    f"ε = {attrs['epsilon_total']:.2f}, "
                    f"ε/columna = {attrs['epsilon_por_columna']:.3f}, "
                    f"{attrs['n_columnas_ruido']} columnas con ruido Laplace"
                )

            if badges:
                st.markdown(
                    "<div style='background:#f0fdf4;border:1px solid #86efac;border-radius:6px;"
                    "padding:1rem 1.2rem;margin-bottom:1rem;font-size:0.88rem;line-height:1.8'>"
                    + "<br>".join(badges)
                    + "</div>",
                    unsafe_allow_html=True,
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