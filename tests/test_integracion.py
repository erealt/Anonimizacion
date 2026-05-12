"""
Tests de integracion del pipeline completo.
"""

import numpy as np
import pandas as pd
import pytest
from pycanon import anonymity

from utils.anonimizacion import (
    _generar_jerarquias,
    _preparar_df,
    k_anonimicidad,
    l_diversidad,
    privacidad_diferencial,
)


class TestPipelineCompleto:
    @pytest.fixture
    def dataset_pipeline(self):
        np.random.seed(777)
        n = 500
        return pd.DataFrame({
            "edad": np.random.randint(18, 80, n),
            "codigo_postal": np.random.choice([28001, 28002, 28003, 28004, 28005], n),
            "sexo": np.random.choice(["Hombre", "Mujer"], n),
            "enfermedad": np.random.choice(["Gripe", "Diabetes", "Cancer", "Hipertension", "Asma"], n),
        })

    @pytest.fixture
    def qi(self):
        return ["edad", "codigo_postal", "sexo"]

    @pytest.fixture
    def sensible(self):
        return "enfermedad"

    def test_etapa1_k_anonimicidad(self, dataset_pipeline, qi):
        df_k = k_anonimicidad(dataset_pipeline, qi, k=3, supp_level=30)
        assert isinstance(df_k, pd.DataFrame)
        assert 0 < len(df_k) <= len(dataset_pipeline)
        assert set(df_k.columns) == set(dataset_pipeline.columns)
        assert "index" not in df_k.columns

    def test_etapa2_l_diversidad(self, dataset_pipeline, qi, sensible):
        df_l = l_diversidad(dataset_pipeline, qi, sensible, k=3, l=2, supp_level=30)
        assert isinstance(df_l, pd.DataFrame)
        assert 0 < len(df_l) <= len(dataset_pipeline)
        assert set(df_l.columns) == set(dataset_pipeline.columns)

    def test_etapa3_privacidad_diferencial(self, dataset_pipeline):
        df_dp = privacidad_diferencial(dataset_pipeline, epsilon=1.0, sensibilidad=1.0)
        assert isinstance(df_dp, pd.DataFrame)
        assert df_dp.shape == dataset_pipeline.shape
        assert set(df_dp.columns) == set(dataset_pipeline.columns)

    def test_pipeline_completo_tres_etapas(self, dataset_pipeline, qi, sensible):
        df_paso1 = k_anonimicidad(dataset_pipeline, qi, k=2, supp_level=40)
        df_paso2 = l_diversidad(df_paso1, qi, sensible, k=2, l=2, supp_level=40)
        df_paso3 = privacidad_diferencial(df_paso2, epsilon=1.0, sensibilidad=1.0)

        assert set(df_paso3.columns) == set(dataset_pipeline.columns)
        assert len(df_paso3) == len(df_paso2)

    def test_no_corrupcion_tras_pipeline(self, dataset_pipeline, qi):
        df_k = k_anonimicidad(dataset_pipeline, qi, k=3, supp_level=30)
        df_final = privacidad_diferencial(df_k, epsilon=1.0, sensibilidad=1.0)

        for col in df_final.select_dtypes(include=[np.number]).columns:
            assert not np.any(np.isinf(df_final[col].dropna().values))

        for col in df_final.select_dtypes(exclude=[np.number]).columns:
            assert df_final[col].apply(lambda x: isinstance(x, str)).all()


class TestIntegracionJerarquias:
    @pytest.fixture
    def dataset_jer(self):
        np.random.seed(42)
        return pd.DataFrame({
            "edad": np.random.randint(18, 80, 300),
            "ciudad": np.random.choice(["Madrid", "Barcelona", "Sevilla", "Valencia"], 300),
        })

    def test_flujo_jerarquias_completo(self, dataset_jer):
        qi = ["edad", "ciudad"]
        df_clean = _preparar_df(dataset_jer, qi)
        h = _generar_jerarquias(df_clean, qi)

        assert len(h["edad"][0]) == len(dataset_jer)
        assert "[" in str(h["edad"][1][0]) and ")" in str(h["edad"][1][0])
        assert any("*" in str(v) for v in h["ciudad"][1])

    def test_jerarquias_compatibles_con_anjana(self, dataset_jer):
        qi = ["edad", "ciudad"]
        df_k = k_anonimicidad(dataset_jer.assign(enfermedad="Gripe"), qi, k=2, supp_level=50)
        assert isinstance(df_k, pd.DataFrame)
        assert "index" not in df_k.columns


class TestIntegracionDatasetGrande:
    def test_k_anonimicidad_grande(self, large_dataframe, qi_cols):
        df_k = k_anonimicidad(large_dataframe, qi_cols, k=5, supp_level=20)
        assert isinstance(df_k, pd.DataFrame)
        assert len(df_k) > 0
        assert set(df_k.columns) == set(large_dataframe.columns)
        k_real = df_k.groupby(qi_cols, dropna=False).size().min()
        assert k_real >= 5

    def test_l_diversidad_grande(self, large_dataframe, qi_cols, col_sensible):
        df_l = l_diversidad(large_dataframe, qi_cols, col_sensible, k=3, l=2, supp_level=30)
        assert isinstance(df_l, pd.DataFrame)
        assert len(df_l) > 0
        assert set(df_l.columns) == set(large_dataframe.columns)

    def test_k_anonimicidad_grande_verificada_con_pycanon(self, large_dataframe, qi_cols):
        k_solicitado = 5
        df_k = k_anonimicidad(large_dataframe, qi_cols, k=k_solicitado, supp_level=20)
        k_real = int(anonymity.k_anonymity(df_k, qi_cols))
        assert k_real >= k_solicitado

    def test_l_diversidad_grande_verificada_con_pycanon(self, large_dataframe, qi_cols, col_sensible):
        l_solicitado = 2
        df_l = l_diversidad(large_dataframe, qi_cols, col_sensible, k=3, l=l_solicitado, supp_level=30)
        l_real = int(anonymity.l_diversity(df_l, qi_cols, [col_sensible]))
        assert l_real >= l_solicitado

    def test_privacidad_diferencial_grande(self, large_dataframe):
        df_dp = privacidad_diferencial(large_dataframe, epsilon=1.0, sensibilidad=1.0)
        assert df_dp.shape == large_dataframe.shape
        assert "epsilon_total" in df_dp.attrs
