from src.retrieval.vector_retriever import VectorRetriever


def print_results(query, results):
    print("=" * 90)
    print(f"Query: {query}")
    print("=" * 90)

    for index, result in enumerate(results, start=1):
        print(
            f"{index}. Similarity: {result['similarity']:.4f} | "
            f"Source: {result['source_file']} | "
            f"Section: {result['section_title']}"
        )
        print(f"   Chunk ID: {result['chunk_id']}")
        print(f"   Preview: {result['text'][:220]}...\n")


def assert_source_in_results(results, expected_source, test_name):
    sources = {result["source_file"] for result in results}

    if expected_source not in sources:
        raise ValueError(
            f"{test_name} failed. Expected source '{expected_source}' was not retrieved. "
            f"Retrieved sources: {sources}"
        )


def test_inventory_policy_query(retriever):
    query = "When should a product be reordered?"
    results = retriever.search(query=query, top_k=5)

    print_results(query, results)

    assert len(results) > 0
    assert_source_in_results(
        results=results,
        expected_source="inventory_policy.txt",
        test_name="Inventory policy query",
    )

    print("[OK] Inventory policy query retrieved relevant chunks\n")


def test_supplier_policy_query(retriever):
    query = "What should we do if a supplier has long delivery time?"
    results = retriever.search(query=query, top_k=5)

    print_results(query, results)

    assert len(results) > 0
    assert_source_in_results(
        results=results,
        expected_source="supplier_policy.txt",
        test_name="Supplier policy query",
    )

    print("[OK] Supplier policy query retrieved relevant chunks\n")


def test_document_type_filter(retriever):
    query = "How should negative inventory be investigated?"
    results = retriever.search(
        query=query,
        top_k=5,
        document_type="Warehouse SOP",
    )

    print_results(query, results)

    assert len(results) > 0

    for result in results:
        if result["document_type"] != "Warehouse SOP":
            raise ValueError(
                f"Document type filter failed. Found: {result['document_type']}"
            )

    print("[OK] Document type filter works correctly\n")


def test_minimum_similarity_filter(retriever):
    query = "When should a product be reordered?"

    unfiltered_results = retriever.search(query=query, top_k=5)
    filtered_results = retriever.search(
        query=query,
        top_k=5,
        minimum_similarity=0.50,
    )

    print("=" * 90)
    print("Testing minimum similarity filter")
    print("=" * 90)
    print(f"Unfiltered result count: {len(unfiltered_results)}")
    print(f"Filtered result count: {len(filtered_results)}")

    for result in filtered_results:
        if result["similarity"] < 0.50:
            raise ValueError("Similarity filter failed.")

    print("[OK] Minimum similarity filter works correctly\n")


def main():
    print("Initializing VectorRetriever...")
    retriever = VectorRetriever()
    print("[OK] VectorRetriever initialized\n")

    chunk_count = retriever.count_chunks()
    print(f"[OK] rag_document_chunks contains {chunk_count} chunks\n")

    if chunk_count != 22:
        raise ValueError(f"Expected 22 chunks, found {chunk_count}")

    test_inventory_policy_query(retriever)
    test_supplier_policy_query(retriever)
    test_document_type_filter(retriever)
    test_minimum_similarity_filter(retriever)

    print("Vector retriever test completed successfully.")


if __name__ == "__main__":
    main()