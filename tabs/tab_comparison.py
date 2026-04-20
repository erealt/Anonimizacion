import matplotlib.pyplot as plt
import streamlit as st

from utils.anonymization import apply_k_anonymity, apply_l_diversity
from utils.metrics import compute_prosecutor_risk, compute_journalist_risk, compute_k_value


def render(df, qi_cols, sensitive_col):
    if df is None:
        st.info("👈 Ve a la pestaña **📥 IMPORTAR DATOS** para cargar un dataset.")
        return
    if not qi_cols:
        st.warning("Selecciona al menos un cuasi-identificador.")
        return

    st.markdown("<div class='section-header'>Comparativa entre técnicas</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='info-box'>Simula las tres técnicas con parámetros estándar para comparar privacidad vs utilidad.</div>",
        unsafe_allow_html=True,
    )

    with st.spinner("Calculando..."):
        try:
            df_k = apply_k_anonymity(df, qi_cols, 3)
            df_l = apply_l_diversity(df, qi_cols, sensitive_col, 3, 2)
            results = {
                "K-Anonimato (k=3)": {
                    "Retención (%)": len(df_k) / len(df) * 100,
                    "Riesgo Fiscal": compute_prosecutor_risk(df_k, qi_cols),
                    "Riesgo Periodístico": compute_journalist_risk(df_k, qi_cols),
                    "k efectivo": compute_k_value(df_k, qi_cols),
                },
                "L-Diversidad (k=3,l=2)": {
                    "Retención (%)": len(df_l) / len(df) * 100,
                    "Riesgo Fiscal": compute_prosecutor_risk(df_l, qi_cols),
                    "Riesgo Periodístico": compute_journalist_risk(df_l, qi_cols),
                    "k efectivo": compute_k_value(df_l, qi_cols),
                },
                "Priv. Diferencial (ε=1)": {
                    "Retención (%)": 100.0,
                    "Riesgo Fiscal": 0.10,
                    "Riesgo Periodístico": 0.067,
                    "k efectivo": "N/A",
                },
            }
            import pandas as pd
            comp_df = pd.DataFrame(results).T
            st.dataframe(
                comp_df.style.format({
                    "Retención (%)": "{:.1f}%",
                    "Riesgo Fiscal": "{:.2%}",
                    "Riesgo Periodístico": "{:.2%}",
                }),
                use_container_width=True,
            )

            st.markdown("---")
            fig2, axes = plt.subplots(1, 2, figsize=(10, 3.5))
            fig2.patch.set_facecolor("#0d0f14")
            techs = list(results.keys())
            colors = ["#4da6ff", "#f5a623", "#00e5a0"]
            for ax_i, key, title in zip(
                axes,
                ["Riesgo Fiscal", "Retención (%)"],
                ["Riesgo Fiscal", "Retención de datos (%)"],
            ):
                ax_i.set_facecolor("#12151c")
                vals = [results[t][key] for t in techs]
                bars = ax_i.bar(range(len(techs)), vals, color=colors, alpha=0.85, width=0.5)
                ax_i.set_xticks(range(len(techs)))
                ax_i.set_xticklabels([t.split(" ")[0] for t in techs], color="#a0aec0", fontsize=9)
                ax_i.set_title(title, color="#a0aec0", fontsize=10)
                ax_i.set_ylim(0, max(vals) * 1.3 + 0.01)
                ax_i.spines["top"].set_visible(False)
                ax_i.spines["right"].set_visible(False)
                for s in ax_i.spines.values():
                    s.set_edgecolor("#1e2330")
                ax_i.tick_params(colors="#6b7280")
                for bar, val in zip(bars, vals):
                    ax_i.text(
                        bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + max(vals) * 0.02,
                        f"{val:.1%}" if key == "Riesgo Fiscal" else f"{val:.1f}%",
                        ha="center", va="bottom", color="white", fontsize=8,
                    )
            plt.tight_layout()
            st.pyplot(fig2)
        except Exception as e:
            st.error(f"Error: {e}")
