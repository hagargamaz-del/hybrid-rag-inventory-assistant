from pathlib import Path
import os
import psycopg2
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5433"),
        dbname=os.getenv("DB_NAME", "inventory_rag"),
        user=os.getenv("DB_USER", "inventory_user"),
        password=os.getenv("DB_PASSWORD", "inventory_password"),
    )


def fetch_one(cursor, query):
    cursor.execute(query)
    return cursor.fetchone()[0]


def print_table_counts(cursor):
    print("Checking table row counts...\n")

    tables = [
        "dim_suppliers",
        "dim_products",
        "dim_customers",
        "fact_orders",
        "fact_order_items",
        "fact_inventory_movements",
    ]

    for table in tables:
        count = fetch_one(cursor, f"SELECT COUNT(*) FROM {table};")
        print(f"[OK] {table}: {count} rows")


def print_business_metrics(cursor):
    print("\nChecking SQL analytics views...\n")

    total_revenue = fetch_one(
        cursor,
        """
        SELECT COALESCE(ROUND(SUM(net_revenue), 2), 0)
        FROM vw_sales_by_product;
        """
    )

    stockout_count = fetch_one(
        cursor,
        """
        SELECT COUNT(*)
        FROM vw_stockout_risk;
        """
    )

    monthly_sales_count = fetch_one(
        cursor,
        """
        SELECT COUNT(*)
        FROM vw_monthly_sales;
        """
    )

    print(f"Total revenue from SQL view: ${total_revenue:,.2f}")
    print(f"Stockout-risk products: {stockout_count}")
    print(f"Monthly sales periods: {monthly_sales_count}")


def print_top_selling_products(cursor):
    print("\nTop 5 selling products:\n")

    cursor.execute(
        """
        SELECT
            product_name,
            category,
            total_units_sold,
            net_revenue
        FROM vw_sales_by_product
        ORDER BY total_units_sold DESC
        LIMIT 5;
        """
    )

    rows = cursor.fetchall()

    for row in rows:
        product_name, category, units_sold, net_revenue = row
        print(
            f"- {product_name} | {category} | "
            f"Units sold: {units_sold} | Revenue: ${net_revenue:,.2f}"
        )


def print_stockout_risk_products(cursor):
    print("\nStockout-risk products:\n")

    cursor.execute(
        """
        SELECT
            product_name,
            current_stock,
            reorder_level,
            suggested_reorder_quantity,
            risk_status
        FROM vw_stockout_risk
        ORDER BY current_stock ASC
        LIMIT 10;
        """
    )

    rows = cursor.fetchall()

    for row in rows:
        product_name, current_stock, reorder_level, reorder_qty, risk_status = row
        print(
            f"- {product_name} | "
            f"Current stock: {current_stock} | "
            f"Reorder level: {reorder_level} | "
            f"Suggested reorder: {reorder_qty} | "
            f"Status: {risk_status}"
        )


def main():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            print_table_counts(cursor)
            print_business_metrics(cursor)
            print_top_selling_products(cursor)
            print_stockout_risk_products(cursor)

    print("\nPostgreSQL data test completed successfully.")


if __name__ == "__main__":
    main()