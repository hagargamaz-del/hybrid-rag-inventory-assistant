from pathlib import Path
import csv
import random
from datetime import date, timedelta

random.seed(42)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)


def write_csv(filename, fieldnames, rows):
    file_path = RAW_DIR / filename

    with open(file_path, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[CREATED] {file_path} ({len(rows)} rows)")


def create_suppliers():
    countries = ["Egypt", "Turkey", "China", "Germany", "USA", "India"]

    suppliers = []
    for supplier_id in range(1, 9):
        suppliers.append({
            "supplier_id": supplier_id,
            "supplier_name": f"Supplier {supplier_id}",
            "country": random.choice(countries),
            "avg_delivery_days": random.randint(3, 18),
            "reliability_score": round(random.uniform(0.70, 0.98), 2)
        })

    return suppliers


def create_products(suppliers):
    product_templates = [
        ("Wireless Mouse", "Electronics"),
        ("Mechanical Keyboard", "Electronics"),
        ("USB-C Cable", "Electronics"),
        ("Laptop Stand", "Accessories"),
        ("HDMI Adapter", "Electronics"),
        ("Office Chair", "Furniture"),
        ("Standing Desk", "Furniture"),
        ("Notebook Pack", "Stationery"),
        ("Ballpoint Pens", "Stationery"),
        ("Printer Paper", "Stationery"),
        ("Desk Lamp", "Furniture"),
        ("External SSD", "Electronics"),
        ("Webcam", "Electronics"),
        ("Headset", "Electronics"),
        ("Monitor 24 inch", "Electronics"),
        ("Monitor 27 inch", "Electronics"),
        ("Router", "Networking"),
        ("Ethernet Cable", "Networking"),
        ("Switch 8-Port", "Networking"),
        ("WiFi Extender", "Networking"),
        ("Whiteboard", "Office Supplies"),
        ("Marker Set", "Office Supplies"),
        ("Storage Box", "Office Supplies"),
        ("Desk Organizer", "Accessories"),
        ("Power Bank", "Electronics"),
        ("Tablet Cover", "Accessories"),
        ("Phone Charger", "Electronics"),
        ("Bluetooth Speaker", "Electronics"),
        ("Barcode Scanner", "Warehouse"),
        ("Label Printer", "Warehouse"),
    ]

    products = []

    for product_id, (product_name, category) in enumerate(product_templates, start=1):
        unit_cost = round(random.uniform(5, 250), 2)
        margin = random.uniform(1.25, 1.90)
        unit_price = round(unit_cost * margin, 2)

        products.append({
            "product_id": product_id,
            "product_name": product_name,
            "category": category,
            "supplier_id": random.choice(suppliers)["supplier_id"],
            "unit_cost": unit_cost,
            "unit_price": unit_price,
            "reorder_level": random.randint(20, 70),
            "target_stock": random.randint(100, 250)
        })

    return products


def create_customers():
    cities = ["Cairo", "Giza", "Alexandria", "Mansoura", "Tanta", "Zagazig", "Assiut"]
    segments = ["Retail", "Corporate", "Small Business"]

    customers = []

    for customer_id in range(1, 81):
        customers.append({
            "customer_id": customer_id,
            "customer_name": f"Customer {customer_id}",
            "city": random.choice(cities),
            "segment": random.choice(segments)
        })

    return customers


def create_orders_and_items(customers, products):
    end_date = date.today()
    start_date = end_date - timedelta(days=180)

    orders = []
    order_items = []

    order_item_id = 1

    for order_id in range(1, 451):
        order_date = start_date + timedelta(days=random.randint(0, 180))
        customer = random.choice(customers)

        order_status = random.choices(
            population=["completed", "shipped", "cancelled"],
            weights=[0.70, 0.22, 0.08],
            k=1
        )[0]

        orders.append({
            "order_id": order_id,
            "order_date": order_date.isoformat(),
            "customer_id": customer["customer_id"],
            "order_status": order_status
        })

        number_of_items = random.randint(1, 4)
        selected_products = random.sample(products, number_of_items)

        for product in selected_products:
            quantity = random.randint(1, 10)
            discount_pct = random.choice([0, 0, 0, 5, 10])

            order_items.append({
                "order_item_id": order_item_id,
                "order_id": order_id,
                "product_id": product["product_id"],
                "quantity": quantity,
                "unit_price": product["unit_price"],
                "discount_pct": discount_pct
            })

            order_item_id += 1

    orders.sort(key=lambda row: row["order_date"])

    return orders, order_items


def create_inventory_movements(products, orders, order_items):
    movements = []
    movement_id = 1

    order_lookup = {order["order_id"]: order for order in orders}
    end_date = date.today()
    start_date = end_date - timedelta(days=180)

    # Initial stock
    for product in products:
        movements.append({
            "movement_id": movement_id,
            "movement_date": (start_date - timedelta(days=10)).isoformat(),
            "product_id": product["product_id"],
            "movement_type": "RESTOCK",
            "quantity": random.randint(80, 220),
            "reference_id": "INITIAL_STOCK",
            "notes": "Initial inventory load"
        })
        movement_id += 1

    # Periodic restocks
    for day_offset in range(15, 181, 25):
        movement_date = start_date + timedelta(days=day_offset)

        for product in products:
            should_restock = random.random() < 0.35

            if should_restock:
                movements.append({
                    "movement_id": movement_id,
                    "movement_date": movement_date.isoformat(),
                    "product_id": product["product_id"],
                    "movement_type": "RESTOCK",
                    "quantity": random.randint(30, 120),
                    "reference_id": f"RESTOCK_{movement_date.isoformat()}",
                    "notes": "Scheduled supplier restock"
                })
                movement_id += 1

    # Sales movements from completed or shipped orders
    for item in order_items:
        order = order_lookup[item["order_id"]]

        if order["order_status"] in ["completed", "shipped"]:
            movements.append({
                "movement_id": movement_id,
                "movement_date": order["order_date"],
                "product_id": item["product_id"],
                "movement_type": "SALE",
                "quantity": item["quantity"],
                "reference_id": item["order_id"],
                "notes": "Inventory reduction due to customer order"
            })
            movement_id += 1

    # Random stock adjustments
    for _ in range(25):
        product = random.choice(products)
        adjustment_date = start_date + timedelta(days=random.randint(0, 180))
        adjustment_quantity = random.choice([-10, -5, -3, 3, 5, 10])

        movements.append({
            "movement_id": movement_id,
            "movement_date": adjustment_date.isoformat(),
            "product_id": product["product_id"],
            "movement_type": "ADJUSTMENT",
            "quantity": adjustment_quantity,
            "reference_id": "MANUAL_ADJUSTMENT",
            "notes": "Manual stock correction after warehouse count"
        })
        movement_id += 1

    movements.sort(key=lambda row: row["movement_date"])

    return movements


def main():
    suppliers = create_suppliers()
    products = create_products(suppliers)
    customers = create_customers()
    orders, order_items = create_orders_and_items(customers, products)
    inventory_movements = create_inventory_movements(products, orders, order_items)

    write_csv(
        "suppliers.csv",
        ["supplier_id", "supplier_name", "country", "avg_delivery_days", "reliability_score"],
        suppliers
    )

    write_csv(
        "products.csv",
        ["product_id", "product_name", "category", "supplier_id", "unit_cost", "unit_price", "reorder_level", "target_stock"],
        products
    )

    write_csv(
        "customers.csv",
        ["customer_id", "customer_name", "city", "segment"],
        customers
    )

    write_csv(
        "orders.csv",
        ["order_id", "order_date", "customer_id", "order_status"],
        orders
    )

    write_csv(
        "order_items.csv",
        ["order_item_id", "order_id", "product_id", "quantity", "unit_price", "discount_pct"],
        order_items
    )

    write_csv(
        "inventory_movements.csv",
        ["movement_id", "movement_date", "product_id", "movement_type", "quantity", "reference_id", "notes"],
        inventory_movements
    )

    print("\nStructured sample dataset created successfully.")


if __name__ == "__main__":
    main()
    