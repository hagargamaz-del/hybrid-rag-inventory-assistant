CREATE EXTENSION IF NOT EXISTS vector;

DROP VIEW IF EXISTS vw_monthly_sales CASCADE;
DROP VIEW IF EXISTS vw_supplier_performance CASCADE;
DROP VIEW IF EXISTS vw_stockout_risk CASCADE;
DROP VIEW IF EXISTS vw_current_stock CASCADE;
DROP VIEW IF EXISTS vw_sales_by_product CASCADE;

DROP TABLE IF EXISTS fact_inventory_movements CASCADE;
DROP TABLE IF EXISTS fact_order_items CASCADE;
DROP TABLE IF EXISTS fact_orders CASCADE;
DROP TABLE IF EXISTS dim_products CASCADE;
DROP TABLE IF EXISTS dim_customers CASCADE;
DROP TABLE IF EXISTS dim_suppliers CASCADE;

CREATE TABLE dim_suppliers (
    supplier_id INT PRIMARY KEY,
    supplier_name VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL,
    avg_delivery_days INT NOT NULL CHECK (avg_delivery_days > 0),
    reliability_score NUMERIC(4,2) NOT NULL CHECK (reliability_score BETWEEN 0 AND 1)
);

CREATE TABLE dim_customers (
    customer_id INT PRIMARY KEY,
    customer_name VARCHAR(100) NOT NULL,
    city VARCHAR(100) NOT NULL,
    segment VARCHAR(50) NOT NULL
);

CREATE TABLE dim_products (
    product_id INT PRIMARY KEY,
    product_name VARCHAR(150) NOT NULL,
    category VARCHAR(100) NOT NULL,
    supplier_id INT NOT NULL,
    unit_cost NUMERIC(10,2) NOT NULL CHECK (unit_cost >= 0),
    unit_price NUMERIC(10,2) NOT NULL CHECK (unit_price >= 0),
    reorder_level INT NOT NULL CHECK (reorder_level >= 0),
    target_stock INT NOT NULL CHECK (target_stock >= 0),

    CONSTRAINT fk_products_supplier
        FOREIGN KEY (supplier_id)
        REFERENCES dim_suppliers(supplier_id)
);

CREATE TABLE fact_orders (
    order_id INT PRIMARY KEY,
    order_date DATE NOT NULL,
    customer_id INT NOT NULL,
    order_status VARCHAR(30) NOT NULL CHECK (order_status IN ('completed', 'shipped', 'cancelled')),

    CONSTRAINT fk_orders_customer
        FOREIGN KEY (customer_id)
        REFERENCES dim_customers(customer_id)
);

CREATE TABLE fact_order_items (
    order_item_id INT PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(10,2) NOT NULL CHECK (unit_price >= 0),
    discount_pct NUMERIC(5,2) NOT NULL CHECK (discount_pct >= 0),

    CONSTRAINT fk_order_items_order
        FOREIGN KEY (order_id)
        REFERENCES fact_orders(order_id),

    CONSTRAINT fk_order_items_product
        FOREIGN KEY (product_id)
        REFERENCES dim_products(product_id)
);

CREATE TABLE fact_inventory_movements (
    movement_id INT PRIMARY KEY,
    movement_date DATE NOT NULL,
    product_id INT NOT NULL,
    movement_type VARCHAR(30) NOT NULL CHECK (movement_type IN ('RESTOCK', 'SALE', 'ADJUSTMENT')),
    quantity INT NOT NULL,
    reference_id VARCHAR(100),
    notes TEXT,

    CONSTRAINT fk_inventory_product
        FOREIGN KEY (product_id)
        REFERENCES dim_products(product_id)
);

CREATE INDEX idx_orders_order_date
ON fact_orders(order_date);

CREATE INDEX idx_order_items_product_id
ON fact_order_items(product_id);

CREATE INDEX idx_inventory_product_date
ON fact_inventory_movements(product_id, movement_date);

CREATE INDEX idx_inventory_movement_type
ON fact_inventory_movements(movement_type);