import streamlit as st

from utils.anonymization import apply_k_anonymity, apply_l_diversity, apply_differential_privacy


def render(df, qi_cols, sensitive_col, technique, k, l, epsilon, sensitivity, run):
    if df is None:
        st.info("👈 Ve a la pestaña **📥 IMPORTAR DATOS** para cargar un dataset.")
        return
    if not run:
        st.info("Configura los parámetros en el panel lateral y pulsa **▶ Aplicar anonimización**.")
        return

    with st.spinner("Aplicando anonimización..."):
        try:
            if technique == "K-Anonimato":
                anon_df = apply_k_anonymity(df, qi_cols, k)
                params_str = f"k={k}"
            elif technique == "L-Diversidad":
                anon_df = apply_l_diversity(df, qi_cols, sensitive_col, k, l)
                params_str = f"k={k}, l={l}"
            else:
                anon_df = apply_differential_privacy(df, epsilon, sensitivity)
                params_str = f"ε={epsilon}, Δf={sensitivity}"
            st.session_state["anon_df"] = anon_df
            st.session_state["technique"] = technique
            st.session_state["params_str"] = params_str
        except Exception as e:
            st.error(f"Error: {e}")
            st.stop()

    st.markdown(
        f"<div class='section-header'>{technique} · {params_str} · {len(anon_df)} registros retenidos</div>",
        unsafe_allow_html=True,
    )
    st.dataframe(anon_df, use_container_width=True, height=350)
    c1, c2, c3 = st.columns(3)
    c1.metric("Registros retenidos", len(anon_df))
    c2.metric("Retención", f"{len(anon_df) / len(df) * 100:.1f}%")
    c3.metric("Eliminados", len(df) - len(anon_df))
    st.download_button(
        "⬇ Descargar dataset anonimizado",
        anon_df.to_csv(index=False).encode("utf-8"),
        file_name="dataset_anonimizado.csv",
        mime="text/csv",
    )
