import numpy as np
import pandas as pd
from diffprivlib.mechanisms import Laplace as LaplaceMechanism
from diffprivlib.accountant import BudgetAccountant


# GENERALIZACIÓN ADAPTATIVA


def generalizacion(series, bins=10):
    
    # ── Manejo de series vacías ──────────────────────────────────────────────
    s = series.dropna()
    if len(s) == 0:
        return series.astype(str)

    n_unicos = s.nunique()

   
    # 1. RAMA NUMÉRICA
   
    if pd.api.types.is_numeric_dtype(series):

        # Comprobación segura de si todos son enteros (protege contra NaN)
        es_entero = bool((s % 1 == 0).all()) if len(s) > 0 else False

        # ── 1.A. Discretos con pocos valores: NO generalizar ─────────────────
        # Si ≤60 valores únicos y todos enteros → son categorías codificadas
        # como números. Generalizarlos destruiría su significado.
        if n_unicos <= 60 and es_entero:
            return series.astype(str)

        # ── 1.B. Enteros de alta cardinalidad → SIEMPRE son códigos ──────────
        # Clave: si un número NO tiene decimales y tiene >60 valores únicos,
        # es un código (municipio, CP, ID). Las variables continuas reales
        # (KM, peso, salario) siempre tienen decimales en algún registro.
        # Enmascaramos ~1/3 de los dígitos para preservar la jerarquía.
        if es_entero and n_unicos > 60:
            n_digitos = len(str(int(abs(s.max()))))
            digitos_mask = max(1, n_digitos // 3)
            return series.astype(str).apply(
                lambda x, dm=digitos_mask: (
                    x[:-dm] + "*" * dm
                    if len(x) > dm and x not in ("nan", "None", "")
                    else x
                )
            )

        # ── 1.C. Continuos (decimales): cuantiles ────────────────────────────
        # Si hay sentinelas extremos (ej: 9999 = "no disponible"),
        # recortamos al percentil 99 para que no distorsionen los bins.
        serie_qcut = series.copy()
        p95 = s.quantile(0.95)
        if p95 < s.max() * 0.5:
            # Hay valores extremos muy por encima del grueso de datos (sentinelas)
            serie_qcut = series.clip(upper=p95)

        try:
            resultado = pd.qcut(serie_qcut, q=bins, duplicates="drop")
        except Exception:
            try:
                resultado = pd.cut(serie_qcut, bins=bins)
            except Exception:
                return series.astype(str)

        # Convertir intervalos a etiquetas legibles: (17.999, 27.4] → "18 - 27"
        return resultado.apply(
            lambda x: f"{int(np.ceil(x.left))} - {int(np.floor(x.right))}"
            if pd.notna(x) else "nan"
        )


    # 2. RAMA CATEGÓRICA (texto)
   
    s_str = series.fillna("Desconocido").astype(str)

    # ── 2.A. Baja cardinalidad (≤50): truncar último carácter ────────────────
    if n_unicos <= 50:
        return s_str.apply(lambda x: x[:-1] + "*" if len(x) > 1 else "*")

    # ── 2.B. Alta cardinalidad (>50): top-20 + "Otros" ──────────────────────
    top = s_str.value_counts().head(20).index
    return s_str.where(s_str.isin(top), other="Otros")


# TÉCNICAS DE ANONIMIZACIÓN


def k_anonimicidad(df, qi_cols, k):
    """
    K-Anonimidad 
    Generaliza los QI y suprime registros cuyo grupo tiene tamaño < k.
    """
    anon = df.copy()
    for col in qi_cols:
        anon[col] = generalizacion(anon[col])

    sizes = anon.groupby(qi_cols, dropna=False)[qi_cols[0]].transform("size")
    return anon[sizes >= k].reset_index(drop=True)


def l_diversidad(df, qi_cols, col_sensible, k, l):
    """
    L-Diversidad (Machanavajjhala et al., 2007).
    Cada grupo de equivalencia debe tener ≥k registros Y ≥l valores
    distintos en el atributo sensible.
    """
    anon = df.copy()
    for col in qi_cols:
        anon[col] = generalizacion(anon[col])

    return anon.groupby(qi_cols, group_keys=False, dropna=False).filter(
        lambda g: len(g) >= k and g[col_sensible].nunique() >= l
    ).reset_index(drop=True)


def t_closeness(df, qi_cols, col_sensible, k, t_max):
    """
    La distribución del atributo sensible en cada grupo no debe diferir
    más de t respecto a la distribución global (Earth Mover's Distance).
    Suprime grupos con mayor EMD hasta cumplir el umbral.
    """
    anon = df.copy()
    for col in qi_cols:
        anon[col] = generalizacion(anon[col])

    # Primero aplicar k-anonimidad como base
    sizes = anon.groupby(qi_cols, dropna=False)[qi_cols[0]].transform("size")
    anon = anon[sizes >= k].reset_index(drop=True)

    if len(anon) == 0:
        return anon

    # Calcular EMD por grupo y suprimir los que superen el umbral
    dist_global = anon[col_sensible].value_counts(normalize=True)

    def emd_grupo(grupo):
        dist_local = grupo[col_sensible].value_counts(normalize=True)
        todas = dist_global.index.union(dist_local.index)
        return float(np.abs(
            dist_global.reindex(todas, fill_value=0) -
            dist_local.reindex(todas, fill_value=0)
        ).sum()) / 2

    grupos = list(anon.groupby(qi_cols, dropna=False))
    partes = [g for _, g in grupos if emd_grupo(g) <= t_max and len(g) >= k]

    if partes:
        return pd.concat(partes).reset_index(drop=True)
    return anon.iloc[:0].copy().reset_index(drop=True)


def privacidad_diferencial(df, epsilon, sensibilidad):
    """
    Privacidad Diferencial (Dwork, 2006).
    Usa el mecanismo de Laplace de diffprivlib (IBM) en vez de ruido manual.
    Incluye control de presupuesto de privacidad (ε).
    """
    anon = df.copy()
    columnas_num = df.select_dtypes(include=[np.number]).columns.tolist()

    # Presupuesto total repartido entre columnas (composición secuencial)
    epsilon_por_col = epsilon / len(columnas_num) if columnas_num else epsilon
    accountant = BudgetAccountant(epsilon=epsilon, delta=0)

    for col in columnas_num:
        mech = LaplaceMechanism(
            epsilon=epsilon_por_col,
            sensitivity=sensibilidad,
        )
        # Aplicar mecanismo valor a valor
        anon[col] = anon[col].apply(
            lambda x: mech.randomise(x) if pd.notna(x) else x
        )
        accountant.spend(epsilon_por_col, 0)

    # Guardar metadatos de presupuesto
    anon.attrs["epsilon_total"] = epsilon
    anon.attrs["epsilon_gastado"] = sum(e for e, _ in accountant.spent_budget)
    anon.attrs["epsilon_por_columna"] = epsilon_por_col
    anon.attrs["n_columnas_ruido"] = len(columnas_num)

    return anon

