import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from utils.metricas import *

def render(df, qi_cols, source):
    if df is None:
        st.info("👈 Ve a la pestaña **📥 IMPORTAR DATOS** para cargar un dataset.")
        return

    # ─── 1. CABECERA Y DATOS ──────────────────────────────────────────
    st.markdown(f"<div class='section-header'>{source} · {len(df)} registros · {len(df.columns)} columnas</div>", unsafe_allow_html=True)
    
    # ¡AQUÍ ESTÁ EL CAMBIO! Usamos .head(100) para enviar solo una muestra visual al navegador
    st.dataframe(df.head(100), use_container_width=True, height=250)
    st.caption(f"👀 Mostrando una vista previa de las primeras 100 filas (de un total de {len(df)}).")
    
    if not qi_cols:
        st.warning("⚠️ Selecciona Cuasi-Identificadores en la pestaña de Importar para ver el análisis de riesgo.")
        return

    st.markdown("---")
    st.markdown("### Paso 2: Análisis de Riesgo Original")
    st.markdown("<p style='color:#a0aec0; font-size:0.9rem;'>Evaluación del riesgo de re-identificación en tus datos sin anonimizar.</p>", unsafe_allow_html=True)

    # ─── CÁLCULOS DE MÉTRICAS ────────────────────────────────────────
    r_maximo = riesgo_maximo(df, qi_cols)
    r_medio = riesgo_medio(df, qi_cols)
    t_unicidad = tasa_unicidad(df, qi_cols)
    k_actual = k_value(df, qi_cols)
    
    label_m, class_m = riesgo_label(t_unicidad)
    label_f, class_f = riesgo_label(r_maximo)
    label_p, class_p = riesgo_label(r_medio)

    # ─── 2. ALERTA GLOBAL DE RIESGO (F-SCORE PRIVACIDAD/UTILIDAD) ────
    
    # 1. Definimos las variables de tu fórmula
    utilidad = 1.0  # En los datos originales la retención siempre es 100%
    privacidad = max(0.0, 1.0 - r_maximo) # 100% menos el Riesgo Máximo
    
    # 2. Tu fórmula: La Media Armónica (F-Score)
    if (privacidad + utilidad) == 0:
        riesgo_global = 0.0
    else:
        riesgo_global = 2 * (privacidad * utilidad) / (privacidad + utilidad)
    
    # 3. Definimos las alertas basadas en el score
    # Un score bajo significa que la balanza está muy desequilibrada (mucha utilidad, cero privacidad)
    if riesgo_global < 0.50:
        bg_color, border_color, text_color = "#2e0d0d", "#ff4d4d", "#ff4d4d"
        icono = "⚠️"
        nivel = "CRÍTICO (Desequilibrio)"
        texto_explicativo = f"El Índice Global (F-Score) es de <strong style='color:{text_color};'>{riesgo_global:.1%}</strong>. Los datos tienen utilidad total (100%), pero la privacidad ({privacidad:.1%}) es inaceptable."
    elif riesgo_global < 0.80:
        bg_color, border_color, text_color = "#2e2500", "#f5a623", "#f5a623"
        icono = "⚖️"
        nivel = "MEJORABLE"
        texto_explicativo = f"El Índice Global es de <strong style='color:{text_color};'>{riesgo_global:.1%}</strong>. Se recomienda aplicar anonimización para equilibrar la balanza."
    else:
        bg_color, border_color, text_color = "#0d2e1f", "#00e5a0", "#00e5a0"
        icono = "✅"
        nivel = "ÓPTIMO"
        texto_explicativo = f"El Índice Global es de <strong style='color:{text_color};'>{riesgo_global:.1%}</strong>. El balance entre privacidad ({privacidad:.1%}) y utilidad es excelente."

    st.markdown(f"""
    <div style='background-color: {bg_color}; border: 1px solid {border_color}; border-radius: 8px; padding: 1.5rem; margin-bottom: 2rem;'>
        <div style='display: flex; align-items: center; gap: 1rem;'>
            <div style='background: {bg_color}; border: 2px solid {border_color}; border-radius: 50%; min-width: 50px; height: 50px; display: flex; align-items: center; justify-content: center; font-size: 1.5rem;'>
                {icono}
            </div>
            <div>
                <h3 style='margin: 0; color: {text_color}; display: inline-block;'>Balance Privacidad/Utilidad: {nivel}</h3>
                <p style='margin: 0.5rem 0 0 0; color: #e8eaf0;'>{texto_explicativo}</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    # ─── 3. TARJETAS DE RIESGO (ESTILO DASHBOARD MODERNIZADO) ────────
    c1, c2, c3 = st.columns(3)
    
    def crear_tarjeta(titulo, porcentaje, etiqueta, clase_etiqueta, subtitulo):
        # Asignamos colores a mano para evitar fallos del CSS externo
        if "bajo" in clase_etiqueta or "low" in clase_etiqueta:
            bg_badge, col_badge, color_num = "#0d2e1f", "#00e5a0", "#00e5a0"
        elif "medio" in clase_etiqueta or "medium" in clase_etiqueta:
            bg_badge, col_badge, color_num = "#2e2500", "#f5a623", "#f5a623"
        else:
            bg_badge, col_badge, color_num = "#2e0d0d", "#ff4d4d", "#ff4d4d"

        return f"""
        <div style='background: #12151c; border: 1px solid #1e2330; border-radius: 8px; padding: 1.5rem; height: 100%; box-shadow: 0 4px 6px rgba(0,0,0,0.2);'>
            <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.2rem;'>
                <strong style='color: #a0aec0; font-size: 0.95rem;'>{titulo}</strong>
                <span style='background: {bg_badge}; color: {col_badge}; border: 1px solid {col_badge}; padding: 0.25rem 0.75rem; border-radius: 4px; font-family: "Space Mono", monospace; font-size: 0.75rem; font-weight: bold; letter-spacing: 0.05em;'>{etiqueta}</span>
            </div>
            <div style='font-family: "DM Sans", sans-serif; font-size: 2.8rem; font-weight: 700; color: {color_num}; margin-bottom: 0.3rem; line-height: 1;'>
                {porcentaje:.1%}
            </div>
            <div style='color: #6b7280; font-size: 0.85rem; line-height: 1.3;'>{subtitulo}</div>
        </div>
        """

    with c1:
        st.markdown(crear_tarjeta("🛡️ Riesgo Mámimo", r_maximo, label_f, class_f, "Probabilidad de identificar a alguien concreto"), unsafe_allow_html=True)
    with c2:
        st.markdown(crear_tarjeta("📈 Riesgo Medio", r_medio, label_p, class_p, "Probabilidad media de reidentificación"), unsafe_allow_html=True)
    with c3:
        st.markdown(crear_tarjeta("🎯 Tasa de unicidad", t_unicidad, label_m, class_m, "% de personas únicas en el dataset"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ─── 4. INDICADOR K-ANONIMATO (LIMPIO) ───────────────────────────
    color_k = "#ff4d4d" if k_actual < 3 else "#00e5a0"
    st.markdown(f"""
    <div style='background: #12151c; border: 1px solid #1e2330; border-radius: 8px; padding: 1.5rem; display: flex; justify-content: space-between; align-items: center;'>
        <div>
            <strong style='color: #e8eaf0; font-size: 1.1rem;'>Nivel de K-Anonimidad Actual</strong><br>
            <span style='color: #6b7280; font-size: 0.9rem;'>Tamaño mínimo de grupo encontrado en el dataset</span>
        </div>
        <div style='font-family: "DM Sans", sans-serif; font-size: 3rem; font-weight: 700; color: {color_k}; line-height: 1;'>
            k = {k_actual}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ─── 5. GRÁFICOS ANALÍTICOS ──────────────────────────────────────
    col_graf1, col_graf2 = st.columns(2)

    # Gráfico 1: Tarta de distribución de K (Más pequeña)
    with col_graf1:
        st.markdown("**👥 Distribución de Grupos**")
        
        sizes = df.groupby(qi_cols, dropna=False).size()
        k1 = (sizes == 1).sum()
        k2 = (sizes == 2).sum()
        k3_plus = (sizes >= 3).sum()
        
        # Reducimos el figsize para hacer la tarta más pequeña
        fig1, ax1 = plt.subplots(figsize=(2.5, 2.5)) 
        fig1.patch.set_facecolor('#0d0f14')
        
        valores = [k1, k2, k3_plus]
        etiquetas = [f'k=1 (únicos): {k1}', f'k=2: {k2}', f'k≥3: {k3_plus}']
        colores = ['#ff4d4d', '#f5a623', '#00e5a0']
        
        val_filtrados = [v for v in valores if v > 0]
        etiq_filtradas = [e for v, e in zip(valores, etiquetas) if v > 0]
        col_filtrados = [c for v, c in zip(valores, colores) if v > 0]
        
        if val_filtrados: # Solo dibujar si hay datos
            wedges, texts = ax1.pie(
                val_filtrados, labels=etiq_filtradas, colors=col_filtrados, 
                startangle=90, wedgeprops={'edgecolor': '#0d0f14', 'linewidth': 1.5}
            )
            for text, color in zip(texts, col_filtrados):
                text.set_color(color)
                text.set_fontsize(9)
                
        plt.tight_layout()
        st.pyplot(fig1)

    # Gráfico 2: Riesgo individual por variable
    with col_graf2:
        st.markdown("**📈 Riesgo por Atributo (Aislamiento)**")
        st.caption("Muestra si alguna columna por sí sola hace únicos a los individuos.")
        
        riesgos_attr = []
        for col in qi_cols:
            # Forma más segura y rápida de contar únicos por columna en Pandas
            unicos = (df[col].value_counts(dropna=False) == 1).sum()
            riesgo = (unicos / len(df)) * 100
            riesgos_attr.append((str(col), riesgo))
            
        riesgos_attr.sort(key=lambda x: x[1], reverse=True)
        cols_names = [x[0][:12] + ".." if len(x[0]) > 12 else x[0] for x in riesgos_attr]
        riesgos_vals = [x[1] for x in riesgos_attr]

        # Ajustamos el tamaño
        fig2, ax2 = plt.subplots(figsize=(5, 3.5))
        fig2.patch.set_facecolor('#0d0f14')
        ax2.set_facecolor('#0d0f14')
        
        barras = ax2.bar(cols_names, riesgos_vals, color='#f5a623', alpha=0.85)
        
        # Truco: Si el riesgo máximo es muy bajo o 0, forzamos la escala hasta el 10%
        max_riesgo = max(riesgos_vals) if riesgos_vals else 0
        ax2.set_ylim(0, max(10, max_riesgo * 1.3)) 
        
        ax2.tick_params(colors='#6b7280')
        
        # ─── ¡AQUÍ ESTÁ LA MAGIA PARA QUE NO SE SOLAPEN! ───
        ax2.set_xticks(range(len(cols_names)))
        ax2.set_xticklabels(cols_names, rotation=45, ha='right', fontsize=8)
        # ───────────────────────────────────────────────────
        
        for s in ax2.spines.values():
            s.set_edgecolor('#1e2330')
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        
        # Pintar los porcentajes siempre (incluso si es 0.0%)
        for bar, val in zip(barras, riesgos_vals):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                     f'{val:.1f}%', ha='center', color='#a0aec0', fontsize=8)
            
        plt.tight_layout()
        st.pyplot(fig2)