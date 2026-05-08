"""
Tests de casos limite y condiciones extremas.
"""

import numpy as np
import pandas as pd
import pytest
from unittest.mock import patch

from utils.anonimizacion import (
    _crear_intervalos,
    _generar_jerarquias,
    _preparar_df,
    k_anonimicidad,
    l_diversidad,
    privacidad_diferencial,
)


class TestDataFrameVacio:
    def test_generar_jerarquias_vacio(self, empty_dataframe):
        h = _generar_jerarquias(empty_dataframe, ["edad", "sexo"])
        assert isinstance(h, dict)
        assert "edad" in h and "sexo" in h

    def test_preparar_df_vacio(self, empty_dataframe):
        resultado = _preparar_df(empty_dataframe, ["edad", "sexo"])
        assert isinstance(resultado, pd.DataFrame)
        assert len(resultado) == 0

    def test_privacidad_diferencial_vacio(self, empty_dataframe):
        resultado = privacidad_diferencial(empty_dataframe, epsilon=1.0, sensibilidad=1.0)
        assert isinstance(resultado, pd.DataFrame)
        assert len(resultado) == 0


class TestFilaUnica:
    def test_generar_jerarquias_fila_unica(self, single_row_dataframe):
        h = _generar_jerarquias(single_row_dataframe, ["edad", "sexo"])
        for col in ["edad", "sexo"]:
            for arr in h[col].values():
                assert len(arr) == 1

    def test_privacidad_diferencial_fila_unica(self, single_row_dataframe):
        resultado = privacidad_diferencial(single_row_dataframe, epsilon=1.0, sensibilidad=1.0)
        assert len(resultado) == 1

    def test_k_anonimicidad_fila_unica_con_mock(self, single_row_dataframe):
        df_mock = single_row_dataframe.copy()
        with patch("utils.anonimizacion._anjana_k_anon", return_value=df_mock):
            resultado = k_anonimicidad(single_row_dataframe, ["edad", "sexo"], k=1, supp_level=100)
            assert isinstance(resultado, pd.DataFrame)


class TestColumnasNulas:
    def test_preparar_numerico_100_nulo(self):
        df = pd.DataFrame({"valor": [np.nan, np.nan, np.nan], "cat": ["A", "B", "C"]})
        resultado = _preparar_df(df, ["valor"])
        assert all(resultado["valor"] == "Desconocido")

    def test_jerarquias_numerico_100_nulo(self):
        df = pd.DataFrame({"valor": [np.nan, np.nan, np.nan]})
        df_clean = _preparar_df(df, ["valor"])
        h = _generar_jerarquias(df_clean, ["valor"])
        assert len(h["valor"]) == 3
        assert all(v == "Desconocido" for v in h["valor"][0])
        assert all(v == "*" for v in h["valor"][2])

    def test_jerarquias_categorico_con_nulos(self, nan_dataframe):
        h = _generar_jerarquias(_preparar_df(nan_dataframe, ["sexo"]), ["sexo"])
        assert "Desconocido" in set(h["sexo"][0])


class TestParametrosInvalidos:
    def test_k_mayor_que_registros(self, dummy_dataframe, qi_cols):
        with patch("utils.anonimizacion._anjana_k_anon") as mock_anon:
            mock_anon.return_value = pd.DataFrame(columns=dummy_dataframe.columns)
            resultado = k_anonimicidad(dummy_dataframe, qi_cols, k=9999, supp_level=50)
            assert isinstance(resultado, pd.DataFrame)

    def test_l_mayor_que_valores_sensibles(self, dummy_dataframe, qi_cols, col_sensible):
        with patch("utils.anonimizacion._anjana_l_div") as mock_ldiv:
            mock_ldiv.return_value = pd.DataFrame(columns=dummy_dataframe.columns)
            resultado = l_diversidad(dummy_dataframe, qi_cols, col_sensible, k=2, l=999, supp_level=50)
            assert isinstance(resultado, pd.DataFrame)

    def test_sensibilidad_negativa(self, dummy_dataframe):
        with pytest.raises((ValueError, Exception)):
            privacidad_diferencial(dummy_dataframe, epsilon=1.0, sensibilidad=-1.0)


class TestIntervalosExtremos:
    def test_un_solo_valor(self):
        valores = np.array([50, 50, 50])
        resultado = _crear_intervalos(valores, 50, 51, step=5)
        assert len(resultado) == 3
        assert len(set(resultado)) == 1

    def test_valores_negativos(self):
        valores = np.array([-10, -5, 0, 5])
        resultado = _crear_intervalos(valores, -10, 6, step=5)
        assert len(resultado) == 4


class TestTiposDatos:
    def test_enteros_y_flotantes_mezclados(self):
        df = pd.DataFrame({"valor": [1, 2.5, 3, 4.7, 5], "cat": ["A", "B", "C", "D", "E"]})
        h = _generar_jerarquias(df, ["valor"])
        assert "valor" in h
        assert len(h["valor"]) >= 2

    def test_strings_con_caracteres_especiales(self):
        df = pd.DataFrame({"ciudad": ["Madrid", "Malaga", "A Coruna", "San Sebastian", "Leon"]})
        h = _generar_jerarquias(df, ["ciudad"])
        assert all(isinstance(v, (str, np.str_)) for v in set(h["ciudad"][1]))

    def test_booleanos_como_qi(self):
        df = pd.DataFrame({"activo": [True, False, True, False, True], "nombre": ["A", "B", "C", "D", "E"]})
        h = _generar_jerarquias(df, ["activo"])
        assert "activo" in h
