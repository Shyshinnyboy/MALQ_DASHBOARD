"""Programa de prueba de Streamlit: comprueba que todo responde.

Arranque:  uv run streamlit run app.py
"""

import math

import streamlit as st

st.set_page_config(page_title="MALQ · prueba", layout="centered")
st.title("Prueba de Streamlit")
st.caption("Un programa pequeño para comprobar que la instalación funciona.")

# 1. Entrada de texto
nombre = st.text_input("¿Cómo te llamas?", placeholder="Escribe tu nombre")
if nombre.strip():
    st.write(f"Hola, **{nombre.strip()}**. El texto llega al programa correctamente.")

# 2. Estado que sobrevive a la recarga
if "pulsaciones" not in st.session_state:
    st.session_state.pulsaciones = 0

col_boton, col_cuenta = st.columns(2)
if col_boton.button("Púlsame", type="primary"):
    st.session_state.pulsaciones += 1
col_cuenta.metric("Veces pulsado", st.session_state.pulsaciones)

# 3. Cálculo + gráfica
st.divider()
amplitud = st.slider("Amplitud de la curva", min_value=1, max_value=10, value=3)
puntos = [amplitud * math.sin(i / 10) for i in range(0, 63)]
st.line_chart({"valor": puntos}, height=220)

# 4. Tabla calculada
if st.checkbox("Ver los primeros valores"):
    st.dataframe(
        {"paso": list(range(10)), "valor": [round(p, 3) for p in puntos[:10]]},
        hide_index=True,
    )

st.success("Todo listo: widgets, estado, cálculo y gráfica responden.")
