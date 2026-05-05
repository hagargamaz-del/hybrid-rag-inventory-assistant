from src.retrieval.sql_retriever import SQLRetriever


def print_results(output):
    print("=" * 90)
    print(f"Question: {output['question']}")
    print(f"Query Type: {output['query_type']}")
    print(f"Description: {output['description']}")
    print(f"Rows Returned: {output['row_count']}")
    print("=" * 90)

    for index, row in enumerate(output["results"], start=1):
        print(f"[Row {index}]")
        for key, value in row.items():
            print(f"{key}: {value}")
        print()


def test_stockout_query(retriever):
    question = "Which products are close to stockout?"
    output = retriever.search(question, limit=5)

    print_results(output)

    if output["query_type"] != "stockout_risk":
        raise ValueError("Stockout query was routed incorrectly.")

    if output["row_count"] == 0:
        raise ValueError("Stockout query returned no rows.")

    required_fields = {
        "product_name",
        "current_stock",
        "reorder_level",
        "suggested_reorder_quantity",
        "risk_status",
    }

    first_row_fields = set(output["results"][0].keys())

    if not required_fields.issubset(first_row_fields):
        raise ValueError("Stockout query is missing required fields.")

    print("[OK] Stockout-risk SQL query works correctly\n")


def test_top_selling_query(retriever):
    question = "What are the top 5 selling products?"
    output = retriever.search(question, limit=5)

    print_results(output)

    if output["query_type"] != "top_selling_products":
        raise ValueError("Top-selling query was routed incorrectly.")

    if output["row_count"] == 0:
        raise ValueError("Top-selling query returned no rows.")

    first_units_sold = output["results"][0]["total_units_sold"]

    if first_units_sold <= 0:
        raise ValueError("Top-selling product has invalid total_units_sold.")

    print("[OK] Top-selling-products SQL query works correctly\n")


def test_supplier_query(retriever):
    question = "Which suppliers have long delivery times?"
    output = retriever.search(question, limit=5)

    print_results(output)

    if output["query_type"] != "supplier_performance":
        raise ValueError("Supplier query was routed incorrectly.")

    if output["row_count"] == 0:
        raise ValueError("Supplier query returned no rows.")

    required_fields = {
        "supplier_name",
        "avg_delivery_days",
        "reliability_score",
        "number_of_products",
        "total_revenue",
    }

    first_row_fields = set(output["results"][0].keys())

    if not required_fields.issubset(first_row_fields):
        raise ValueError("Supplier query is missing required fields.")

    print("[OK] Supplier-performance SQL query works correctly\n")


def test_monthly_sales_query(retriever):
    question = "Show monthly revenue trend."
    output = retriever.search(question, limit=7)

    print_results(output)

    if output["query_type"] != "monthly_sales":
        raise ValueError("Monthly sales query was routed incorrectly.")

    if output["row_count"] == 0:
        raise ValueError("Monthly sales query returned no rows.")

    required_fields = {
        "month_start",
        "number_of_orders",
        "total_units_sold",
        "net_revenue",
    }

    first_row_fields = set(output["results"][0].keys())

    if not required_fields.issubset(first_row_fields):
        raise ValueError("Monthly sales query is missing required fields.")

    print("[OK] Monthly-sales SQL query works correctly\n")


def test_current_stock_query(retriever):
    question = "Show products with the lowest current stock."
    output = retriever.search(question, limit=5)

    print_results(output)

    if output["query_type"] != "current_stock":
        raise ValueError("Current-stock query was routed incorrectly.")

    if output["row_count"] == 0:
        raise ValueError("Current-stock query returned no rows.")

    required_fields = {
        "product_name",
        "category",
        "current_stock",
        "reorder_level",
        "target_stock",
    }

    first_row_fields = set(output["results"][0].keys())

    if not required_fields.issubset(first_row_fields):
        raise ValueError("Current-stock query is missing required fields.")

    print("[OK] Current-stock SQL query works correctly\n")


def test_business_overview_query(retriever):
    question = "Give me a business overview."
    output = retriever.search(question)

    print_results(output)

    if output["query_type"] != "business_overview":
        raise ValueError("Business overview query was routed incorrectly.")

    if output["row_count"] != 1:
        raise ValueError("Business overview should return exactly one row.")

    required_fields = {
        "number_of_products",
        "number_of_suppliers",
        "number_of_orders",
        "number_of_order_items",
        "stockout_risk_products",
        "total_revenue",
    }

    first_row_fields = set(output["results"][0].keys())

    if not required_fields.issubset(first_row_fields):
        raise ValueError("Business overview query is missing required fields.")

    print("[OK] Business-overview SQL query works correctly\n")


def main():
    print("Initializing SQLRetriever...")
    retriever = SQLRetriever()
    print("[OK] SQLRetriever initialized\n")

    test_stockout_query(retriever)
    test_top_selling_query(retriever)
    test_supplier_query(retriever)
    test_monthly_sales_query(retriever)
    test_current_stock_query(retriever)
    test_business_overview_query(retriever)

    print("SQL retriever test completed successfully.")


if __name__ == "__main__":
    main()