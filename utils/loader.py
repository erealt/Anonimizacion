import io
import pandas as pd


def decodificar_bytes(contenido):
    for codificacion in ["utf-8", "latin-1", "cp1252"]:
        try:
            return contenido.decode(codificacion), codificacion
        except UnicodeDecodeError:
            continue
    return None, None


def detectar_separador(texto):
    for separador, nombre_separador in [(",", "coma"), (";", "punto y coma"), ("\t", "tabulador"), ("|", "pipe")]:
        try:
            df_prueba = pd.read_csv(io.StringIO(texto), sep=separador, engine="python", nrows=5)
            if len(df_prueba.columns) > 1:
                return separador, nombre_separador
        except Exception:
            continue
    return None, None


def parsear_diseno_ine(fichero_diseno):
    try:
        excel = pd.ExcelFile(fichero_diseno)
        datos_brutos = excel.parse(excel.sheet_names[0], header=None)
        fila_cabecera = 0
        for i, fila in datos_brutos.iterrows():
            fila_texto = " ".join(str(valor).lower() for valor in fila.values)
            if any(palabra in fila_texto for palabra in ["inicio", "posici", "variable", "nombre"]):
                fila_cabecera = i
                break
        df_diseno = excel.parse(excel.sheet_names[0], header=fila_cabecera)
        df_diseno.columns = [str(c).strip().lower() for c in df_diseno.columns]
        df_diseno = df_diseno.dropna(how="all")
        mapa_columnas = {}
        for columna in df_diseno.columns:  # Localiza el rol semántico de cada columna del diseño
            if any(palabra in columna for palabra in ["nombre", "variable", "name"]):
                mapa_columnas["nombre"] = columna
            elif any(palabra in columna for palabra in ["inicio", "start", "pos_ini"]):
                mapa_columnas["inicio"] = columna
            elif any(palabra in columna for palabra in ["fin", "end", "pos_fin", "final"]):
                mapa_columnas["fin"] = columna
            elif any(palabra in columna for palabra in ["longitud", "length", "ancho", "tam"]):
                mapa_columnas["longitud"] = columna
            elif any(palabra in columna for palabra in ["descrip", "etiqueta", "label"]):
                mapa_columnas["descripcion"] = columna
        if "nombre" not in mapa_columnas or "inicio" not in mapa_columnas:
            return None, "No se encontraron columnas de nombre/posición en el diseño."
        variables = []
        for _, fila in df_diseno.iterrows():
            nombre = str(fila[mapa_columnas["nombre"]]).strip()
            if not nombre or nombre.lower() in ["nan", "variable", "nombre"]:
                continue
            try:
                inicio = int(float(fila[mapa_columnas["inicio"]])) - 1
            except Exception:
                continue
            if "fin" in mapa_columnas:
                try:
                    fin = int(float(fila[mapa_columnas["fin"]]))
                except Exception:
                    fin = inicio + 1
            elif "longitud" in mapa_columnas:
                try:
                    fin = inicio + int(float(fila[mapa_columnas["longitud"]]))
                except Exception:
                    fin = inicio + 1
            else:
                fin = inicio + 1
            descripcion_campo = str(fila[mapa_columnas["descripcion"]]).strip() if "descripcion" in mapa_columnas else ""
            variables.append({"nombre": nombre, "inicio": inicio, "fin": fin, "descripcion": descripcion_campo})
        return variables, None
    except Exception as e:
        return None, f"Error leyendo diseño: {e}"


def parsear_microdatos_ine(fichero_datos, variables):
    try:
        contenido = fichero_datos.read() if hasattr(fichero_datos, "read") else open(fichero_datos, "rb").read()
        texto, codificacion = decodificar_bytes(contenido)
        if texto is None:
            return None, "No se pudo decodificar el fichero."
        lineas = [l.rstrip("\n").rstrip("\r") for l in texto.splitlines() if l.strip()]
        registros = []
        for linea in lineas:
            registro = {}
            for variable in variables:
                # Recortamos cada campo según sus posiciones de inicio y fin
                registro[variable["nombre"]] = linea[variable["inicio"]:variable["fin"]].strip() if variable["fin"] <= len(linea) else ""
            registros.append(registro)
        df = pd.DataFrame(registros)  # Los registros en bruto se convierten en una tabla real
        for columna in df.columns:    # Se revisa cada columna para convertir números en tipo numérico
            try:
                df[columna] = pd.to_numeric(df[columna])
            except Exception:
                pass
        return df, None
    except Exception as e:
        return None, f"Error parseando microdatos: {e}"


