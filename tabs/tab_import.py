import streamlit as st
import streamlit.components.v1 as components

from utils.loader import carga_automatica


def render():
    st.markdown("<div class='section-header'>Importar datos</div>", unsafe_allow_html=True)
    st.markdown("""
    <div class='info-box'>
    Sube uno o varios ficheros y la app detectará automáticamente el formato.
    </div>""", unsafe_allow_html=True)

    ficheros_subidos = st.file_uploader(
        "Arrastra aquí tu(s) fichero(s)",
        accept_multiple_files=True,
        type=None,
        key="auto_upload",
    )

    # ── Dataset ya cargado (uploader vacío pero hay df en sesión) ────────
    if not ficheros_subidos and "df" in st.session_state:
        df_cargado = st.session_state["df"]
        todas = df_cargado.columns.tolist()

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
                    {len(df_cargado)} registros ·
                    {len(df_cargado.columns)} columnas
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Selección de columnas (siempre accesible) ────────────────────
        st.markdown("---")
        st.markdown("<div class='section-header'>Modificar selección de columnas</div>", unsafe_allow_html=True)
        st.caption("Puedes cambiar los cuasi-identificadores, el atributo sensible y los identificadores directos sin recargar el dataset.")

        st.markdown("""
        <div style='background:#f0f4ff;border:1px solid #c7d2fe;border-left:4px solid #4f46e5;
                    border-radius:6px;padding:1rem 1.4rem;margin:0.8rem 0 1.2rem;font-size:0.85rem;line-height:1.8;'>
            <strong style='color:#1a3a6b;'>¿Cómo clasificar las columnas?</strong><br>
            <span style='color:#374151;'>
            🔴 <strong>Identificadores directos</strong> — Identifican a la persona por sí solos (nombre, DNI, email). Se seudonimizarán automáticamente antes de anonimizar.<br>
            🟡 <strong>Cuasi-identificadores (QI)</strong> — Columnas que combinadas pueden revelar la identidad (edad, sexo, código postal). Definen el riesgo de reidentificación.<br>
            🟢 <strong>Atributo sensible</strong> — El dato privado a proteger (diagnóstico, salario, religión). Es lo que no debe poderse vincular a ningún individuo.
            </span>
        </div>
        """, unsafe_allow_html=True)

        col_a, col_b = st.columns(2)

        sensible_actual = st.session_state.get("columna_sensible")
        qi_actual       = st.session_state.get("columnas_qi", [])
        ident_actual    = st.session_state.get("columnas_identificadoras", [])

        opciones_qi = [c for c in todas if c != sensible_actual and c not in ident_actual]
        default_qi  = [c for c in qi_actual if c in opciones_qi]

        with col_a:
            qi_seleccionado = st.multiselect(
                "Cuasi-identificadores (QI)",
                opciones_qi,
                default=default_qi,
                placeholder="Selecciona una o varias columnas...",
                key="qi_manual_cargado",
                help=(
                    "Atributos que, por sí solos, no identifican a nadie, pero combinados sí podrían hacerlo.\n\n"
                    "Ejemplos típicos: edad, sexo, código postal, fecha de nacimiento, municipio.\n\n"
                    "Selecciona todas las columnas que puedan usarse como filtros de búsqueda o cruzarse con fuentes externas (padrón, RRSS, etc.)."
                ),
            )

        opciones_sens = [c for c in todas if c not in qi_seleccionado and c not in ident_actual]
        idx_defecto = opciones_sens.index(sensible_actual) \
            if sensible_actual in opciones_sens else None

        with col_b:
            sensible_seleccionado = st.selectbox(
                "Atributo sensible",
                [None] + opciones_sens,
                index=0 if idx_defecto is None else idx_defecto + 1,
                format_func=lambda x: "Selecciona una columna..." if x is None else x,
                key="sens_manual_cargado",
                help=(
                    "El dato privado que quieres proteger: la información que no debería poder vincularse a ningún individuo concreto.\n\n"
                    "Ejemplos: diagnóstico médico, salario, filiación política, religión.\n\n"
                    "Solo se puede elegir una columna. No puede coincidir con ningún QI."
                ),
            )

        opciones_ident = [c for c in todas if c not in qi_seleccionado and c != sensible_seleccionado]
        default_ident  = [c for c in ident_actual if c in opciones_ident]
        identificadores_directos = st.multiselect(
            "Identificadores directos a seudonimizar (opcional)",
            opciones_ident,
            default=default_ident,
            placeholder="Ej.: nombre, dni, email, teléfono...",
            key="ident_manual_cargado",
            help="Estas columnas se seudonimizaran antes de la anonimización formal y no se usarán como QI.",
        )

        qi_cambio    = qi_seleccionado       != st.session_state.get("columnas_qi", [])
        sens_cambio  = sensible_seleccionado != st.session_state.get("columna_sensible")
        ident_cambio = identificadores_directos != st.session_state.get("columnas_identificadoras", [])

        st.session_state["columnas_qi"]             = qi_seleccionado
        st.session_state["columna_sensible"]         = sensible_seleccionado
        st.session_state["columnas_identificadoras"] = identificadores_directos

        if qi_cambio or sens_cambio or ident_cambio:
            st.session_state.pop("df_anonimizado", None)
            st.session_state.pop("tecnica_usada", None)

        # ── Botones de acción ────────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        col_nuevo, _, col_continuar = st.columns([1.5, 1.5, 1])

        with col_nuevo:
            if st.button("📂 Cargar un fichero diferente", use_container_width=True):
                for key in ["df", "fuente", "metodo", "hash_archivos",
                            "nuniques", "columnas_qi", "columna_sensible", "columnas_identificadoras",
                            "df_anonimizado", "tecnica_usada"]:
                    st.session_state.pop(key, None)
                st.session_state["abrir_dialogo"] = True
                st.rerun()

        with col_continuar:
            listo = bool(qi_seleccionado) and sensible_seleccionado is not None
            if st.button(
                "Continuar →",
                key="continuar_cargado",
                use_container_width=True,
                type="primary",
                disabled=not listo,
            ):
                st.session_state["pagina_activa"] = 1
                st.rerun()

        if not (bool(qi_seleccionado) and sensible_seleccionado is not None):
            st.caption("Selecciona al menos un cuasi-identificador y un atributo sensible para continuar.")
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
            "columnas_qi":             [],
            "columna_sensible":        None,
            "columnas_identificadoras": [],
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

    # ── Selección manual de columnas ─────────────────────────────────────
    st.markdown("---")
    st.markdown("<div class='section-header'>Selección de columnas</div>", unsafe_allow_html=True)

    st.markdown("""
    <div style='background:#f0f4ff;border:1px solid #c7d2fe;border-left:4px solid #4f46e5;
                border-radius:6px;padding:1rem 1.4rem;margin:0.8rem 0 1.2rem;font-size:0.85rem;line-height:1.8;'>
        <strong style='color:#1a3a6b;'>¿Cómo clasificar las columnas?</strong><br>
        <span style='color:#374151;'>
        🔴 <strong>Identificadores directos</strong> — Identifican a la persona por sí solos (nombre, DNI, email). Se seudonimizarán automáticamente antes de anonimizar.<br>
        🟡 <strong>Cuasi-identificadores (QI)</strong> — Columnas que combinadas pueden revelar la identidad (edad, sexo, código postal). Definen el riesgo de reidentificación.<br>
        🟢 <strong>Atributo sensible</strong> — El dato privado a proteger (diagnóstico, salario, religión). Es lo que no debe poderse vincular a ningún individuo.
        </span>
    </div>
    """, unsafe_allow_html=True)

    col_a, col_b = st.columns(2)

    sensible_actual = st.session_state.get("columna_sensible")
    qi_actual       = st.session_state.get("columnas_qi", [])
    ident_actual    = st.session_state.get("columnas_identificadoras", [])

    opciones_qi = [c for c in todas if c != sensible_actual and c not in ident_actual]
    default_qi  = [c for c in qi_actual if c in opciones_qi]

    with col_a:
        qi_seleccionado = st.multiselect(
            "Cuasi-identificadores (QI)",
            opciones_qi,
            default=default_qi,
            placeholder="Selecciona una o varias columnas...",
            key="qi_manual",
            help=(
                "Atributos que, por sí solos, no identifican a nadie, pero combinados sí podrían hacerlo.\n\n"
                "Ejemplos típicos: edad, sexo, código postal, fecha de nacimiento, municipio.\n\n"
                "Selecciona todas las columnas que puedan usarse como filtros de búsqueda o cruzarse con fuentes externas (padrón, RRSS, etc.)."
            ),
        )

    opciones_sens = [c for c in todas if c not in qi_seleccionado and c not in ident_actual]
    idx_defecto   = opciones_sens.index(sensible_actual) \
        if sensible_actual in opciones_sens else None

    with col_b:
        sensible_seleccionado = st.selectbox(
            "Atributo sensible",
            [None] + opciones_sens,
            index=0 if idx_defecto is None else idx_defecto + 1,
            format_func=lambda x: "Selecciona una columna..." if x is None else x,
            key="sens_manual",
            help=(
                "El dato privado que quieres proteger: la información que no debería poder vincularse a ningún individuo concreto.\n\n"
                "Ejemplos: diagnóstico médico, salario, filiación política, religión.\n\n"
                "Solo se puede elegir una columna. No puede coincidir con ningún QI."
            ),
        )

    opciones_ident = [c for c in todas if c not in qi_seleccionado and c != sensible_seleccionado]
    default_ident  = [c for c in ident_actual if c in opciones_ident]
    identificadores_directos = st.multiselect(
        "Identificadores directos a seudonimizar (opcional)",
        opciones_ident,
        default=default_ident,
        placeholder="Ej.: nombre, dni, email, teléfono...",
        key="ident_manual",
        help="Estas columnas se seudonimizaran antes de la anonimización formal y no se usarán como QI.",
    )

    st.session_state["columnas_qi"]             = qi_seleccionado
    st.session_state["columna_sensible"]         = sensible_seleccionado
    st.session_state["columnas_identificadoras"] = identificadores_directos

    # ── Botón continuar ──────────────────────────────────────────────────
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
