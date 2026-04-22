import streamlit as st
import pandas as pd
#from utils.metricas import 

def render(df, qi_cols, source):
    if df is None:
        st.info("👈 Ve a la pestaña **📥 IMPORTAR DATOS** para cargar un dataset.")
        return


   