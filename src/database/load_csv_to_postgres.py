from pathlib import Path
import os
import psycopg2
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"

load_dotenv(PROJECT_ROOT / ".env")


def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5433"),
        dbname=os.getenv("DB_NAME", "inventory_rag"),
        user=os.getenv("DB_USER", "inventory_user"),
        password=os.getenv("DB_PASSWORD", "inventory_password"),
    )


def run_sql_file(connection, sql_file_path):
    print(f"[RUNNING SQL] {sql_file_path}")

    with open(sql_file_path, mode="r", encoding="utf-8") as file:
        sql = file.read()

    with connection.cursor() as cursor:
        cursor.execute(sql)

    connection.commit()
    print(f"[OK] Executed {sql_file_path.name}")


def copy_csv_to_table(connection, csv_filename, table_name, columns):
    csv_path = RAW_DIR / csv_filename

    if not csv_path.exists():
        raise FileNotFoundError(f"Missing CSV file: {csv_path}")

    columns_sql = ", ".join(columns)

    copy_sql = f"""
        COPY {table_name} ({columns_sql})
        FROM STDIN
        WITH CSV HEADER
    """

    print(f"[LOADING] {csv_filename} -> {table_name}")

    with open(csv_path, mode="r", encoding="utf-8") as file:
        with connection.cursor() as cursor:
            cursor.copy_expert(copy_sql, file)

    connection.commit()
    print(f"[OK] Loaded {csv_filename}")


def main():
    table_load_order = [
        {
            "csv_filename": "suppliers.csv",
            "table_name": "dim_suppliers",
            "columns": [
                "supplier_id",
                "supplier_name",
                "country",
                "avg_delivery_days",
                "reliability_score",
            ],
        },
        {
            "csv_filename": "customers.csv",
            "table_name": "dim_customers",
            "columns": [
                "customer_id",
                "customer_name",
                "city",
                "segment",
            ],
        },
        {
            "csv_filename": "products.csv",
            "table_name": "dim_products",
            "columns": [
                "product_id",
                "product_name",
                "category",
                "supplier_id",
                "unit_cost",
                "unit_price",
                "reorder_level",
                "target_stock",
            ],
        },
        {
            "csv_filename": "orders.csv",
            "table_name": "fact_orders",
            "columns": [
                "order_id",
                "order_date",
                "customer_id",
                "order_status",
            ],
        },
        {
            "csv_filename": "order_items.csv",
            "table_name": "fact_order_items",
            "columns": [
                "order_item_id",
                "order_id",
                "product_id",
                "quantity",
                "unit_price",
                "discount_pct",
            ],
        },
        {
            "csv_filename": "inventory_movements.csv",
            "table_name": "fact_inventory_movements",
            "columns": [
                "movement_id",
                "movement_date",
                "product_id",
                "movement_type",
                "quantity",
                "reference_id",
                "notes",
            ],
        },
    ]

    with get_connection() as connection:
        run_sql_file(connection, PROJECT_ROOT / "sql" / "create_tables.sql")

        for table_info in table_load_order:
            copy_csv_to_table(
                connection=connection,
                csv_filename=table_info["csv_filename"],
                table_name=table_info["table_name"],
                columns=table_info["columns"],
            )

        run_sql_file(connection, PROJECT_ROOT / "sql" / "create_views.sql")

    print("\nPostgreSQL database loaded successfully.")


if __name__ == "__main__":
    main()