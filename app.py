import streamlit as st

st.set_page_config(page_title="MALQ", layout="wide")

st.title("MALQ")
st.caption("Panel personal · contenido por definir")

c1, c2, c3 = st.columns(3)
c1.metric("Métrica 1", "—")
c2.metric("Métrica 2", "—")
c3.metric("Métrica 3", "—")

st.divider()

st.markdown(
    """
Aquí irá lo que definamos en clase.

- Los datos y el cálculo: pendientes de decidir.
- Las dependencias se añaden con `uv add <paquete>`.
- El panel se arranca con `uv run streamlit run app.py`.
"""
)
