"""MALQ · panel de ventas sobre SQLite (Streamlit).

Consulta la base de datos de prueba (data/test.db) y representa los resultados:
KPIs, evolución mensual, productos más vendidos y reparto por categoría.

Arranque:  uv run streamlit run app.py
"""

import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

DB = Path(__file__).parent / "data" / "test.db"

st.set_page_config(page_title="MALQ · ventas", layout="wide")
st.title("MALQ · ventas")
st.caption("Consulta a `data/test.db` · tablas sales_uuid, products_uuid, stores_uuid")


# --- acceso a datos ---------------------------------------------------------


@st.cache_data(show_spinner=False)
def consultar(sql: str, params: tuple = ()) -> pd.DataFrame:
    """Ejecuta una consulta de solo lectura y devuelve un DataFrame."""
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    try:
        return pd.read_sql_query(sql, con, params=list(params))
    finally:
        con.close()


# Vista común: ventas con el nombre de producto y de tienda ya resueltos.
VISTA = """
WITH v AS (
    SELECT s.transaction_id, s.quantity, s.price, s.transaction_date,
           COALESCE(p.product_name, '(sin producto)')  AS producto,
           COALESCE(p.category, '(sin categoría)')     AS categoria,
           COALESCE(t.store_name, '(sin tienda)')      AS tienda,
           COALESCE(t.location, '—')                   AS ciudad
    FROM sales_uuid s
    LEFT JOIN products_uuid p ON p.product_id = s.product_id
    LEFT JOIN stores_uuid  t ON t.store_id   = s.store_id
)
"""

SQL_KPIS = (
    VISTA
    + """
SELECT COUNT(*)                                   AS transacciones,
       COALESCE(SUM(quantity), 0)                 AS unidades,
       COALESCE(SUM(quantity * price), 0)         AS ingresos,
       COALESCE(AVG(quantity * price), 0)         AS ticket
FROM v {filtro}
"""
)
SQL_MENSUAL = (
    VISTA
    + """
SELECT substr(transaction_date, 1, 7) AS mes,
       COUNT(*)                        AS transacciones,
       SUM(quantity * price)           AS ingresos
FROM v
WHERE {cond} AND transaction_date IS NOT NULL AND trim(transaction_date) <> ''
GROUP BY mes
ORDER BY mes
"""
)
SQL_PRODUCTOS = (
    VISTA
    + """
SELECT producto, categoria,
       SUM(quantity) AS unidades, SUM(quantity * price) AS ingresos
FROM v {filtro}
GROUP BY producto, categoria
ORDER BY ingresos DESC
LIMIT 10
"""
)
SQL_CATEGORIAS = (
    VISTA
    + """
SELECT categoria, COUNT(*) AS ventas, SUM(quantity * price) AS ingresos
FROM v {filtro}
GROUP BY categoria
ORDER BY ingresos DESC
"""
)

# --- consultas de la tarea del 6/11/2025 (clase) ----------------------------

# Tarea nº 7: total de ventas por tienda
SQL_TIENDAS = (
    VISTA
    + """
SELECT tienda, ciudad, COUNT(*) AS ventas,
       SUM(quantity) AS unidades, SUM(quantity * price) AS ingresos
FROM v {filtro}
GROUP BY tienda, ciudad
ORDER BY ingresos DESC
"""
)

# Tarea nº 8: productos con más de N unidades vendidas (HAVING)
SQL_MIN_UNIDADES = (
    VISTA
    + """
SELECT producto, SUM(quantity) AS unidades
FROM v {filtro}
GROUP BY producto
HAVING SUM(quantity) > ?
ORDER BY unidades DESC
"""
)

# Tarea nº 2: productos de una categoría, ordenados alfabéticamente
SQL_CATALOGO = """
SELECT product_id, product_name, category
FROM products_uuid
WHERE category = ?
ORDER BY product_name
"""

if not DB.exists():
    st.error(f"No encuentro la base de datos en {DB}. Añádela a la carpeta data/.")
    st.stop()


# --- filtros ----------------------------------------------------------------


@st.cache_data(show_spinner=False)
def opciones() -> tuple[list[str], list[str], dict]:
    """Categorías, tiendas y aviso de filas sin correspondencia."""
    cat = consultar(
        "SELECT DISTINCT p.category FROM products_uuid p ORDER BY 1"
    )["category"].tolist()
    tie = consultar("SELECT DISTINCT store_name FROM stores_uuid ORDER BY 1")[
        "store_name"
    ].tolist()
    huerf = consultar(
        """
        SELECT
          (SELECT COUNT(*) FROM sales_uuid s
             LEFT JOIN products_uuid p ON p.product_id = s.product_id
            WHERE p.product_id IS NULL) AS productos,
          (SELECT COUNT(*) FROM sales_uuid s
             LEFT JOIN stores_uuid t ON t.store_id = s.store_id
            WHERE t.store_id IS NULL) AS tiendas
        """
    ).iloc[0]
    return cat, tie, huerf.to_dict()


categorias, tiendas, huerfanos = opciones()

with st.sidebar:
    st.subheader("Filtros")
    sel_cat = st.multiselect("Categoría", categorias, placeholder="Todas")
    sel_tie = st.multiselect("Tienda", tiendas, placeholder="Todas")
    st.caption(
        f"Sin correspondencia en el catálogo: {int(huerfanos['productos'])} ventas sin producto, "
        f"{int(huerfanos['tiendas'])} sin tienda. Se agrupan como «(sin producto)» / «(sin tienda)»."
    )

condiciones, valores = [], []
if sel_cat:
    condiciones.append(f"categoria IN ({', '.join('?' * len(sel_cat))})")
    valores.extend(sel_cat)
