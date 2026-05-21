import numpy as np
import pandas as pd
import unicodedata
from hashlib import sha256
from anjana.anonymity import k_anonymity as _anjana_k_anon
from anjana.anonymity import l_diversity as _anjana_l_div
from anjana.anonymity.utils.utils import get_transformation as _anjana_get_transformation
from diffprivlib.accountant import BudgetAccountant
from diffprivlib.mechanisms import Laplace as LaplaceMechanism


def _crear_intervalos(valores, v_min, v_max, step):
    """
    Genera intervalos de generalizacion para valores numericos.

    Mantiene el formato que espera anjana ("[a, b)") y evita el bug
    observado en ``generate_intervals`` cuando el maximo cae en el borde.
    """
    inicio = np.floor(v_min / step) * step
    fin = (np.floor(v_max / step) + 2) * step
    bordes = np.arange(inicio, fin, step)

    resultado = []
    for val in valores:
        idx = np.searchsorted(bordes, val, side="right") - 1
        idx = max(0, min(idx, len(bordes) - 2))
        resultado.append(f"[{bordes[idx]}, {bordes[idx + 1]})")

    return resultado


def _preparar_df(df, qi_cols):
    """Limpia los cuasi-identificadores antes de delegar en anjana."""
    df_clean = df.copy()

    for col in qi_cols:
        if pd.api.types.is_numeric_dtype(df_clean[col]):
            if df_clean[col].dropna().empty:
                df_clean[col] = pd.Series(["Desconocido"] * len(df_clean), index=df_clean.index)
            else:
                df_clean[col] = df_clean[col].fillna(df_clean[col].median())
        else:
            df_clean[col] = df_clean[col].fillna("Desconocido").astype(str)

    return df_clean


def _generar_jerarquias(df, qi_cols):
    """
    Construye el diccionario ``hierarchies`` con el formato de anjana.

    Estructura esperada:
    ``{columna_qi: {0: valores_limpios, 1: nivel_1, ..., n: supresion_total}}``
    """
    hierarchies = {}
    n = len(df)

    for col in qi_cols:
        series = df[col]

        if pd.api.types.is_numeric_dtype(series):
            raw = np.asarray(series.to_numpy())

            if len(raw) == 0:
                hierarchies[col] = {
                    0: raw,
                    1: np.array([], dtype=object),
                }
                continue

            v_min = float(np.nanmin(raw))
            v_max = float(np.nanmax(raw))

            hierarchies[col] = {
                0: raw,
                1: np.array(_crear_intervalos(raw, v_min, v_max, step=5), dtype=object),
                2: np.array(_crear_intervalos(raw, v_min, v_max, step=10), dtype=object),
                3: np.array(_crear_intervalos(raw, v_min, v_max, step=20), dtype=object),
                4: np.array(["*"] * n, dtype=object),
            }
            continue

        raw = np.asarray(series.fillna("Desconocido").astype(str).to_numpy(), dtype=object)
        truncado = np.array(
            [(valor[:3] + "*" if len(valor) > 3 else valor) for valor in raw],
            dtype=object,
        )
        hierarchies[col] = {
            0: raw,
            1: truncado,
            2: np.array(["*"] * n, dtype=object),
        }

    return hierarchies


def _normalizar_salida_anjana(df_resultado, columnas_originales):
    """Elimina artefactos de anjana y restablece un indice limpio."""
    if "index" in df_resultado.columns and "index" not in columnas_originales:
        df_resultado = df_resultado.drop(columns=["index"])

    return df_resultado.reset_index(drop=True)


def _anotar_resultado_anjana(df_original, df_anon, qi_cols, hierarchies):
    """
    Adjunta metadatos utiles para auditoria y diagnostico.

    Estos metadatos permiten saber si anjana aplico generalizacion,
    cuantas filas suprimio y si el resultado termino siendo identico.
    """
    df_anon = df_anon.copy()
    transformacion = _anjana_get_transformation(df_anon, qi_cols, hierarchies)
    filas_suprimidas = max(len(df_original) - len(df_anon), 0)
    salida_igual = df_anon.reset_index(drop=True).equals(df_original.reset_index(drop=True))

    df_anon.attrs["anjana_transformation"] = transformacion
    df_anon.attrs["filas_suprimidas"] = filas_suprimidas
    df_anon.attrs["resultado_identico_original"] = salida_igual

    return df_anon


def k_anonimicidad(df, qi_cols, k, supp_level=30):
    """
    El algoritmo de generalizacion y supresion se delega por completo a anjana.
    """
    df_clean = _preparar_df(df, qi_cols)
    hierarchies = _generar_jerarquias(df_clean, qi_cols)

    df_anon = _anjana_k_anon(
        data=df_clean,
        ident=[],
        quasi_ident=qi_cols,
        k=k,
        supp_level=supp_level,
        hierarchies=hierarchies,
    )
    df_anon = _normalizar_salida_anjana(df_anon, df.columns)
    return _anotar_resultado_anjana(df_clean, df_anon, qi_cols, hierarchies)


