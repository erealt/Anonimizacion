import numpy as np
import pandas as pd

def generalizacion(series,bins=5):
    if pd.api.types.is_numeric_dtype(series): # si los datos son números 
        try:
            return pd.cut(series, bins=bins).astype(str) #cut coge el valor mas bajo y el mas alto de esa columna y divide segun los bins, es decir ve cuantas "cajas" hay que hacer
        except Exception:
            return series.astype(str)
    else:
        return series.astype(str).apply(lambda x: x[:-1] + "*" if len(x) > 1 else "*") # si es texto lo que hacemos es coge todo menos el ultimo caracter y en la posicion final ponemos un *

def k_anonimicidad(df,qi_cols,k):
    anon=df.copy();
    for col in qi_cols:
        anon[col]=generalizacion(anon[col])
    sizes=anon.groupby(qi_cols,dropna=False).transform("count").iloc[:,0] # dropna:descarta los vacios , lo ponemos a False ya que por defecto en pandas esta a true.
    #Es decir si estamos contando por Ciudades y hay algún campo vacio donde no lo pone que no los elimine de ese recuento
    return anon[sizes >= k].reset_index(drop=True)  # supresión de registros que no cumplen k

def l_diversidad(df,qi_cols,col_sensibles,k,l):
    anon= df.copy()
    for col in qi_cols:
        anon[col]=generalizacion(anon[col])
    return anon.groupby(qi_cols,group_keys=False,dropna=False).filter(
         lambda g: len(g) >= k and g[col_sensibles].nunique() >= l
    ).reset_index(drop=True)

def privacidad_diferencial(df,epsilon,sensibilidad):
    anon = df.copy()
    scale = sensibilidad / epsilon
    for col in df.select_dtypes(include=[np.number]).columns:
        anon[col] = anon[col] + np.random.laplace(0, scale, len(df))
    return anon

