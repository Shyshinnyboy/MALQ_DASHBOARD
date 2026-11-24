# MALQ_DASHBOARD

Panel personal de ventas: Streamlit + SQLite. Consulta la base de datos de prueba
`data/test.db` y muestra ingresos, evolución mensual, productos más vendidos,
reparto por categoría y las consultas de la tarea del 6/11, con filtros por
categoría y tienda.

## Arrancar

```bash
uv run streamlit run app.py
```

## Estructura

```
app.py            panel y consultas SQL
data/test.db      base de datos (sales_uuid, products_uuid, stores_uuid)
src/              paquete del proyecto
pyproject.toml    dependencias (streamlit) y metadatos
uv.lock           versiones exactas de las dependencias
```

## Añadir dependencias

```bash
uv add <paquete>
```
