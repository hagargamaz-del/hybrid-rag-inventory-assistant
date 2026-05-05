from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOCUMENTS_DIR = PROJECT_ROOT / "data" / "documents"
DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)


DOCUMENTS = {
    "inventory_policy.txt": """
Inventory Replenishment and Stockout Policy

Document Type: Inventory Policy
Department: Supply Chain and Warehouse Operations
Version: 1.0

1. Purpose
This policy defines how inventory levels should be monitored, when products should be reordered, and how stockout risks should be handled.

2. Reorder Rules
A product must be flagged for reorder when its current stock is less than or equal to its reorder level.
The reorder quantity should normally be calculated as the difference between the target stock and the current stock.
If the current stock is negative, the product must be treated as a critical stockout.

3. Stockout Risk Classification
Products are classified as CRITICAL_STOCKOUT when the current stock is zero or below.
Products are classified as REORDER_REQUIRED when the current stock is above zero but less than or equal to the reorder level.
Products are classified as WATCHLIST when the current stock is slightly above the reorder level but demand is increasing.

4. Recommended Action
For CRITICAL_STOCKOUT products, the purchasing team must create an urgent replenishment request within the same business day.
For REORDER_REQUIRED products, the purchasing team should create a standard replenishment order within two business days.
For WATCHLIST products, the inventory team should monitor sales velocity before placing a new order.

5. Business Rule
The recommended reorder quantity should not be lower than the target stock minus the current stock.
If supplier lead time is greater than 10 days, the reorder request should be prioritized.
""",

    "supplier_policy.txt": """
Supplier Performance and Procurement Policy

Document Type: Supplier Policy
Department: Procurement
Version: 1.0

1. Purpose
This document defines how suppliers should be evaluated and how procurement decisions should be made.

2. Supplier Reliability
Suppliers with a reliability score below 0.80 should be reviewed by the procurement team.
Suppliers with an average delivery time greater than 10 days should be considered high lead-time suppliers.
For high lead-time suppliers, reorder requests should be submitted earlier to reduce stockout risk.

3. Procurement Priority
Products with CRITICAL_STOCKOUT status must be prioritized regardless of supplier category.
If a product is supplied by a high lead-time supplier, the purchasing team should increase the urgency of the replenishment request.
If a supplier has both low reliability and long delivery time, the operations team should consider alternative suppliers.

4. Supplier Review
Supplier performance should be reviewed monthly using total units sold, number of supplied products, delivery time, and reliability score.
""",

    "returns_policy.txt": """
Customer Returns and Damaged Goods Policy

Document Type: Returns Policy
Department: Customer Service and Warehouse Operations
Version: 1.0

1. Purpose
This policy defines how returned, damaged, and defective products should be handled.

2. Return Conditions
Customers may return damaged products within 14 days of delivery.
Returned products must be inspected by the warehouse team before they are added back to available inventory.
Defective products should not be returned to sellable stock.

3. Inventory Adjustment
If a returned item is sellable, the warehouse team may create a positive inventory adjustment.
If a returned item is damaged or defective, the warehouse team must create a negative adjustment or mark the item as unsellable.
Manual stock corrections must include a clear note explaining the reason for the adjustment.

4. Reporting
High return rates should be reviewed monthly by product, supplier, and customer segment.
""",

    "warehouse_sop.txt": """
Warehouse Inventory Movement Standard Operating Procedure

Document Type: Warehouse SOP
Department: Warehouse Operations
Version: 1.0

1. Purpose
This SOP explains how warehouse staff should record inventory movements.

2. Movement Types
RESTOCK movements increase available inventory.
SALE movements decrease available inventory after customer orders are completed or shipped.
ADJUSTMENT movements are used for manual corrections after warehouse counts, damaged goods, returns, or reconciliation issues.

3. Data Entry Rules
Every inventory movement must include a movement date, product identifier, movement type, quantity, reference identifier, and notes.
Warehouse staff must not create inventory movements without a valid product identifier.
Negative inventory should be investigated because it may indicate delayed restocking, incorrect sales recording, or missing warehouse adjustments.

4. Audit Requirements
Inventory movement records should be reviewed weekly.
Products with repeated negative adjustments should be investigated by the warehouse manager.
""",

    "product_handling_notes.txt": """
Product Handling and Category Notes

Document Type: Product Handling Notes
Department: Warehouse Operations
Version: 1.0

1. Electronics
Electronics products such as monitors, external SSDs, routers, webcams, and headsets should be stored in dry areas away from moisture.
High-value electronics should be checked during receiving and before shipment.

2. Furniture
Furniture products such as office chairs, standing desks, and lamps should be inspected for physical damage before storage.
Large furniture items may require additional handling time.

3. Stationery and Office Supplies
Stationery items should be counted in batches during warehouse audits.
Office supplies with low unit cost may still require reorder monitoring if demand volume is high.

4. Networking Products
Networking products such as switches, routers, Ethernet cables, and WiFi extenders should be tracked carefully because demand may increase suddenly during office setup projects.

5. Warehouse Equipment
Barcode scanners and label printers are operationally important products.
If warehouse equipment reaches reorder level, the issue should be escalated because it may affect warehouse processing efficiency.
"""
}


def main():
    print("Creating unstructured business documents...\n")

    for filename, content in DOCUMENTS.items():
        file_path = DOCUMENTS_DIR / filename

        clean_content = content.strip()

        with open(file_path, mode="w", encoding="utf-8") as file:
            file.write(clean_content)

        print(f"[CREATED] {file_path}")

    print("\nBusiness documents created successfully.")


if __name__ == "__main__":
    main()