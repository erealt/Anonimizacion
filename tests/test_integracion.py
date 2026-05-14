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
        n=500
        return pd.DataFrame({
            "edad": np.random.randint(18, 80, size=n),
            "codigo_postal": np.random.choice(["28001", "28002", "28003", "28004"], size=n),
            "sexo": np.random.choice(["Mujer", "Hombre"], size=n),
            "enferemedad": np.random.choice(["Diabetes", "Hipertension", "Asma"], size=n)
        })
    @pytest.fixture
    def qi(self):
        return ["edad", "codigo_postal", "sexo"]
    @pytest.fixture  
    def col_sensible(self):
        return "enferemedad"
    def test_k_anonimidad(self,dataset_pipeline,qi):
        df_k = k_anonimicidad(dataset_pipeline, qi, k=5, supp_level=30)
        assert isinstance(df_k, pd.DataFrame) # verificamos que la funcion de anonimizacion devuelve un dataset
        assert 0 < len(df_k) <= len(dataset_pipeline) #comprobamos que ese dataset que devuelve no este vacio y que no sea mas grande que el original
        assert set(df_k.columns)==set(dataset_pipeline.columns)# se conservan las mismas columnas que el original
        assert "insex" not in df_k.columns # anjana al anonimizar pone una columna de indice , la quitamos para la salida
    
    def test_l_diversidad(self,dataset_pipeline,qi,col_sensible):
        df_l=l_diversidad(dataset_pipeline, qi, col_sensible, k=3, l=2, supp_level=30)
        assert isinstance(df_l,pd.DataFrame)
        assert 0 < len(df_l) <= len(dataset_pipeline)
        assert set(df_l.columns)==set(dataset_pipeline.columns)
    
    def test_privacidad_diferencial(self,dataset_pipeline):
        df_dp=privacidad_diferencial(dataset_pipeline, epsilon=1.0, sensibilidad=1.0)
        assert isinstance(df_dp,pd.DataFrame)
        assert df_dp.shape == dataset_pipeline.shape
        assert set(df_dp.columns)==set(dataset_pipeline.columns)
class TestIntegracionDatasetGrande:

    def test_k_anonimicidad__verificada_con_pycanon(self, large_dataframe, qi_cols):
        k_solicitado = 5
        df_k = k_anonimicidad(large_dataframe, qi_cols, k=k_solicitado, supp_level=20)
        k_real = int(anonymity.k_anonymity(df_k, qi_cols))
        assert k_real >= k_solicitado

    def test_l_diversidad_verificada_con_pycanon(self, large_dataframe, qi_cols, col_sensible):
        l_solicitado = 2
        df_l = l_diversidad(large_dataframe, qi_cols, col_sensible, k=3, l=l_solicitado, supp_level=30)
        l_real = int(anonymity.l_diversity(df_l, qi_cols, [col_sensible]))
        assert l_real >= l_solicitado

    def test_privacidad_diferencial(self, large_dataframe):
        df_dp = privacidad_diferencial(large_dataframe, epsilon=1.0, sensibilidad=1.0)
        assert df_dp.shape == large_dataframe.shape
        assert "epsilon_total" in df_dp.attrs
