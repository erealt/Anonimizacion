import sys
import pandas as pd
 
RUTA_MICRODATOS = r"C:\Users\ereal1\Desktop\estela\Datasets\Adultos_Encuesta Nacional de Salud - Año 2017\MICRODAT.CA.txt"
RUTA_DISENO     = r"C:\Users\ereal1\Desktop\estela\Datasets\Adultos_Encuesta Nacional de Salud - Año 2017\Diseño registro ADULTO ENSE 2017_PUBLICACIÓN.xlsx"
RUTA_SALIDA     = r"C:\Users\ereal1\Desktop\estela\Datasets\Adultos_Encuesta Nacional de Salud - Año 2017\resultados.csv"

def parse_design(design_path): # leer el Excel de diseño

    print(f"[1/3] Leyendo diseño de registro: {design_path}")

    xl = pd.ExcelFile(design_path) #abre el Excel
    raw = xl.parse(xl.sheet_names[0], header=None)#Lee la primera hoja

    # Detectar fila de cabecera
    header_row = 0
    for i, row in raw.iterrows():
        row_str = " ".join(str(v).lower() for v in row.values) # recorre fila por fila y convierte todo el contenido de esa fila a texto en minúsculas
        if any(w in row_str for w in ["inicio", "posici", "variable", "nombre"]):
            header_row = i
            break

    df_design = xl.parse(xl.sheet_names[0], header=header_row)
    df_design.columns = [str(c).strip().lower() for c in df_design.columns]
    df_design = df_design.dropna(how="all")

    print(f"    Cabecera en fila {header_row} | Columnas: {list(df_design.columns)}")

    # Mapear columnas
    col_map = {}
    for col in df_design.columns:
        if any(w in col for w in ["nombre", "variable", "name"]):
            col_map["name"] = col
        elif any(w in col for w in ["inicio", "start", "pos_ini"]):
            col_map["start"] = col
        elif any(w in col for w in ["fin", "end", "pos_fin", "final"]):
            col_map["end"] = col
        elif any(w in col for w in ["longitud", "length", "ancho", "tam"]):
            col_map["length"] = col
        elif any(w in col for w in ["descrip", "etiqueta", "label"]):
            col_map["desc"] = col

    if "name" not in col_map:
        sys.exit("ERROR: No se encontró columna de nombre de variable.")
    if "start" not in col_map:
        sys.exit("ERROR: No se encontró columna de posición de inicio.")

    variables = []
    for _, row in df_design.iterrows():
        name = str(row[col_map["name"]]).strip()
        if not name or name.lower() in ["nan", "variable", "nombre"]:
            continue
        try:
            start = int(float(row[col_map["start"]])) - 1  # 0-indexed
        except (ValueError, TypeError):
            continue
        if "end" in col_map:
            try:
                end = int(float(row[col_map["end"]]))
            except (ValueError, TypeError):
                end = start + 1
        elif "length" in col_map:
            try:
                end = start + int(float(row[col_map["length"]]))
            except (ValueError, TypeError):
                end = start + 1
        else:
            end = start + 1

        desc = str(row[col_map["desc"]]).strip() if "desc" in col_map else ""
        variables.append({"name": name, "start": start, "end": end, "description": desc})

    print(f"    Variables detectadas: {len(variables)}")
    return variables


def parse_microdata(micro_path, variables):  # leemos el texto línea a línea
    print(f"[2/3] Leyendo microdatos: {micro_path}")

    lines = None
    for enc in ["utf-8", "latin-1", "cp1252"]:
        try:
            with open(micro_path, "r", encoding=enc) as f:
                lines = [l.rstrip("\n").rstrip("\r") for l in f if l.strip()]
            print(f"    Codificación: {enc} | Registros: {len(lines)}")
            break
        except UnicodeDecodeError:
            continue
        except FileNotFoundError:
            sys.exit(f"ERROR: No se encontró el fichero '{micro_path}'.")

    if lines is None:
        sys.exit("ERROR: No se pudo leer el fichero de microdatos.")

    records = []
    for line in lines:
        record = {}
        for var in variables:
            record[var["name"]] = line[var["start"]:var["end"]].strip() if var["end"] <= len(line) else ""
        records.append(record)

    df = pd.DataFrame(records)

    # Convertir columnas numéricas
    converted = 0
    for col in df.columns:
        try:
            df[col] = pd.to_numeric(df[col])
            converted += 1
        except (ValueError, TypeError):
            pass
    print(f"    Columnas numéricas: {converted}/{len(df.columns)}")
    return df


def save_csv(df, out_path):
    print(f"[3/3] Guardando CSV: {out_path}")
    df.to_csv(out_path, index=False, encoding="utf-8")
    print(f"    ✅ Listo — {len(df)} registros · {len(df.columns)} columnas")


if __name__ == "__main__":
    print("=" * 50)
    print("  Conversor Microdatos INE → CSV")
    print("=" * 50)

    variables = parse_design(RUTA_DISENO)
    df = parse_microdata(RUTA_MICRODATOS, variables)
    save_csv(df, RUTA_SALIDA)

    print("\n── Vista previa (5 primeras filas) ───────────────")
    print(df.head().to_string())
    print("\n✅ Conversión completada.")