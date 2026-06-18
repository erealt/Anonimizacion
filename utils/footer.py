import base64
from pathlib import Path

import streamlit as st


FOOTER_IMAGE = Path(__file__).resolve().parents[1] / "data" / "footer.png"


def render_footer():
    """Renderiza el footer institucional si la imagen existe."""
    if not FOOTER_IMAGE.exists():
        return

    image_b64 = base64.b64encode(FOOTER_IMAGE.read_bytes()).decode("utf-8")
    st.markdown(
        f"""
        <div style='margin-top:2.5rem;padding-top:1rem;border-top:1px solid #e5e7eb;'>
            <img
                src="data:image/png;base64,{image_b64}"
                alt="Footer"
                style="display:block;width:100%;height:auto;border-radius:8px;"
            />
        </div>
        """,
        unsafe_allow_html=True,
    )