def es_fichero_diseno(fichero):
    extension = fichero.name.rsplit(".", 1)[-1].lower() if "." in fichero.name else ""
    return extension in ["xlsx", "xls", "ods"]


def es_fichero_datos(fichero):
    extension = fichero.name.rsplit(".", 1)[-1].lower() if "." in fichero.name else ""
    return extension in ["dat", "txt", "asc", "mic", "csv", "sin_ext"]


def carga_automatica(ficheros):
    if not ficheros:
        return None, None, None, None

    # ─── UN SOLO FICHERO ────────────────────────────────────────────
    if len(ficheros) == 1:
        return _cargar_fichero_unico(ficheros[0])

    # ─── DOS FICHEROS ───────────────────────────────────────────────
    if len(ficheros) == 2:
        fichero1, fichero2 = ficheros[0], ficheros[1]

        es_diseno1 = es_fichero_diseno(fichero1)
        es_diseno2 = es_fichero_diseno(fichero2)

        # Caso claro: uno es diseño y el otro no
        if es_diseno1 and not es_diseno2:
            fichero_diseno, fichero_datos = fichero1, fichero2
        elif es_diseno2 and not es_diseno1:
            fichero_diseno, fichero_datos = fichero2, fichero1

        # Ambos parecen diseño o ninguno → intentar por contenido
        else:
            es_datos1 = es_fichero_datos(fichero1)
            es_datos2 = es_fichero_datos(fichero2)

            if es_datos1 and not es_datos2:
                fichero_datos, fichero_diseno = fichero1, fichero2
            elif es_datos2 and not es_datos1:
                fichero_datos, fichero_diseno = fichero2, fichero1
            else:
                return None, None, None, (
                    "⚠️ Se han subido dos ficheros pero no se ha podido "
                    "determinar cuál contiene los datos y cuál el diseño. "
                    "Asegúrate de que el fichero de diseño contiene columnas "
                    "como 'nombre', 'inicio', 'fin' o 'longitud'."
                )

        return _cargar_con_diseno(fichero_datos, fichero_diseno)

    # ─── MÁS DE DOS FICHEROS ────────────────────────────────────────
    return None, None, None, (
        "⚠️ Se han subido más de dos ficheros. "
        "Sube únicamente el fichero de datos y, opcionalmente, "
        "el fichero de diseño de registro."
    )


