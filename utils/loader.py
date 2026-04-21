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


def auto_load(files):
    if not files:
        return None, None, None, None

    ext_map = {}
    for f in files: #guarda en una "libreta" las extensiones de cada fichero para saber los que le hemos pasado y hacer las conversiones respectivas en cada uno 
        ext = f.name.rsplit(".", 1)[-1].lower() if "." in f.name else "sin_ext"
        ext_map[ext] = f

    if "csv" in ext_map:
        f = ext_map["csv"]
        try:
            content = f.read()
            text, enc = decode_bytes(content)
            sep, sep_nombre = detect_separator(text)
            df = pd.read_csv(io.StringIO(text), sep=sep or ",", engine="python")
            return df, f"CSV · {f.name}", f"CSV (separador: {sep_nombre or 'coma'}, codificación: {enc})", None
        except Exception as e:
            return None, None, None, f"Error leyendo CSV: {e}"

    if "xlsx" in ext_map and len(files) == 1: #Si lo que se sube es solo un fichero, se entiende que la tabla con lod datos esta dentro y lo lee
        # si hay mas de un ficheo a parte de este, es porque es el mapa de como estan guardados los datos en el otro fichero y no lo trata en este apartado
        f = ext_map["xlsx"]
        try:
            df = pd.read_excel(f)
            return df, f"Excel · {f.name}", "Excel tabular directo", None
        except Exception as e:
            return None, None, None, f"Error leyendo Excel: {e}"

    if "json" in ext_map:
        f = ext_map["json"]
        try:
            content = f.read()
            text, enc = decode_bytes(content)
            df = pd.read_json(io.StringIO(text))
            return df, f"JSON · {f.name}", f"JSON directo (codificación: {enc})", None
        except Exception as e:
            return None, None, None, f"Error leyendo JSON: {e}"

    if "xml" in ext_map:
        f = ext_map["xml"]
        try:
            content = f.read()
            text, enc = decode_bytes(content)
            df = pd.read_xml(io.StringIO(text))
            return df, f"XML · {f.name}", f"XML directo (codificación: {enc})", None
        except Exception as e:
            return None, None, None, f"Error leyendo XML: {e}"
    #Si llega aqui es porque hay dos ficheros subidos.
    ascii_exts = ["dat", "txt", "asc", "mic", "sin_ext"]
    ascii_file = next((ext_map[e] for e in ascii_exts if e in ext_map), None)


    if ascii_file:
        content = ascii_file.read()
        text, enc = decode_bytes(content)
        if text is None:
            return None, None, None, "No se pudo decodificar el fichero ASCII."

        design_file = ext_map.get("xlsx") or ext_map.get("xls")

        if design_file:
            variables, err = parse_ine_design(design_file)
            if err:
                return None, None, None, f"Error en diseño de registro: {err}"
            ascii_file.seek(0)

            df, err2 = parse_ine_microdata(ascii_file, variables)

            if err2:
                return None, None, None, err2
            return df, f"Microdatos · {ascii_file.name}", f"ASCII ancho fijo + diseño Excel ({len(variables)} variables, codificación: {enc})", None

        else:
            sep, sep_nombre = detect_separator(text)
            if sep:
                try:
                    df = pd.read_csv(io.StringIO(text), sep=sep, engine="python")
                    return df, f"Microdatos · {ascii_file.name}", f"ASCII con separador '{sep_nombre}' detectado (codificación: {enc})", None
                except Exception as e:
                    return None, None, None, f"Error: {e}"
            else:
                return None, None, None, (
                    "⚠️ El fichero parece ser ASCII de ancho fijo sin separadores.\n"
                    "Sube también el **Excel de diseño de registro** junto a este fichero para poder convertirlo."
                )

    return None, None, None, "Formato no reconocido. Formatos soportados: CSV, JSON, XML, Excel, DAT/TXT/ASC (con o sin diseño de registro)."