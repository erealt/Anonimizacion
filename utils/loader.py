import io
import pandas as pd


def decode_bytes(content):
    for enc in ["utf-8", "latin-1", "cp1252"]:
        try:
            return content.decode(enc), enc
        except UnicodeDecodeError:
            continue
    return None, None


def detect_separator(text):
    for sep, nombre in [(",", "coma"), (";", "punto y coma"), ("\t", "tabulador"), ("|", "pipe")]:
        try:
            df_try = pd.read_csv(io.StringIO(text), sep=sep, engine="python", nrows=5)
            if len(df_try.columns) > 1:
                return sep, nombre
        except Exception:
            continue
    return None, None


def parse_ine_design(design_file):
    try:
        xl = pd.ExcelFile(design_file)
        raw = xl.parse(xl.sheet_names[0], header=None)
        header_row = 0
        for i, row in raw.iterrows():
            row_str = " ".join(str(v).lower() for v in row.values)
            if any(w in row_str for w in ["inicio", "posici", "variable", "nombre"]):
                header_row = i
                break
        df_d = xl.parse(xl.sheet_names[0], header=header_row)
        df_d.columns = [str(c).strip().lower() for c in df_d.columns]
        df_d = df_d.dropna(how="all")
        col_map = {}
        for col in df_d.columns: #Localiza por cada fila del e
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
        if "name" not in col_map or "start" not in col_map:
            return None, "No se encontraron columnas de nombre/posición en el diseño."
        variables = []
        for _, row in df_d.iterrows():
            name = str(row[col_map["name"]]).strip()
            if not name or name.lower() in ["nan", "variable", "nombre"]:
                continue
            try:
                start = int(float(row[col_map["start"]])) - 1
            except Exception:
                continue
            if "end" in col_map:
                try:
                    end = int(float(row[col_map["end"]]))
                except Exception:
                    end = start + 1
            elif "length" in col_map:
                try:
                    end = start + int(float(row[col_map["length"]]))
                except Exception:
                    end = start + 1
            else:
                end = start + 1
            desc = str(row[col_map["desc"]]).strip() if "desc" in col_map else ""
            variables.append({"name": name, "start": start, "end": end, "description": desc})
        return variables, None
    except Exception as e:
        return None, f"Error leyendo diseño: {e}"


def parse_ine_microdata(txt_file, variables):
    try:
        content = txt_file.read() if hasattr(txt_file, "read") else open(txt_file, "rb").read()
        text, enc = decode_bytes(content)
        if text is None:
            return None, "No se pudo decodificar el fichero."
        lines = [l.rstrip("\n").rstrip("\r") for l in text.splitlines() if l.strip()]
        records = []
        for line in lines:
            record = {}
            for var in variables:
                record[var["name"]] = line[var["start"]:var["end"]].strip() if var["end"] <= len(line) else ""
            records.append(record)
        df = pd.DataFrame(records) # esos datos que se guardan, se convierten en una tabla real.
        for col in df.columns:# Se revisa una por una todas las columnas 
            try:
                df[col] = pd.to_numeric(df[col]) #con esto convertimos todos los "numeros" en numerico , para luego poder trabajar con ellos 
            except Exception:
                pass
        return df, None
    except Exception as e:
        return None, f"Error parseando microdatos: {e}"
def is_design_file(f):
    ext = f.name.rsplit(".", 1)[-1].lower() if "." in f.name else ""
    return ext in ["xlsx", "xls", "ods"]

def is_data_file(f):
    ext = f.name.rsplit(".", 1)[-1].lower() if "." in f.name else ""
    return ext in ["dat", "txt", "asc", "mic", "csv", "sin_ext"]

def auto_load(files):
    if not files:
        return None, None, None, None

    # ─── UN SOLO FICHERO ────────────────────────────────────────────
    if len(files) == 1:
        return _load_single(files[0])

    # ─── DOS FICHEROS ───────────────────────────────────────────────
    if len(files) == 2:
        f1, f2 = files[0], files[1]

        d1 = is_design_file(f1)
        d2 = is_design_file(f2)

        # Caso claro: uno es diseño y el otro no
        if d1 and not d2:
            design_file, data_file = f1, f2
        elif d2 and not d1:
            design_file, data_file = f2, f1

        # Ambos parecen diseño o ninguno → intentar por contenido
        else:
            t1 = is_data_file(f1)
            t2 = is_data_file(f2)

            if t1 and not t2:
                data_file, design_file = f1, f2
            elif t2 and not t1:
                data_file, design_file = f2, f1
            else:
                return None, None, None, (
                    "⚠️ Se han subido dos ficheros pero no se ha podido "
                    "determinar cuál contiene los datos y cuál el diseño. "
                    "Asegúrate de que el fichero de diseño contiene columnas "
                    "como 'nombre', 'inicio', 'fin' o 'longitud'."
                )

        return _load_with_design(data_file, design_file)

    # ─── MÁS DE DOS FICHEROS ────────────────────────────────────────
    return None, None, None, (
        "⚠️ Se han subido más de dos ficheros. "
        "Sube únicamente el fichero de datos y, opcionalmente, "
        "el fichero de diseño de registro."
    )


