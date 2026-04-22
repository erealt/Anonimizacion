# Definición interna de palabras clave para detectar QI y atributos sensibles,
# aunque el usuario pueda modificarlos manualmente después.

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


def sugerir_qi_y_sensibles(df):
    columnas = df.columns.tolist()
    qi, sensibles = [], []
    for columna in columnas:
        columna_min = columna.lower()
        if any(palabra_clave.lower() in columna_min for palabra_clave in PALABRAS_CLAVE_SENSIBLES):
            sensibles.append(columna)
        elif any(palabra_clave.lower() in columna_min for palabra_clave in PALABRAS_CLAVE_QI):
            qi.append(columna)
        elif df[columna].dtype == object or df[columna].nunique() < 25:
            qi.append(columna)
        else:
            sensibles.append(columna)
    if not sensibles and columnas:
        sensibles = [columnas[-1]]
    return qi, sensibles
