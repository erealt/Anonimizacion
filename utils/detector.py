QI_KEYWORDS = [
    "edad", "age", "sexo", "sex", "genero", "cp", "postal", "municipio",
    "provincia", "region", "comunidad", "pais", "nacionalidad", "estudios",
    "educacion", "ocupacion", "empleo", "civil",
    "EDAD", "SEXO", "CCAA", "PROVRES", "ESTUDIOS", "ECIVIL",
]

SENSITIVE_KEYWORDS = [
    "diagnostico", "enfermedad", "patologia", "medicacion", "medicamento",
    "tratamiento", "ingreso", "salud", "health", "disease", "diagnosis",
    "DIAG", "ENFER", "MEDIC", "TRATA",
]


def suggest_qi_and_sensitive(df):
    cols = df.columns.tolist()
    qi, sens = [], []
    for col in cols:
        cl = col.lower()
        if any(kw.lower() in cl for kw in SENSITIVE_KEYWORDS):
            sens.append(col)
        elif any(kw.lower() in cl for kw in QI_KEYWORDS):
            qi.append(col)
        elif df[col].dtype == object or df[col].nunique() < 25:
            qi.append(col)
        else:
            sens.append(col)
    if not sens and cols:
        sens = [cols[-1]]
    return qi, sens
