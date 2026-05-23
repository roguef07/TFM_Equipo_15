-- ============================================================
-- DATA MART – Customer Shopping Analytics
-- Fuente: tabla customer_sales_gold (cargada por 03_load_postgres.py)
-- ============================================================

-- Vista 1: Ventas agregadas por categoría y mes
CREATE OR REPLACE VIEW dm_ventas_por_categoria_mes AS
SELECT
    DATE_TRUNC('month', invoice_date)::DATE                             AS mes,
    category                                                            AS categoria,
    ROUND(SUM(ventas_totales)::NUMERIC, 2)                              AS ventas_totales,
    SUM(unidades_vendidas)                                              AS unidades_vendidas,
    SUM(cantidad_transacciones)                                         AS transacciones,
    ROUND(SUM(ventas_totales)::NUMERIC
          / NULLIF(SUM(cantidad_transacciones), 0), 2)                  AS ticket_promedio
FROM customer_sales_gold
GROUP BY 1, 2;

-- Vista 2: Ranking de centros comerciales por ventas totales
CREATE OR REPLACE VIEW dm_ranking_shopping_mall AS
SELECT
    shopping_mall,
    ROUND(SUM(ventas_totales)::NUMERIC, 2)                              AS ventas_totales,
    SUM(unidades_vendidas)                                              AS unidades_vendidas,
    SUM(cantidad_transacciones)                                         AS transacciones,
    ROUND(SUM(ventas_totales)::NUMERIC
          / NULLIF(SUM(cantidad_transacciones), 0), 2)                  AS ticket_promedio
FROM customer_sales_gold
GROUP BY shopping_mall;

-- Vista 3: Evolución de ventas diarias (serie temporal para forecasting)
CREATE OR REPLACE VIEW dm_evolucion_diaria AS
SELECT
    invoice_date                                                        AS fecha,
    ROUND(SUM(ventas_totales)::NUMERIC, 2)                              AS ventas_totales,
    SUM(unidades_vendidas)                                              AS unidades_vendidas,
    SUM(cantidad_transacciones)                                         AS transacciones
FROM customer_sales_gold
GROUP BY invoice_date;

-- Vista 4: Tabla resumen para dashboard BI (granularidad: fecha + categoría + mall)
CREATE OR REPLACE VIEW dm_dashboard_bi AS
SELECT
    invoice_date                                                        AS fecha,
    category                                                            AS categoria,
    shopping_mall                                                       AS centro_comercial,
    ROUND(ventas_totales::NUMERIC, 2)                                   AS ventas_totales,
    unidades_vendidas,
    cantidad_transacciones                                              AS transacciones,
    ROUND(ticket_promedio::NUMERIC, 2)                                  AS ticket_promedio
FROM customer_sales_gold;
