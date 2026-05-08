"""
Tests unitarios para las funciones principales del modulo de anonimización.
"""

import numpy as np
import pandas as pd
import pytest
from unittest.mock import MagicMock, patch

from utils.anonimizacion import (
    _crear_intervalos,
    _generar_jerarquias,
    _preparar_df,
    k_anonimicidad,
    l_diversidad,
    privacidad_diferencial,
)


class TestCrearIntervalos:
    def test_intervalos_basicos(self):
        valores = np.array([20, 25, 30, 35])
        resultado = _crear_intervalos(valores, 20, 36, step=10)
        assert len(resultado) == 4
        assert all(r.startswith("[") and ")" in r for r in resultado)

    def test_valor_en_limite_superior(self):
        valores = np.array([89, 90])
        resultado = _crear_intervalos(valores, 17, 91, step=5)
        assert len(resultado) == 2

    def test_step_mayor_que_rango(self):
        valores = np.array([25, 26, 27])
        resultado = _crear_intervalos(valores, 25, 28, step=100)
        assert len(resultado) == 3
        assert len(set(resultado)) == 1


class TestGenerarJerarquias:
    def test_devuelve_diccionario(self, dummy_dataframe, qi_cols):
        h = _generar_jerarquias(dummy_dataframe, qi_cols)
        assert isinstance(h, dict)
        assert set(h.keys()) == set(qi_cols)

    def test_nivel_0_tiene_misma_longitud(self, dummy_dataframe, qi_cols):
        h = _generar_jerarquias(dummy_dataframe, qi_cols)
        for col in qi_cols:
            assert 0 in h[col]
            assert len(h[col][0]) == len(dummy_dataframe)

    def test_numerico_tiene_intervalos_y_supresion(self, dummy_dataframe):
        h = _generar_jerarquias(dummy_dataframe, ["edad"])
        assert list(h["edad"].keys()) == [0, 1, 2, 3, 4]
        assert "[" in str(h["edad"][1][0]) and ")" in str(h["edad"][1][0])
        assert all(v == "*" for v in h["edad"][4])

    def test_categorico_tiene_truncado_y_supresion(self, dummy_dataframe):
        h = _generar_jerarquias(dummy_dataframe, ["sexo"])
        assert list(h["sexo"].keys()) == [0, 1, 2]
        assert any("*" in str(v) for v in h["sexo"][1])
        assert all(v == "*" for v in h["sexo"][2])

    def test_columna_completamente_nula_es_valida(self, nan_dataframe):
        df_clean = _preparar_df(nan_dataframe, ["codigo_postal"])
        h = _generar_jerarquias(df_clean, ["codigo_postal"])
        assert all(v == "Desconocido" for v in h["codigo_postal"][0])
        assert all(v == "*" for v in h["codigo_postal"][2])


class TestPrepararDf:
    def test_sin_nan_en_qi(self, nan_dataframe, qi_cols):
        df_clean = _preparar_df(nan_dataframe, qi_cols)
        for col in qi_cols:
            assert df_clean[col].isna().sum() == 0

    def test_numerico_rellena_con_mediana(self, nan_dataframe):
        df_clean = _preparar_df(nan_dataframe, ["edad"])
        mediana = nan_dataframe["edad"].median()
        mask_nan = nan_dataframe["edad"].isna()
        assert all(df_clean.loc[mask_nan, "edad"] == mediana)

    def test_numerico_100_nulo_rellena_con_desconocido(self):
        df = pd.DataFrame({"valor": [np.nan, np.nan, np.nan]})
        df_clean = _preparar_df(df, ["valor"])
        assert all(df_clean["valor"] == "Desconocido")

    def test_categorico_rellena_con_desconocido(self, nan_dataframe):
        df_clean = _preparar_df(nan_dataframe, ["sexo"])
        mask_nan = nan_dataframe["sexo"].isna()
        assert all(df_clean.loc[mask_nan, "sexo"] == "Desconocido")

    def test_no_modifica_original(self, dummy_dataframe, qi_cols):
        original = dummy_dataframe.copy()
        _preparar_df(dummy_dataframe, qi_cols)
        pd.testing.assert_frame_equal(dummy_dataframe, original)


class TestKAnonimicidad:
    def test_devuelve_dataframe(self, dummy_dataframe, qi_cols):
        resultado = k_anonimicidad(dummy_dataframe, qi_cols, k=2, supp_level=50)
        assert isinstance(resultado, pd.DataFrame)

    def test_retencion_registros(self, dummy_dataframe, qi_cols):
        resultado = k_anonimicidad(dummy_dataframe, qi_cols, k=2, supp_level=50)
        assert len(resultado) <= len(dummy_dataframe)

    def test_integridad_columnas(self, dummy_dataframe, qi_cols):
        resultado = k_anonimicidad(dummy_dataframe, qi_cols, k=2, supp_level=50)
        assert set(resultado.columns) == set(dummy_dataframe.columns)

    def test_index_limpio(self, dummy_dataframe, qi_cols):
        resultado = k_anonimicidad(dummy_dataframe, qi_cols, k=2, supp_level=50)
        assert "index" not in resultado.columns

    def test_con_mock_anjana(self, dummy_dataframe, qi_cols):
        df_mock = dummy_dataframe.copy()
        df_mock["index"] = range(len(df_mock))

        with patch("utils.anonimizacion._anjana_k_anon", return_value=df_mock) as mock_anon:
            resultado = k_anonimicidad(dummy_dataframe, qi_cols, k=3, supp_level=50)
            mock_anon.assert_called_once()
            _, kwargs = mock_anon.call_args
            assert kwargs["ident"] == []
            assert kwargs["quasi_ident"] == qi_cols
            assert kwargs["k"] == 3
            assert kwargs["supp_level"] == 50
            assert set(kwargs["hierarchies"].keys()) == set(qi_cols)
            assert "index" not in resultado.columns


