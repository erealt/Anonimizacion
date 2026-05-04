import io
import pandas as pd
import streamlit as st


# ── Generadores por formato ──────────────────────────────────────────────────

def _a_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")



def _a_json(df: pd.DataFrame) -> bytes:
    return df.to_json(
        orient="records", force_ascii=False, indent=2, date_format="iso"
    ).encode("utf-8")


def _a_xlsx(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Datos")
    return buf.getvalue()


# ── Catálogo público ─────────────────────────────────────────────────────────

FORMATOS: dict[str, dict] = {
    "CSV": {
        "ext":  "csv",
        "mime": "text/csv",
        "fn":   _a_csv,
    },
    
    "JSON": {
        "ext":  "json",
        "mime": "application/json",
        "fn":   _a_json,
    },
    "Excel (.xlsx)": {
        "ext":  "xlsx",
        "mime": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "fn":   _a_xlsx,
    },
}


# ── API ──────────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def exportar(df: pd.DataFrame, formato: str) -> tuple[bytes, str, str]:
    """Convierte ``df`` al formato pedido. Devuelve (bytes, extensión, mime)."""
    info = FORMATOS[formato]
    return info["fn"](df), info["ext"], info["mime"]
