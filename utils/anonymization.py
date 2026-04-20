import numpy as np
import pandas as pd


def generalize_column(series, bins=5):
    if pd.api.types.is_numeric_dtype(series):
        try:
            return pd.cut(series, bins=bins).astype(str)
        except Exception:
            return series.astype(str)
    else:
        return series.astype(str).apply(lambda x: x[:-1] + "*" if len(x) > 1 else "*")


def apply_k_anonymity(df, qi_cols, k):
    anon = df.copy()
    for col in qi_cols:
        anon[col] = generalize_column(anon[col])
    sizes = anon.groupby(qi_cols, dropna=False).transform("count").iloc[:, 0]
    return anon[sizes >= k].reset_index(drop=True)


def apply_l_diversity(df, qi_cols, sensitive_col, k, l):
    anon = df.copy()
    for col in qi_cols:
        anon[col] = generalize_column(anon[col])
    return anon.groupby(qi_cols, group_keys=False, dropna=False).filter(
        lambda g: len(g) >= k and g[sensitive_col].nunique() >= l
    ).reset_index(drop=True)


def apply_differential_privacy(df, epsilon, sensitivity):
    anon = df.copy()
    scale = sensitivity / epsilon
    for col in df.select_dtypes(include=[np.number]).columns:
        anon[col] = anon[col] + np.random.laplace(0, scale, len(df))
    return anon