def _cargar_fichero_unico(fichero):
    """Carga un único fichero detectando su formato automáticamente."""
    extension = fichero.name.rsplit(".", 1)[-1].lower() if "." in fichero.name else "sin_ext"

    if extension == "csv":
        try:
            contenido = fichero.read()
            texto, codificacion = decodificar_bytes(contenido)
            separador, nombre_separador = detectar_separador(texto)
            df = pd.read_csv(io.StringIO(texto), sep=separador or ",", engine="python")
            return df, f"CSV · {fichero.name}", \
                   f"CSV (separador: {nombre_separador or 'coma'}, codificación: {codificacion})", None
        except Exception as e:
            return None, None, None, f"Error leyendo CSV: {e}"

    if extension in ("xlsx", "xls"):
        try:
            df = pd.read_excel(fichero)
            return df, f"Excel · {fichero.name}", "Excel tabular directo", None
        except Exception as e:
            return None, None, None, f"Error leyendo Excel: {e}"

    if extension == "json":
        try:
            contenido = fichero.read()
            texto, codificacion = decodificar_bytes(contenido)
            df = pd.read_json(io.StringIO(texto))
            return df, f"JSON · {fichero.name}", \
                   f"JSON directo (codificación: {codificacion})", None
        except Exception as e:
            return None, None, None, f"Error leyendo JSON: {e}"

    if extension == "xml":
        try:
            contenido = fichero.read()
            texto, codificacion = decodificar_bytes(contenido)
            df = pd.read_xml(io.StringIO(texto))
            return df, f"XML · {fichero.name}", \
                   f"XML directo (codificación: {codificacion})", None
        except Exception as e:
            return None, None, None, f"Error leyendo XML: {e}"

    # ASCII de ancho fijo sin diseño
    extensiones_ascii = ["dat", "txt", "asc", "mic", "sin_ext"]
    if extension in extensiones_ascii:
        try:
            contenido = fichero.read()
            texto, codificacion = decodificar_bytes(contenido)
            if texto is None:
                return None, None, None, "No se pudo decodificar el fichero."
            separador, nombre_separador = detectar_separador(texto)
            if separador:
                df = pd.read_csv(io.StringIO(texto), sep=separador, engine="python")
                return df, f"Microdatos · {fichero.name}", \
                       f"ASCII con separador '{nombre_separador}' (codificación: {codificacion})", None
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


def _cargar_con_diseno(fichero_datos, fichero_diseno):
    """Carga datos usando un fichero de diseño y traduce los nombres de las columnas."""
    try:
        # 1. Parsear el diseño (el mapa semántico)
        fichero_diseno.seek(0)
        variables, error = parsear_diseno_ine(fichero_diseno)  # Extrae el código de cada columna y su descripción real
        if error:
            return None, None, None, f"Error en diseño de registro: {error}"

        extension = fichero_datos.name.rsplit(".", 1)[-1].lower() if "." in fichero_datos.name else ""

        # 2. Cargar los datos (el cuerpo) según su formato
        if extension in ("xlsx", "xls"):
            fichero_datos.seek(0)
            try:
                df = pd.read_excel(fichero_datos)
                metodo = f"Excel tabular con diseño ({len(variables)} variables)"
            except Exception as e:
                return None, None, None, f"Error leyendo datos Excel: {e}"

        else:
            fichero_datos.seek(0)
            contenido = fichero_datos.read()
            texto, codificacion = decodificar_bytes(contenido)
            if texto is None:
                return None, None, None, "No se pudo decodificar el fichero de datos."

            separador, nombre_separador = detectar_separador(texto)
            if separador:
                df = pd.read_csv(io.StringIO(texto), sep=separador, engine="python")
                metodo = f"ASCII separado ('{nombre_separador}') con diseño ({len(variables)} vars, cod: {codificacion})"
            else:
                fichero_datos.seek(0)
                df, error2 = parsear_microdatos_ine(fichero_datos, variables)
                if error2:
                    return None, None, None, error2
                metodo = f"ASCII ancho fijo + diseño ({len(variables)} vars, cod: {codificacion})"

        # 3. Traducción semántica con control de colisiones
        mapa_renombrado = {}
        nombres_usados = set()
        for variable in variables:
            codigo = variable["nombre"]
            # Cogemos la descripción del diccionario, si la hay
            descripcion = variable.get("descripcion", "")

            if descripcion and str(descripcion).lower() not in ["nan", ""]:
                # Limpiamos el texto: quitamos espacios sobrantes y lo cortamos si es larguísimo
                descripcion_limpia = str(descripcion)[:60].strip()

                if descripcion_limpia in nombres_usados:
                    descripcion_limpia = f"{descripcion_limpia} ({codigo})"

                nombres_usados.add(descripcion_limpia)
                mapa_renombrado[codigo] = descripcion_limpia

        if mapa_renombrado:
            df = df.rename(columns=mapa_renombrado)

        # 4. Devolvemos la tabla ya procesada y con nombres descriptivos
        return df, f"Microdatos · {fichero_datos.name}", metodo, None

    except Exception as e:
        return None, None, None, f"Error procesando ficheros: {e}"
