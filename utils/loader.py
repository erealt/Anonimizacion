import io
import pandas as pd

try:
    import pyarrow  # noqa: F401
    _CSV_ENGINE = "pyarrow"
except ImportError:
    _CSV_ENGINE = "c"


# ── Helpers de detección ─────────────────────────────────────────────────────

def _detectar_encoding(contenido_bytes):
    """Detecta encoding probando solo los primeros 1 KB (no el fichero entero)."""
    muestra = contenido_bytes[:1024]
    for enc in ["utf-8", "latin-1", "cp1252", "utf-8-sig"]:
        try:
            muestra.decode(enc)
            return enc
        except UnicodeDecodeError:
            continue
    return "latin-1"


def _leer_csv_rapido(contenido_bytes, separador, encoding):
    
    if _CSV_ENGINE == "pyarrow":
        try:
            return pd.read_csv(
                io.BytesIO(contenido_bytes),
                sep=separador,
                encoding=encoding,
                engine="pyarrow",
            )
        except Exception:
            pass
    return pd.read_csv(
        io.BytesIO(contenido_bytes),
        sep=separador,
        encoding=encoding,
        engine="c",
    )


def _detectar_separador(contenido_bytes, encoding):

    muestra = contenido_bytes[:4096].decode(encoding, errors="replace")
    for sep, nombre in [(",", "coma"), (";", "punto y coma"), ("\t", "tabulador"), ("|", "pipe")]:
        try:
            df = pd.read_csv(io.StringIO(muestra), sep=sep, nrows=5)
            if len(df.columns) > 1:
                return sep, nombre
        except Exception:
            continue
    return None, None


# ── Parsers especializados ───────────────────────────────────────────────────

def parsear_diseno_ine(fichero_diseno):
    try:
        excel = pd.ExcelFile(fichero_diseno)
        datos_brutos = excel.parse(excel.sheet_names[0], header=None)
        fila_cabecera = 0
        for i, fila in datos_brutos.iterrows():
            fila_texto = " ".join(str(v).lower() for v in fila.values)
            if any(p in fila_texto for p in ["inicio", "posici", "variable", "nombre"]):
                fila_cabecera = i
                break
        df_diseno = excel.parse(excel.sheet_names[0], header=fila_cabecera)
        df_diseno.columns = [str(c).strip().lower() for c in df_diseno.columns]
        df_diseno = df_diseno.dropna(how="all")

        mapa = {}
        for col in df_diseno.columns:
            if any(p in col for p in ["nombre", "variable", "name"]):
                mapa["nombre"] = col
            elif any(p in col for p in ["inicio", "start", "pos_ini"]):
                mapa["inicio"] = col
            elif any(p in col for p in ["fin", "end", "pos_fin", "final"]):
                mapa["fin"] = col
            elif any(p in col for p in ["longitud", "length", "ancho", "tam"]):
                mapa["longitud"] = col
            elif any(p in col for p in ["descrip", "etiqueta", "label"]):
                mapa["descripcion"] = col

        if "nombre" not in mapa or "inicio" not in mapa:
            return None, "No se encontraron columnas de nombre/posición en el diseño."

        variables = []
        for _, fila in df_diseno.iterrows():
            nombre = str(fila[mapa["nombre"]]).strip()
            if not nombre or nombre.lower() in ["nan", "variable", "nombre"]:
                continue
            try:
                inicio = int(float(fila[mapa["inicio"]])) - 1
            except Exception:
                continue
            if "fin" in mapa:
                try:
                    fin = int(float(fila[mapa["fin"]]))
                except Exception:
                    fin = inicio + 1
            elif "longitud" in mapa:
                try:
                    fin = inicio + int(float(fila[mapa["longitud"]]))
                except Exception:
                    fin = inicio + 1
            else:
                fin = inicio + 1
            desc = str(fila[mapa["descripcion"]]).strip() if "descripcion" in mapa else ""
            variables.append({"nombre": nombre, "inicio": inicio, "fin": fin, "descripcion": desc})

        return variables, None
    except Exception as e:
        return None, f"Error leyendo diseño: {e}"


def parsear_microdatos_ine(fichero_datos, variables):

    try:
        contenido = fichero_datos.read() if hasattr(fichero_datos, "read") else open(fichero_datos, "rb").read()
        encoding  = _detectar_encoding(contenido)

        colspecs = [(v["inicio"], v["fin"]) for v in variables]
        nombres  = [v["nombre"] for v in variables]

        df = pd.read_fwf(
            io.BytesIO(contenido),
            colspecs=colspecs,
            names=nombres,
            header=None,
            encoding=encoding,
        )
        return df, None
    except Exception as e:
        return None, f"Error parseando microdatos: {e}"


def es_fichero_diseno(fichero):
    ext = fichero.name.rsplit(".", 1)[-1].lower() if "." in fichero.name else ""
    return ext in ["xlsx", "xls", "ods"]


def es_fichero_datos(fichero):
    ext = fichero.name.rsplit(".", 1)[-1].lower() if "." in fichero.name else ""
    return ext in ["dat", "txt", "asc", "mic", "csv", "sin_ext"]


# ── Entrada principal ────────────────────────────────────────────────────────