if sel_tie:
    condiciones.append(f"tienda IN ({', '.join('?' * len(sel_tie))})")
    valores.extend(sel_tie)

filtro = ("WHERE " + " AND ".join(condiciones)) if condiciones else ""
params = tuple(valores)

# --- KPIs -------------------------------------------------------------------


def euros(valor: float) -> str:
    """10.733,03 €  (separador de miles con punto, decimales con coma)."""
    texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{texto} €"


kpis = consultar(SQL_KPIS.format(filtro=filtro), params).iloc[0]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Ingresos", euros(kpis["ingresos"]))
c2.metric("Transacciones", f"{int(kpis['transacciones']):,}".replace(",", "."))
c3.metric("Unidades", f"{int(kpis['unidades']):,}".replace(",", "."))
c4.metric("Ticket medio", euros(kpis["ticket"]))

# --- evolución mensual ------------------------------------------------------

st.subheader("Evolución mensual")
# el filtro mensual usa las mismas condiciones, ya dentro de v
mensual = consultar(
    SQL_MENSUAL.format(cond=(" AND ".join(condiciones) or "1=1")), params
)

if mensual.empty:
    st.info("No hay ventas con fecha para los filtros elegidos.")
else:
    mensual = mensual.set_index("mes")
    st.bar_chart(mensual["ingresos"], height=260, color="#0e6f68")

    con_fecha = int(mensual["transacciones"].sum())
    total_filas = int(consultar("SELECT COUNT(*) AS n FROM sales_uuid").iloc[0]["n"])
    st.caption(
        f"{con_fecha} de {total_filas} ventas tienen fecha; el resto no entra en la evolución mensual."
    )

# --- detalle ----------------------------------------------------------------

izq, der = st.columns([3, 2])

with izq:
    st.subheader("Top 10 productos por ingresos")
    productos = consultar(SQL_PRODUCTOS.format(filtro=filtro), params)
    st.dataframe(
        productos,
        hide_index=True,
        width="stretch",
        column_config={
            "ingresos": st.column_config.NumberColumn("Ingresos", format="euro"),
            "unidades": st.column_config.NumberColumn("Unidades", format="%d"),
        },
    )

with der:
    st.subheader("Ingresos por categoría")
    categorias_df = consultar(SQL_CATEGORIAS.format(filtro=filtro), params)
    st.dataframe(
        categorias_df,
        hide_index=True,
        width="stretch",
        column_config={
            "ingresos": st.column_config.NumberColumn("Ingresos", format="euro"),
            "ventas": st.column_config.NumberColumn("Ventas", format="%d"),
        },
    )

# --- consultas de clase (tarea 6/11/2025) ----------------------------------

st.subheader("Consultas de clase")
st.caption("Tomadas de `tarea_6-11-2025.sql`, aplicadas aquí a la misma base de datos.")

vista = st.segmented_control(
    "Consulta de la tarea",
    ["Ventas por tienda", "Más de N unidades", "Catálogo por categoría"],
    default="Ventas por tienda",
    label_visibility="collapsed",
)
vista = vista or "Ventas por tienda"

if vista == "Ventas por tienda":
    tiendas_df = consultar(SQL_TIENDAS.format(filtro=filtro), params)
    st.dataframe(
        tiendas_df,
        hide_index=True,
        width="stretch",
        column_config={
            "ingresos": st.column_config.NumberColumn("Ingresos", format="euro"),
            "unidades": st.column_config.NumberColumn("Unidades", format="%d"),
            "ventas": st.column_config.NumberColumn("Ventas", format="%d"),
        },
    )

elif vista == "Más de N unidades":
    minimo = st.slider("Unidades vendidas como mínimo", 1, 100, 10, step=1)
    unidades_df = consultar(
        SQL_MIN_UNIDADES.format(filtro=filtro), (*valores, minimo)
    )
    if unidades_df.empty:
        st.info(f"Ningún producto llega a {minimo} unidades con los filtros actuales.")
    else:
        st.dataframe(
            unidades_df,
            hide_index=True,
            width="stretch",
            column_config={"unidades": st.column_config.NumberColumn("Unidades", format="%d")},
        )
        st.caption(f"{len(unidades_df)} productos con más de {minimo} unidades (agrupado por nombre).")

else:
    por_defecto = categorias.index("Snacks") if "Snacks" in categorias else 0
    cat_sel = st.selectbox("Categoría", categorias, index=por_defecto)
    st.dataframe(
        consultar(SQL_CATALOGO, (cat_sel,)),
        hide_index=True,
        width="stretch",
    )
    st.caption("Catálogo completo de la categoría: no le afectan los filtros de la barra lateral.")

# --- las consultas, a la vista ---------------------------------------------

with st.expander("Ver las consultas SQL"):
    st.markdown("**KPIs**")
    st.code(SQL_KPIS.format(filtro=filtro).strip(), language="sql")
    st.markdown("**Evolución mensual**")
    st.code(SQL_MENSUAL.format(cond=(" AND ".join(condiciones) or "1=1")).strip(), language="sql")
    st.markdown("**Top productos**")
    st.code(SQL_PRODUCTOS.format(filtro=filtro).strip(), language="sql")
    st.markdown("**Tarea nº 7 — ventas por tienda**")
    st.code(SQL_TIENDAS.format(filtro=filtro).strip(), language="sql")
    st.markdown("**Tarea nº 8 — más de N unidades (HAVING)**")
    st.code(SQL_MIN_UNIDADES.format(filtro=filtro).strip(), language="sql")
    st.markdown("**Tarea nº 2 — catálogo por categoría**")
    st.code(SQL_CATALOGO.strip(), language="sql")
    if params:
        st.caption(f"Parámetros aplicados: {params}")
