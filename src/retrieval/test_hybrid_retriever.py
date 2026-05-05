from src.retrieval.hybrid_retriever import HybridRetriever


def print_retrieval_summary(output):
    print("=" * 90)
    print(f"Question: {output['question']}")
    print(f"Retrieval Mode: {output['retrieval_mode']}")
    print("=" * 90)

    if output["sql_output"]:
        print("\nSQL Output:")
        print(f"- Query Type: {output['sql_output']['query_type']}")
        print(f"- Rows Returned: {output['sql_output']['row_count']}")

        for index, row in enumerate(output["sql_output"]["results"][:3], start=1):
            print(f"  Row {index}: {row}")

    if output["vector_output"]:
        print("\nVector Output:")
        print(f"- Chunks Returned: {len(output['vector_output'])}")

        for index, chunk in enumerate(output["vector_output"][:3], start=1):
            print(
                f"  Chunk {index}: "
                f"{chunk['source_file']} | "
                f"{chunk['section_title']} | "
                f"Similarity: {chunk['similarity']:.4f}"
            )

    print()


def test_sql_only_question(retriever):
    question = "What are the top 5 selling products?"
    output = retriever.retrieve(question)

    print_retrieval_summary(output)

    if output["retrieval_mode"] != "sql":
        raise ValueError("SQL-only question was not classified as sql.")

    if output["sql_output"] is None:
        raise ValueError("SQL-only question did not return SQL output.")

    if output["vector_output"] is not None:
        raise ValueError("SQL-only question should not return vector output.")

    if output["sql_output"]["query_type"] != "top_selling_products":
        raise ValueError("SQL-only question returned wrong SQL query type.")

    print("[OK] SQL-only retrieval works correctly\n")


def test_vector_only_question(retriever):
    question = "What is the inventory policy for reorder actions?"
    output = retriever.retrieve(question)

    print_retrieval_summary(output)

    if output["retrieval_mode"] != "hybrid":
        raise ValueError(
            "This question should be hybrid because it contains both inventory/reorder and policy intent."
        )

    if output["sql_output"] is None:
        raise ValueError("Hybrid policy question did not return SQL output.")

    if output["vector_output"] is None:
        raise ValueError("Hybrid policy question did not return vector output.")

    sources = {chunk["source_file"] for chunk in output["vector_output"]}

    if "inventory_policy.txt" not in sources:
        raise ValueError("Inventory policy source was not retrieved.")

    print("[OK] Inventory policy hybrid retrieval works correctly\n")


def test_true_vector_only_question(retriever):
    question = "Explain the warehouse movement procedure."
    output = retriever.retrieve(question)

    print_retrieval_summary(output)

    if output["retrieval_mode"] != "vector":
        raise ValueError("Vector-only question was not classified as vector.")

    if output["sql_output"] is not None:
        raise ValueError("Vector-only question should not return SQL output.")

    if output["vector_output"] is None:
        raise ValueError("Vector-only question did not return vector output.")

    sources = {chunk["source_file"] for chunk in output["vector_output"]}

    if "warehouse_sop.txt" not in sources:
        raise ValueError("Warehouse SOP source was not retrieved.")

    print("[OK] Vector-only retrieval works correctly\n")


def test_hybrid_question(retriever):
    question = "Which products are at stockout risk and what policy explains the reorder action?"
    output = retriever.retrieve(question)

    print_retrieval_summary(output)

    if output["retrieval_mode"] != "hybrid":
        raise ValueError("Hybrid question was not classified as hybrid.")

    if output["sql_output"] is None:
        raise ValueError("Hybrid question did not return SQL output.")

    if output["vector_output"] is None:
        raise ValueError("Hybrid question did not return vector output.")

    if output["sql_output"]["query_type"] != "stockout_risk":
        raise ValueError("Hybrid question returned wrong SQL query type.")

    sources = {chunk["source_file"] for chunk in output["vector_output"]}

    if "inventory_policy.txt" not in sources:
        raise ValueError("Hybrid question did not retrieve inventory policy.")

    print("[OK] Hybrid SQL + vector retrieval works correctly\n")


def test_supplier_hybrid_question(retriever):
    question = "Which suppliers have long delivery times and what procurement policy should we follow?"
    output = retriever.retrieve(question)

    print_retrieval_summary(output)

    if output["retrieval_mode"] != "hybrid":
        raise ValueError("Supplier hybrid question was not classified as hybrid.")

    if output["sql_output"] is None:
        raise ValueError("Supplier hybrid question did not return SQL output.")

    if output["vector_output"] is None:
        raise ValueError("Supplier hybrid question did not return vector output.")

    if output["sql_output"]["query_type"] != "supplier_performance":
        raise ValueError("Supplier hybrid question returned wrong SQL query type.")

    sources = {chunk["source_file"] for chunk in output["vector_output"]}

    if "supplier_policy.txt" not in sources:
        raise ValueError("Supplier policy was not retrieved.")

    print("[OK] Supplier hybrid retrieval works correctly\n")


def main():
    print("Initializing HybridRetriever...")
    retriever = HybridRetriever()
    print("[OK] HybridRetriever initialized\n")

    test_sql_only_question(retriever)
    test_vector_only_question(retriever)
    test_true_vector_only_question(retriever)
    test_hybrid_question(retriever)
    test_supplier_hybrid_question(retriever)

    print("Hybrid retriever test completed successfully.")


if __name__ == "__main__":
    main()