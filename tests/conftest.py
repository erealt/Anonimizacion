"""
conftest.py — Fixtures reutilizables para toda la suite de tests.

Proporciona DataFrames sinteticos con distintas caracteristicas
(normal, vacio, con NaN, fila unica) para probar el modulo de anonimizacion.

"""

import numpy as np
import pandas as pd
import pytest


# ═══════════════════════════════════════════════════════════════════════════════
# FIXTURES PRINCIPALES
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def dummy_dataframe():
    """
    DataFrame sintetico representativo con 4 columnas:
    - edad (numerico): cuasi-identificador
    - codigo_postal (numerico): cuasi-identificador
    - sexo (categorico): cuasi-identificador
    - enfermedad (categorico): atributo sensible

    200 registros con distribucion variada para que k-anonimidad
    y l-diversidad tengan grupos de distintos tamanos.
    """
    np.random.seed(42)
    n = 200
    return pd.DataFrame({
        "edad": np.random.randint(18, 80, n),
        "codigo_postal": np.random.choice([28001, 28002, 28003, 28004, 28005], n),
        "sexo": np.random.choice(["Hombre", "Mujer"], n),
        "enfermedad": np.random.choice(
            ["Gripe", "Diabetes", "Cancer", "Hipertension", "Asma"], n
        ),
    })


@pytest.fixture
def qi_cols():
    """Lista de cuasi-identificadores por defecto."""
    return ["edad", "codigo_postal", "sexo"]


@pytest.fixture
def col_sensible():
    """Nombre del atributo sensible por defecto."""
    return "enfermedad"


@pytest.fixture
def empty_dataframe():
    """DataFrame vacio con la misma estructura de columnas."""
    return pd.DataFrame({
        "edad": pd.Series(dtype="int64"),
        "codigo_postal": pd.Series(dtype="int64"),
        "sexo": pd.Series(dtype="object"),
        "enfermedad": pd.Series(dtype="object"),
    })


@pytest.fixture
def nan_dataframe():
    """
    DataFrame con NaN en posiciones criticas:
    - edad: 40% nulos
    - codigo_postal: completamente nulo
    - sexo: 20% nulos
    - enfermedad: sin nulos (atributo sensible debe estar completo)
    """
    np.random.seed(99)
    n = 100
    edad = np.random.randint(18, 80, n).astype(float)
    edad[np.random.choice(n, 40, replace=False)] = np.nan

    codigo_postal = np.full(n, np.nan)  # 100% nulos

    sexo = np.random.choice(["Hombre", "Mujer", None], n, p=[0.4, 0.4, 0.2])

    enfermedad = np.random.choice(
        ["Gripe", "Diabetes", "Cancer", "Hipertension"], n
    )

    return pd.DataFrame({
        "edad": edad,
        "codigo_postal": codigo_postal,
        "sexo": sexo,
        "enfermedad": enfermedad,
    })


@pytest.fixture
def single_row_dataframe():
    """DataFrame con una unica fila — caso limite."""
    return pd.DataFrame({
        "edad": [35],
        "codigo_postal": [28001],
        "sexo": ["Hombre"],
        "enfermedad": ["Gripe"],
    })


@pytest.fixture
def large_dataframe():
    """
    DataFrame grande (5000 registros) para tests de rendimiento
    y para garantizar que anjana generaliza correctamente.
    """
    np.random.seed(123)
    n = 5000
    return pd.DataFrame({
        "edad": np.random.randint(18, 90, n),
        "codigo_postal": np.random.choice(
            [28001, 28002, 28003, 28004, 28005, 28006, 28007, 28008], n
        ),
        "sexo": np.random.choice(["Hombre", "Mujer"], n),
        "enfermedad": np.random.choice(
            ["Gripe", "Diabetes", "Cancer", "Hipertension", "Asma",
             "Bronquitis", "Neumonia", "Artritis"], n
        ),
    })
