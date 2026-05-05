from pathlib import Path
import csv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"


REQUIRED_FILES = {
    "suppliers.csv": 8,
    "products.csv": 30,
    "customers.csv": 80,
    "orders.csv": 450,
    "order_items.csv": 500,
    "inventory_movements.csv": 500,
}


def read_csv(filename):
    file_path = RAW_DIR / filename

    if not file_path.exists():
        raise FileNotFoundError(f"Missing file: {file_path}")

    with open(file_path, mode="r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def check_file_exists_and_row_counts():
    print("Checking raw CSV files...\n")

    loaded_data = {}

    for filename, minimum_rows in REQUIRED_FILES.items():
        rows = read_csv(filename)
        loaded_data[filename] = rows

        if len(rows) < minimum_rows:
            raise ValueError(
                f"{filename} has only {len(rows)} rows. Expected at least {minimum_rows}."
            )

        print(f"[OK] {filename}: {len(rows)} rows")

    return loaded_data


def check_foreign_keys(data):
    print("\nChecking relationships between files...\n")

    suppliers = data["suppliers.csv"]
    products = data["products.csv"]
    customers = data["customers.csv"]
    orders = data["orders.csv"]
    order_items = data["order_items.csv"]
    movements = data["inventory_movements.csv"]

    supplier_ids = {row["supplier_id"] for row in suppliers}
    product_ids = {row["product_id"] for row in products}
    customer_ids = {row["customer_id"] for row in customers}
    order_ids = {row["order_id"] for row in orders}

    invalid_product_suppliers = [
        row for row in products if row["supplier_id"] not in supplier_ids
    ]

    invalid_order_customers = [
        row for row in orders if row["customer_id"] not in customer_ids
    ]

    invalid_order_items_orders = [
        row for row in order_items if row["order_id"] not in order_ids
    ]

    invalid_order_items_products = [
        row for row in order_items if row["product_id"] not in product_ids
    ]

    invalid_movement_products = [
        row for row in movements if row["product_id"] not in product_ids
    ]

    if invalid_product_suppliers:
        raise ValueError("Some products reference invalid supplier_id values.")

    if invalid_order_customers:
        raise ValueError("Some orders reference invalid customer_id values.")

    if invalid_order_items_orders:
        raise ValueError("Some order_items reference invalid order_id values.")

    if invalid_order_items_products:
        raise ValueError("Some order_items reference invalid product_id values.")

    if invalid_movement_products:
        raise ValueError("Some inventory movements reference invalid product_id values.")

    print("[OK] products.supplier_id references suppliers.supplier_id")
    print("[OK] orders.customer_id references customers.customer_id")
    print("[OK] order_items.order_id references orders.order_id")
    print("[OK] order_items.product_id references products.product_id")
    print("[OK] inventory_movements.product_id references products.product_id")


def calculate_basic_metrics(data):
    print("\nCalculating basic business metrics...\n")

    products = data["products.csv"]
    orders = data["orders.csv"]
    order_items = data["order_items.csv"]
    movements = data["inventory_movements.csv"]

    order_status_lookup = {
        row["order_id"]: row["order_status"]
        for row in orders
    }

    product_lookup = {
        row["product_id"]: row
        for row in products
    }

    total_revenue = 0.0

    for item in order_items:
        order_status = order_status_lookup[item["order_id"]]

        if order_status in ["completed", "shipped"]:
            quantity = int(item["quantity"])
            unit_price = float(item["unit_price"])
            discount_pct = float(item["discount_pct"])

            total_revenue += quantity * unit_price * (1 - discount_pct / 100)

    stock_by_product = {product["product_id"]: 0 for product in products}

    for movement in movements:
        product_id = movement["product_id"]
        movement_type = movement["movement_type"]
        quantity = int(movement["quantity"])

        if movement_type == "RESTOCK":
            stock_by_product[product_id] += quantity
        elif movement_type == "SALE":
            stock_by_product[product_id] -= quantity
        elif movement_type == "ADJUSTMENT":
            stock_by_product[product_id] += quantity

    low_stock_products = []

    for product_id, current_stock in stock_by_product.items():
        product = product_lookup[product_id]
        reorder_level = int(product["reorder_level"])

        if current_stock <= reorder_level:
            low_stock_products.append({
                "product_id": product_id,
                "product_name": product["product_name"],
                "current_stock": current_stock,
                "reorder_level": reorder_level
            })

    low_stock_products.sort(key=lambda row: row["current_stock"])

    print(f"Total completed/shipped revenue: ${total_revenue:,.2f}")
    print(f"Number of low-stock products: {len(low_stock_products)}")

    print("\nLowest-stock products:")
    for row in low_stock_products[:5]:
        print(
            f"- {row['product_name']} | "
            f"Current stock: {row['current_stock']} | "
            f"Reorder level: {row['reorder_level']}"
        )


def main():
    data = check_file_exists_and_row_counts()
    check_foreign_keys(data)
    calculate_basic_metrics(data)

    print("\nRaw structured data test completed successfully.")


if __name__ == "__main__":
    main()