class TestLDiversidad:
    def test_devuelve_dataframe(self, dummy_dataframe, qi_cols, col_sensible):
        resultado = l_diversidad(dummy_dataframe, qi_cols, col_sensible, k=2, l=2, supp_level=50)
        assert isinstance(resultado, pd.DataFrame)

    def test_retencion_registros(self, dummy_dataframe, qi_cols, col_sensible):
        resultado = l_diversidad(dummy_dataframe, qi_cols, col_sensible, k=2, l=2, supp_level=50)
        assert len(resultado) <= len(dummy_dataframe)

    def test_integridad_columnas(self, dummy_dataframe, qi_cols, col_sensible):
        resultado = l_diversidad(dummy_dataframe, qi_cols, col_sensible, k=2, l=2, supp_level=50)
        assert set(resultado.columns) == set(dummy_dataframe.columns)

    def test_atributo_sensible_preservado(self, dummy_dataframe, qi_cols, col_sensible):
        resultado = l_diversidad(dummy_dataframe, qi_cols, col_sensible, k=2, l=2, supp_level=50)
        assert set(resultado[col_sensible]).issubset(set(dummy_dataframe[col_sensible]))

    def test_con_mock_anjana(self, dummy_dataframe, qi_cols, col_sensible):
        df_mock = dummy_dataframe.copy()
        df_mock["index"] = range(len(df_mock))

        with patch("utils.anonimizacion._anjana_l_div", return_value=df_mock) as mock_ldiv:
            resultado = l_diversidad(dummy_dataframe, qi_cols, col_sensible, k=2, l=2, supp_level=50)
            mock_ldiv.assert_called_once()
            _, kwargs = mock_ldiv.call_args
            assert kwargs["ident"] == []
            assert kwargs["quasi_ident"] == qi_cols
            assert kwargs["sens_att"] == col_sensible
            assert kwargs["k"] == 2
            assert kwargs["l_div"] == 2
            assert kwargs["supp_level"] == 50
            assert set(kwargs["hierarchies"].keys()) == set(qi_cols)
            assert "index" not in resultado.columns


class TestPrivacidadDiferencial:
    def test_devuelve_dataframe(self, dummy_dataframe):
        resultado = privacidad_diferencial(dummy_dataframe, epsilon=1.0, sensibilidad=1.0)
        assert isinstance(resultado, pd.DataFrame)

    def test_misma_forma(self, dummy_dataframe):
        resultado = privacidad_diferencial(dummy_dataframe, epsilon=1.0, sensibilidad=1.0)
        assert resultado.shape == dummy_dataframe.shape

    def test_columnas_no_numericas_intactas(self, dummy_dataframe):
        resultado = privacidad_diferencial(dummy_dataframe, epsilon=1.0, sensibilidad=1.0)
        pd.testing.assert_series_equal(resultado["sexo"], dummy_dataframe["sexo"], check_names=True)
        pd.testing.assert_series_equal(resultado["enfermedad"], dummy_dataframe["enfermedad"], check_names=True)

    def test_metadatos_presupuesto(self, dummy_dataframe):
        resultado = privacidad_diferencial(dummy_dataframe, epsilon=1.5, sensibilidad=2.0)
        assert resultado.attrs["epsilon_total"] == 1.5
        assert resultado.attrs["n_columnas_ruido"] == 2
        assert "epsilon_por_columna" in resultado.attrs
        assert "epsilon_gastado" in resultado.attrs

    def test_con_mock_laplace(self, dummy_dataframe):
        with patch("utils.anonimizacion.LaplaceMechanism") as MockLaplace:
            mock_instance = MagicMock()
            mock_instance.randomise.side_effect = lambda x: x + 0.5
            MockLaplace.return_value = mock_instance

            resultado = privacidad_diferencial(dummy_dataframe, epsilon=1.0, sensibilidad=1.0)
            assert MockLaplace.call_count == 2
            assert isinstance(resultado, pd.DataFrame)

    def test_no_modifica_original(self, dummy_dataframe):
        original = dummy_dataframe.copy()
        privacidad_diferencial(dummy_dataframe, epsilon=1.0, sensibilidad=1.0)
        pd.testing.assert_frame_equal(dummy_dataframe, original)