def _load_single(f):
    """Carga un único fichero detectando su formato."""
    ext = f.name.rsplit(".", 1)[-1].lower() if "." in f.name else "sin_ext" #mira la extension del fichero

    if ext == "csv":
        try:
            content = f.read()
            text, enc = decode_bytes(content)
            sep, sep_nombre = detect_separator(text)
            df = pd.read_csv(io.StringIO(text), sep=sep or ",", engine="python")
            return df, f"CSV · {f.name}", \
                   f"CSV (separador: {sep_nombre or 'coma'}, codificación: {enc})", None
        except Exception as e:
            return None, None, None, f"Error leyendo CSV: {e}"

    if ext in ("xlsx", "xls"):
        try:
            df = pd.read_excel(f)
            return df, f"Excel · {f.name}", "Excel tabular directo", None
        except Exception as e:
            return None, None, None, f"Error leyendo Excel: {e}"

    if ext == "json":
        try:
            content = f.read()
            text, enc = decode_bytes(content)
            df = pd.read_json(io.StringIO(text))
            return df, f"JSON · {f.name}", \
                   f"JSON directo (codificación: {enc})", None
        except Exception as e:
            return None, None, None, f"Error leyendo JSON: {e}"

    if ext == "xml":
        try:
            content = f.read()
            text, enc = decode_bytes(content)
            df = pd.read_xml(io.StringIO(text))
            return df, f"XML · {f.name}", \
                   f"XML directo (codificación: {enc})", None
        except Exception as e:
            return None, None, None, f"Error leyendo XML: {e}"

    # ASCII ancho fijo sin diseño
    ascii_exts = ["dat", "txt", "asc", "mic", "sin_ext"]
    if ext in ascii_exts:
        try:
            content = f.read()
            text, enc = decode_bytes(content)
            if text is None:
                return None, None, None, "No se pudo decodificar el fichero."
            sep, sep_nombre = detect_separator(text)
            if sep:
                df = pd.read_csv(io.StringIO(text), sep=sep, engine="python")
                return df, f"Microdatos · {f.name}", \
                       f"ASCII con separador '{sep_nombre}' (codificación: {enc})", None
            else:
                return None, None, None, (
                    "⚠️ El fichero parece ser ASCII de ancho fijo sin separadores. "
                    "Sube también el fichero de diseño de registro junto a este."
                )
        except Exception as e:
            return None, None, None, f"Error: {e}"

    return None, None, None, (
        "Formato no reconocido. Formatos soportados: "
        "CSV, JSON, XML, Excel, DAT/TXT/ASC."
    )


def _load_with_design(data_file, design_file):
    """Carga datos usando un fichero de diseño y traduce los nombres de las columnas."""
    try:
        # 1. Parsear el diseño (el mapa)
        design_file.seek(0)
        variables, err = parse_ine_design(design_file) # extrae una lista llamada variable, donde contiene el codigo de cada columna y su descripcion real
        if err:
            return None, None, None, f"Error en diseño de registro: {err}"

        ext = data_file.name.rsplit(".", 1)[-1].lower() if "." in data_file.name else ""

        # 2. Cargar los datos (el cuerpo) según su formato
        if ext in ("xlsx", "xls"):
            data_file.seek(0)
            try:
                df = pd.read_excel(data_file)
                metodo = f"Excel tabular con diseño ({len(variables)} variables)"
            except Exception as e:
                return None, None, None, f"Error leyendo datos Excel: {e}"
                
        else:
            data_file.seek(0)
            content = data_file.read()
            text, enc = decode_bytes(content)
            if text is None:
                return None, None, None, "No se pudo decodificar el fichero de datos."

            sep, sep_nombre = detect_separator(text)
            if sep:
                df = pd.read_csv(io.StringIO(text), sep=sep, engine="python")
                metodo = f"ASCII separado ('{sep_nombre}') con diseño ({len(variables)} vars, cod: {enc})"
            else:
                data_file.seek(0)
                df, err2 = parse_ine_microdata(data_file, variables)
                if err2:
                    return None, None, None, err2
                metodo = f"ASCII ancho fijo + diseño ({len(variables)} vars, cod: {enc})"

        
        rename_map = {}
        nombres_usados = set()
        for var in variables:
            codigo = var["name"]
            # Cogemos la descripción, si la hay
            descripcion = var.get("description", "") 
            
            if descripcion and str(descripcion).lower() not in ["nan", ""]:
                # Limpiamos el texto: quitamos espacios sobrantes y lo cortamos si es larguísimo
                descripcion_limpia = str(descripcion)[:60].strip()

                if descripcion_limpia in nombres_usados:
                    descripcion_limpia = f"{descripcion_limpia} ({codigo})"
                
                nombres_usados.add(descripcion_limpia)
                rename_map[codigo] = descripcion_limpia
        
       
        if rename_map:
            df = df.rename(columns=rename_map)
     

        # 4. Devolvemos la tabla ya procesada y con nombres bonitos
        return df, f"Microdatos · {data_file.name}", metodo, None

    except Exception as e:
        return None, None, None, f"Error procesando ficheros: {e}"