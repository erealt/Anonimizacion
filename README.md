# Anonimizacion 

> Trabajo de Fin de Grado · Grado en Ingenieria Informatica  
> Aplicacion web para la anonimización de microdatos bajo los principios de **Privacy by Design**

---

## Descripcion

Este proyecto implementa un prototipo de aplicacion web orientado a la anonimización de microdatos y a la evaluacion del riesgo residual de reidentificacion. La solucion permite cargar conjuntos de datos tabulares, seleccionar cuasi-identificadores y atributos sensibles, aplicar tecnicas formales de protección y analizar el equilibrio entre privacidad y utilidad.

La arquitectura de la aplicacion es **in-memory y stateless**: los datos se procesan en memoria volatil durante la sesion activa y no se persisten de forma estructural en base de datos. Esta decision de diseño se alinea con el principio de minimizacion de datos y con el enfoque de **Privacy by Design** recogido en el RGPD.

---

## Tecnicas de anonimización implementadas

| Tecnica | Parametros | Libreria base | Garantia |
|---|---|---|---|
| **K-Anonimidad** | `k`, `supp_level` | `anjana` | Cada registro queda oculto dentro de un grupo de equivalencia de tamano al menos `k` |
| **L-Diversidad** | `k`, `l`, `supp_level` | `anjana` | Cada grupo equivalente contiene al menos `l` valores sensibles distintos |
| **Privacidad Diferencial** | `epsilon`, `sensibilidad` | `Laplace` | Se inyecta ruido Laplaciano calibrado sobre atributos numericos |

Adicionalmente, el sistema genera metadatos tecnicos sobre la transformacion aplicada, el numero de filas suprimidas y el presupuesto de privacidad consumido.

---

## Metricas de riesgo y auditoria

La aplicacion incorpora una capa de analitica posterior a la anonimización para evaluar el riesgo residual y la calidad del resultado.

| Bloque | Metricas principales |
|---|---|
| **Riesgo de reidentificacion** | Riesgo fiscal, riesgo periodistico, tasa de unicidad, valor real de `k` |
| **Privacidad diferencial** | `epsilon`, numero de columnas perturbadas |
| **Utilidad** | Retencion de registros y comparativa visual entre dataset original y anonimizado |

---

## Formatos de entrada soportados

| Formato | Descripcion |
|---|---|
| `.csv` | Deteccion automatica de separador y lectura tabular |
| `.xlsx` / `.xls` | Carga directa desde hojas Excel |
| `.json` | Lectura de estructuras JSON tabulares |
| `.xml` | Parseo de XML con estructura tabular |
| `.dat` / `.txt` / `.asc` | Microdatos ASCII de ancho fijo con soporte para fichero de diseno |


---

## Exportacion de resultados

Los datos anonimizado se pueden exportar en los siguientes formatos:

- `CSV`
- `JSON`
- `Excel (.xlsx)`

La descarga se bloquea automaticamente cuando el resultado coincide con el dataset original, como medida defensiva para evitar la exportacion accidental de datos sin transformar.

---

## Instalacion

### Opcion A — Ejecucion local

```bash
# 1. Clonar el repositorio
git clone https://github.com/erealt/Anonimizacion.git
cd Anonimizacion

# 2. Crear entorno virtual
python -m venv .venv

# 3. Activar el entorno
source .venv/bin/activate      # Linux / macOS
.venv\Scripts\activate         # Windows

# 4. Instalar dependencias
pip install -r requirements.txt
```

### Opcion B — Docker Compose

```bash
# Construir la imagen y arrancar el contenedor
docker compose up --build

# Siguientes veces (sin reconstruir)
docker compose up

# En segundo plano
docker compose up -d

# Parar
docker compose down
```

---

## Ejecucion

```bash
# Local
streamlit run app.py

# Docker (ver seccion anterior)
docker compose up
```

La aplicacion queda disponible, por defecto, en `http://localhost:8501`.

---

## Flujo de uso

1. **Importar datos**: carga uno o varios ficheros y deja que el sistema detecte automaticamente el formato.
2. **Revisar datos originales**: inspecciona el dataset cargado y ajusta manualmente cuasi-identificadores y atributo sensible si es necesario.
3. **Anonimizar datos**: selecciona la tecnica, configura sus parametros y ejecuta la transformacion.
4. **Analizar metricas**: revisa el riesgo residual, la retencion, el valor real de `k` y las metricas formales de privacidad.
5. **Comparar resultados**: contrasta visualmente el conjunto original frente al anonimizado.

---

## Estructura del proyecto

```text
anonimizacion/
├── app.py
├── README.md
├── requirements.txt
├── runtime.txt
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── .streamlit/
│   └── config.toml
├── tabs/
│   ├── tab_import.py
│   ├── tab_original.py
│   ├── tab_anonimizacion.py
│   ├── tab_metricas.py
│   └── tab_comparativa.py
├── utils/
    ├── anonimizacion.py
    ├── exporter.py
    ├── loader.py
    ├── metricas.py
    └── styles.py

```

### Componentes principales

- `app.py`: punto de entrada de la aplicacion Streamlit y orquestacion de la navegacion.
- `tabs/tab_import.py`: carga de datos y ajuste manual de columnas clave.
- `tabs/tab_original.py`: visualizacion del dataset original.
- `tabs/tab_anonimizacion.py`: ejecucion de K-Anonimidad, L-Diversidad y Privacidad Diferencial.
- `tabs/tab_metricas.py`: analisis de riesgo, utilidad y verificacion formal.
- `tabs/tab_comparativa.py`: comparativa entre dataset original y anonimizado.
- `utils/anonimizacion.py`: nucleo del motor de anonimización.
- `utils/metricas.py`: metricas de riesgo y auditoria con `pycanon`.
- `utils/loader.py`: parseo de formatos de entrada.
- `utils/exporter.py`: serializacion y descarga de resultados.

---

## Dependencias principales

| Libreria | Version minima | Uso |
|---|---|---|
| `streamlit` | 1.35.0 | Interfaz web |
| `pandas` | 2.2.2 | Procesamiento tabular |
| `numpy` | 2.0.2 | Operaciones numericas |
| `matplotlib` | 3.9.0 | Visualizacion de metricas |
| `openpyxl` | 3.1.0 | Lectura y exportacion Excel |
| `pyarrow` | 14.0.0 | Soporte de serializacion tabular |
| `anjana` | 1.1.0 | Algoritmos de K-Anonimidad y L-Diversidad |
| `scikit-learn` | 1.5.0 | Dependencia complementaria del ecosistema analitico |
| `scipy` | 1.11.0 | Calculos estadisticos auxiliares |

---
