PALABRAS_CLAVE_QI = [
    "edad", "age", "sexo", "sex", "genero", "cp", "postal", "municipio",
    "provincia", "region", "comunidad", "pais", "nacionalidad", "estudios",
    "educacion", "ocupacion", "empleo", "civil",
    "EDAD", "SEXO", "CCAA", "PROVRES", "ESTUDIOS", "ECIVIL",
]

PALABRAS_CLAVE_SENSIBLES = [
    "diagnostico", "enfermedad", "patologia", "medicacion", "medicamento",
    "tratamiento", "ingreso", "salud", "health", "disease", "diagnosis",
    "DIAG", "ENFER", "MEDIC", "TRATA",
]


def sugerir_qi_y_sensibles(df, nuniques=None):
    """
    Sugiere qué columnas son cuasi-identificadores y cuáles son sensibles.
    Si se pasan nuniques (dict col→int) no se recalculan, ahorrando tiempo.
    """
    if nuniques is None:
        nuniques = {c: int(df[c].nunique()) for c in df.columns}

    columnas = df.columns.tolist()
    qi, sensibles = [], []

    for columna in columnas:
        columna_min = columna.lower()
        if any(p.lower() in columna_min for p in PALABRAS_CLAVE_SENSIBLES):
            sensibles.append(columna)
        elif any(p.lower() in columna_min for p in PALABRAS_CLAVE_QI):
            qi.append(columna)
        elif df[columna].dtype == object or nuniques[columna] < 25:
            qi.append(columna)
        else:
            sensibles.append(columna)

    if not sensibles and columnas:
        sensibles = [columnas[-1]]

    return qi, sensibles
