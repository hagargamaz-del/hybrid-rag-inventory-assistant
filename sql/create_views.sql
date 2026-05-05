CREATE OR REPLACE VIEW vw_sales_by_product AS
SELECT
    p.product_id,
    p.product_name,
    p.category,
    s.supplier_name,
    SUM(oi.quantity) AS total_units_sold,
    ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount_pct / 100)), 2) AS net_revenue,
    ROUND(SUM((oi.quantity * oi.unit_price * (1 - oi.discount_pct / 100)) - (oi.quantity * p.unit_cost)), 2) AS estimated_profit
FROM fact_order_items oi
JOIN fact_orders o
    ON oi.order_id = o.order_id
JOIN dim_products p
    ON oi.product_id = p.product_id
JOIN dim_suppliers s
    ON p.supplier_id = s.supplier_id
WHERE o.order_status IN ('completed', 'shipped')
GROUP BY
    p.product_id,
    p.product_name,
    p.category,
    s.supplier_name;


CREATE OR REPLACE VIEW vw_current_stock AS
SELECT
    p.product_id,
    p.product_name,
    p.category,
    p.reorder_level,
    p.target_stock,
    COALESCE(
        SUM(
            CASE
                WHEN m.movement_type = 'RESTOCK' THEN m.quantity
                WHEN m.movement_type = 'SALE' THEN -m.quantity
                WHEN m.movement_type = 'ADJUSTMENT' THEN m.quantity
                ELSE 0
            END
        ),
        0
    ) AS current_stock
FROM dim_products p
LEFT JOIN fact_inventory_movements m
    ON p.product_id = m.product_id
GROUP BY
    p.product_id,
    p.product_name,
    p.category,
    p.reorder_level,
    p.target_stock;


CREATE OR REPLACE VIEW vw_stockout_risk AS
SELECT
    cs.product_id,
    cs.product_name,
    cs.category,
    cs.current_stock,
    cs.reorder_level,
    cs.target_stock,
    GREATEST(cs.target_stock - cs.current_stock, 0) AS suggested_reorder_quantity,
    CASE
        WHEN cs.current_stock <= 0 THEN 'CRITICAL_STOCKOUT'
        WHEN cs.current_stock <= cs.reorder_level THEN 'REORDER_REQUIRED'
        WHEN cs.current_stock <= cs.reorder_level * 1.2 THEN 'WATCHLIST'
        ELSE 'OK'
    END AS risk_status
FROM vw_current_stock cs
WHERE cs.current_stock <= cs.reorder_level;


CREATE OR REPLACE VIEW vw_supplier_performance AS
SELECT
    s.supplier_id,
    s.supplier_name,
    s.country,
    s.avg_delivery_days,
    s.reliability_score,
    COUNT(DISTINCT p.product_id) AS number_of_products,
    COALESCE(SUM(sp.total_units_sold), 0) AS total_units_sold,
    COALESCE(ROUND(SUM(sp.net_revenue), 2), 0) AS total_revenue
FROM dim_suppliers s
LEFT JOIN dim_products p
    ON s.supplier_id = p.supplier_id
LEFT JOIN vw_sales_by_product sp
    ON p.product_id = sp.product_id
GROUP BY
    s.supplier_id,
    s.supplier_name,
    s.country,
    s.avg_delivery_days,
    s.reliability_score;


CREATE OR REPLACE VIEW vw_monthly_sales AS
SELECT
    DATE_TRUNC('month', o.order_date)::DATE AS month_start,
    COUNT(DISTINCT o.order_id) AS number_of_orders,
    SUM(oi.quantity) AS total_units_sold,
    ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount_pct / 100)), 2) AS net_revenue
FROM fact_orders o
JOIN fact_order_items oi
    ON o.order_id = oi.order_id
WHERE o.order_status IN ('completed', 'shipped')
GROUP BY
    DATE_TRUNC('month', o.order_date)::DATE
ORDER BY
    month_start;