def l_diversidad(df, qi_cols, col_sensible, k, l, supp_level=30):
    """
    El algoritmo de generalizacion y supresion se delega por completo a anjana.
    """
    df_clean = _preparar_df(df, qi_cols)
    hierarchies = _generar_jerarquias(df_clean, qi_cols)

    df_anon = _anjana_l_div(
        data=df_clean,
        ident=[],
        quasi_ident=qi_cols,
        sens_att=col_sensible,
        k=k,
        l_div=l,
        supp_level=supp_level,
        hierarchies=hierarchies,
    )
    df_anon = _normalizar_salida_anjana(df_anon, df.columns)
    return _anotar_resultado_anjana(df_clean, df_anon, qi_cols, hierarchies)


def privacidad_diferencial(df, epsilon, sensibilidad):
    """
    Privacidad Diferencial usando diffprivlib (IBM).

    Aplica el mecanismo de Laplace a cada columna numerica
    """
    anon = df.copy()
    columnas_num = df.select_dtypes(include=[np.number]).columns.tolist()

    epsilon_por_col = epsilon / len(columnas_num) if columnas_num else epsilon
    accountant = BudgetAccountant(epsilon=epsilon, delta=0)

    for col in columnas_num:
        mech = LaplaceMechanism(
            epsilon=epsilon_por_col,
            sensitivity=sensibilidad,
        )
        anon[col] = anon[col].apply(
            lambda x: mech.randomise(x) if pd.notna(x) else x
        )
        accountant.spend(epsilon_por_col, 0)

    anon.attrs["epsilon_total"] = epsilon
    anon.attrs["epsilon_gastado"] = sum(e for e, _ in accountant.spent_budget)
    anon.attrs["epsilon_por_columna"] = epsilon_por_col
    anon.attrs["n_columnas_ruido"] = len(columnas_num)

    return anon


def _seudonimo_determinista(columna, valor):
    """Genera un seudonimo estable para un valor concreto."""
    if pd.isna(valor):
        return valor

    token = sha256(f"{columna}::{valor}".encode("utf-8")).hexdigest()[:12].upper()
    return f"{columna}_ID_{token}"


def seudonimizar_columnas(df, columnas):
    """Seudonimiza identificadores directos"""
    presentes = [c for c in (columnas or []) if c in df.columns]
    if not presentes:
        return df.copy(), []

    df_seud = df.copy()
    for col in presentes:
        df_seud[col] = df_seud[col].map(lambda valor: _seudonimo_determinista(col, valor))

    return df_seud, presentes


def top_coding_columna(serie, percentil=90):
    """Aplica top-coding a una Serie numerica: valores por encima del percentil se capan al umbral."""
    if not pd.api.types.is_numeric_dtype(serie):
        return serie
    datos = serie.dropna()
    if datos.empty:
        return serie
    umbral = np.percentile(datos, percentil)
    return serie.where(serie.isna() | (serie <= umbral), umbral)


def bottom_coding_columna(serie, percentil=10):
    """Aplica bottom-coding a una Serie numerica: valores por debajo del percentil se elevan al umbral."""
    if not pd.api.types.is_numeric_dtype(serie):
        return serie
    datos = serie.dropna()
    if datos.empty:
        return serie
    umbral = np.percentile(datos, percentil)
    return serie.where(serie.isna() | (serie >= umbral), umbral)

def _normalizar_texto(s):
    if pd.isna(s):
        return s
    s = str(s).strip().lower()
    s = " ".join(s.split())
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s


def aplicar_preprocesado(df, columnas_directas=None, qi_cols=None, percentil_top=90, percentil_bottom=10):
    #1. SEUDONIMIZACION
    df_trabajo, seudonimizadas = seudonimizar_columnas(df, columnas_directas)
    resumen = []
    if seudonimizadas:
        resumen.append(
            f"Seudonimizacion de identificadores directos: {', '.join(seudonimizadas)}"
        )
    # 2. TOP-CODING + BOTTON-CODING
    cols_num = [
        c for c in (qi_cols or [])
        if c in df_trabajo.columns and pd.api.types.is_numeric_dtype(df_trabajo[c])
    ]
    if cols_num:
        for col in cols_num:
            # Calcular ambos umbrales sobre los datos originales antes de transformar
            datos_originales = df_trabajo[col].dropna()
            umbral_top = np.percentile(datos_originales, percentil_top)
            umbral_bottom = np.percentile(datos_originales, percentil_bottom)
            df_trabajo[col] = (
                df_trabajo[col]
                .where(df_trabajo[col].isna() | (df_trabajo[col] <= umbral_top), umbral_top)
                .where(df_trabajo[col].isna() | (df_trabajo[col] >= umbral_bottom), umbral_bottom)
            )
        resumen.append(
            f"Top-coding (p{percentil_top}) aplicado a: {', '.join(cols_num)}"
        )
        resumen.append(
            f"Bottom-coding (p{percentil_bottom}) aplicado a: {', '.join(cols_num)}"
        )
    #3. NORMALIZACIÓN DE TEXTOS
    cols_texto = [
        c for c in (qi_cols or [])  
        if c in df_trabajo.columns and pd.api.types.is_string_dtype(df_trabajo[c])
    ]
    if cols_texto:
        for col in cols_texto:
            df_trabajo[col] = df_trabajo[col].map(_normalizar_texto)
        resumen.append(
            f"Normalización de textos (strip + lower + acentos) aplicada a: {', '.join(cols_texto)}"
        )
        resumen.append(
            "Valores únicos por columna después de normalización: " +
            ", ".join([f"{col}: {df_trabajo[col].nunique()}" for col in cols_texto])
        )


    return df_trabajo, resumen