def carga_automatica(ficheros):
    if not ficheros:
        return None, None, None, None

    if len(ficheros) == 1:
        return _cargar_fichero_unico(ficheros[0])

    if len(ficheros) == 2:
        f1, f2 = ficheros[0], ficheros[1]
        d1, d2 = es_fichero_diseno(f1), es_fichero_diseno(f2)

        if d1 and not d2:
            fichero_diseno, fichero_datos = f1, f2
        elif d2 and not d1:
            fichero_diseno, fichero_datos = f2, f1
        else:
            e1, e2 = es_fichero_datos(f1), es_fichero_datos(f2)
            if e1 and not e2:
                fichero_datos, fichero_diseno = f1, f2
            elif e2 and not e1:
                fichero_datos, fichero_diseno = f2, f1
            else:
                return None, None, None, (
                    "⚠️ No se ha podido determinar cuál fichero contiene los datos "
                    "y cuál el diseño. Asegúrate de que el diseño tiene columnas "
                    "como 'nombre', 'inicio', 'fin' o 'longitud'."
                )
        return _cargar_con_diseno(fichero_datos, fichero_diseno)

    return None, None, None, (
        "⚠️ Sube únicamente el fichero de datos y, opcionalmente, el fichero de diseño."
    )


def _cargar_fichero_unico(fichero):
    ext = fichero.name.rsplit(".", 1)[-1].lower() if "." in fichero.name else "sin_ext"

    # ── CSV ──────────────────────────────────────────────────────────────
    if ext == "csv":
        try:
            contenido = fichero.read()
            encoding  = _detectar_encoding(contenido)
            sep, nombre_sep = _detectar_separador(contenido, encoding)
            df = _leer_csv_rapido(contenido, sep or ",", encoding)
            return df, f"CSV · {fichero.name}", \
                   f"CSV (separador: {nombre_sep or 'coma'}, codificación: {encoding}, motor: {_CSV_ENGINE})", None
        except Exception as e:
            return None, None, None, f"Error leyendo CSV: {e}"

    # ── Excel ─────────────────────────────────────────────────────────────
    if ext in ("xlsx", "xls"):
        try:
            df = pd.read_excel(fichero)
            return df, f"Excel · {fichero.name}", "Excel tabular", None
        except Exception as e:
            return None, None, None, f"Error leyendo Excel: {e}"

    # ── JSON ──────────────────────────────────────────────────────────────
    if ext == "json":
        try:
            contenido = fichero.read()
            encoding  = _detectar_encoding(contenido)
            df = pd.read_json(io.BytesIO(contenido), encoding=encoding)
            return df, f"JSON · {fichero.name}", f"JSON (codificación: {encoding})", None
        except Exception as e:
            return None, None, None, f"Error leyendo JSON: {e}"

    # ── XML ───────────────────────────────────────────────────────────────
    if ext == "xml":
        try:
            contenido = fichero.read()
            encoding  = _detectar_encoding(contenido)
            df = pd.read_xml(io.BytesIO(contenido), encoding=encoding)
            return df, f"XML · {fichero.name}", f"XML (codificación: {encoding})", None
        except Exception as e:
            return None, None, None, f"Error leyendo XML: {e}"

    # ── ASCII (DAT / TXT / ASC …) ─────────────────────────────────────────
    if ext in ("dat", "txt", "asc", "mic", "sin_ext"):
        try:
            contenido = fichero.read()
            encoding  = _detectar_encoding(contenido)
            sep, nombre_sep = _detectar_separador(contenido, encoding)
            if sep:
                df = _leer_csv_rapido(contenido, sep, encoding)
                return df, f"Microdatos · {fichero.name}", \
                       f"ASCII separado por '{nombre_sep}' (codificación: {encoding}, motor: {_CSV_ENGINE})", None
            return None, None, None, (
                "⚠️ El fichero parece ser ASCII de ancho fijo. "
                "Sube también el fichero de diseño de registro."
            )
        except Exception as e:
            return None, None, None, f"Error: {e}"

    return None, None, None, (
        "Formato no reconocido. Formatos soportados: CSV, JSON, XML, Excel, DAT/TXT/ASC."
    )


def _cargar_con_diseno(fichero_datos, fichero_diseno):
    try:
        fichero_diseno.seek(0)
        variables, error = parsear_diseno_ine(fichero_diseno)
        if error:
            return None, None, None, f"Error en diseño de registro: {error}"

        ext = fichero_datos.name.rsplit(".", 1)[-1].lower() if "." in fichero_datos.name else ""

        if ext in ("xlsx", "xls"):
            fichero_datos.seek(0)
            df = pd.read_excel(fichero_datos)
            metodo = f"Excel + diseño ({len(variables)} variables)"
        else:
            fichero_datos.seek(0)
            contenido = fichero_datos.read()
            encoding  = _detectar_encoding(contenido)
            sep, nombre_sep = _detectar_separador(contenido, encoding)

            if sep:
                df = _leer_csv_rapido(contenido, sep, encoding)
                metodo = f"ASCII '{nombre_sep}' + diseño ({len(variables)} vars, motor: {_CSV_ENGINE})"
            else:
                fichero_datos.seek(0)
                df, error2 = parsear_microdatos_ine(fichero_datos, variables)
                if error2:
                    return None, None, None, error2
                metodo = f"ASCII ancho fijo + diseño ({len(variables)} vars)"

        # Renombrar columnas con las descripciones del diseño
        mapa, usados = {}, set()
        for v in variables:
            desc = str(v.get("descripcion", "")).strip()
            if desc and desc.lower() not in ("nan", ""):
                desc = desc[:60]
                if desc in usados:
                    desc = f"{desc} ({v['nombre']})"
                usados.add(desc)
                mapa[v["nombre"]] = desc
        if mapa:
            df = df.rename(columns=mapa)

        return df, f"Microdatos · {fichero_datos.name}", metodo, None

    except Exception as e:
        return None, None, None, f"Error procesando ficheros: {e}"
