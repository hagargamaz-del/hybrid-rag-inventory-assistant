from src.rag.answer_generator import RAGAnswerGenerator


def test_stockout_hybrid_answer(generator):
    question = "Which products are at stockout risk and what policy explains the reorder action?"
    response = generator.generate_answer(question)

    generator.print_response(response)

    answer = response["answer"]
    sources = response["sources"]

    if response["retrieval_mode"] != "hybrid":
        raise ValueError("Stockout question should use hybrid retrieval.")

    if "WiFi Extender" not in answer:
        raise ValueError("Stockout answer should mention WiFi Extender.")

    if "CRITICAL_STOCKOUT" not in answer:
        raise ValueError("Stockout answer should mention CRITICAL_STOCKOUT.")

    if "vw_stockout_risk" not in sources["sql_sources"]:
        raise ValueError("Stockout answer should cite vw_stockout_risk.")

    document_sources_text = " ".join(sources["document_sources"])

    if "inventory_policy.txt" not in document_sources_text:
        raise ValueError("Stockout answer should cite inventory_policy.txt.")

    print("[OK] Stockout hybrid answer works correctly\n")


def test_supplier_hybrid_answer(generator):
    question = "Which suppliers have long delivery times and what procurement policy should we follow?"
    response = generator.generate_answer(question)

    generator.print_response(response)

    answer = response["answer"]
    sources = response["sources"]

    if response["retrieval_mode"] != "hybrid":
        raise ValueError("Supplier question should use hybrid retrieval.")

    if "Supplier 7" not in answer:
        raise ValueError("Supplier answer should mention Supplier 7.")

    if "vw_supplier_performance" not in sources["sql_sources"]:
        raise ValueError("Supplier answer should cite vw_supplier_performance.")

    document_sources_text = " ".join(sources["document_sources"])

    if "supplier_policy.txt" not in document_sources_text:
        raise ValueError("Supplier answer should cite supplier_policy.txt.")

    print("[OK] Supplier hybrid answer works correctly\n")


def test_sql_only_answer(generator):
    question = "What are the top 5 selling products?"
    response = generator.generate_answer(question)

    generator.print_response(response)

    answer = response["answer"]
    sources = response["sources"]

    if response["retrieval_mode"] != "sql":
        raise ValueError("Top-selling question should use SQL retrieval.")

    if "External SSD" not in answer:
        raise ValueError("Top-selling answer should mention External SSD.")

    if "vw_sales_by_product" not in sources["sql_sources"]:
        raise ValueError("Top-selling answer should cite vw_sales_by_product.")

    print("[OK] SQL-only answer works correctly\n")


def test_vector_only_answer(generator):
    question = "Explain the warehouse movement procedure."
    response = generator.generate_answer(question)

    generator.print_response(response)

    answer = response["answer"]
    sources = response["sources"]

    if response["retrieval_mode"] != "vector":
        raise ValueError("Warehouse procedure question should use vector retrieval.")

    if "warehouse" not in answer.lower():
        raise ValueError("Vector-only answer should mention warehouse context.")

    document_sources_text = " ".join(sources["document_sources"])

    if "warehouse_sop.txt" not in document_sources_text:
        raise ValueError("Vector-only answer should cite warehouse_sop.txt.")

    print("[OK] Vector-only answer works correctly\n")


def main():
    print("Initializing RAGAnswerGenerator...")
    generator = RAGAnswerGenerator()
    print("[OK] RAGAnswerGenerator initialized\n")

    test_stockout_hybrid_answer(generator)
    test_supplier_hybrid_answer(generator)
    test_sql_only_answer(generator)
    test_vector_only_answer(generator)

    print("RAG answer generator test completed successfully.")


if __name__ == "__main__":
    main()