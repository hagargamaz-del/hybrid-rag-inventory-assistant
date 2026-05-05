from pathlib import Path
import json
import math
import numpy as np
from sentence_transformers import SentenceTransformer

PROJECT_ROOT = Path(__file__).resolve().parents[2]

CHUNKS_FILE = PROJECT_ROOT / "data" / "processed" / "document_chunks.jsonl"
EMBEDDINGS_FILE = PROJECT_ROOT / "data" / "processed" / "chunk_embeddings.jsonl"

EXPECTED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def load_jsonl(file_path):
    if not file_path.exists():
        raise FileNotFoundError(f"Missing file: {file_path}")

    records = []

    with open(file_path, mode="r", encoding="utf-8") as file:
        for line in file:
            records.append(json.loads(line))

    return records


def check_embedding_file(chunks, embedding_records):
    print("Checking embedding file structure...\n")

    if len(chunks) != len(embedding_records):
        raise ValueError(
            f"Chunk count and embedding count mismatch. "
            f"Chunks: {len(chunks)}, Embeddings: {len(embedding_records)}"
        )

    chunk_ids = {chunk["chunk_id"] for chunk in chunks}
    embedding_chunk_ids = {record["chunk_id"] for record in embedding_records}

    if chunk_ids != embedding_chunk_ids:
        raise ValueError("Chunk IDs do not match between chunks and embeddings.")

    dimensions = set()

    for record in embedding_records:
        required_fields = [
            "chunk_id",
            "text",
            "metadata",
            "embedding_model",
            "embedding_dimension",
            "embedding",
        ]

        for field in required_fields:
            if field not in record:
                raise ValueError(f"Record {record.get('chunk_id')} is missing field: {field}")

        embedding = record["embedding"]

        if not isinstance(embedding, list):
            raise ValueError(f"Embedding is not a list for chunk {record['chunk_id']}")

        if len(embedding) == 0:
            raise ValueError(f"Empty embedding for chunk {record['chunk_id']}")

        if len(embedding) != record["embedding_dimension"]:
            raise ValueError(f"Embedding dimension mismatch for chunk {record['chunk_id']}")

        if not all(isinstance(value, (int, float)) for value in embedding):
            raise ValueError(f"Embedding contains non-numeric values for chunk {record['chunk_id']}")

        if not all(math.isfinite(value) for value in embedding):
            raise ValueError(f"Embedding contains invalid numeric values for chunk {record['chunk_id']}")

        dimensions.add(len(embedding))

    if len(dimensions) != 1:
        raise ValueError(f"Embeddings have inconsistent dimensions: {dimensions}")

    embedding_dimension = list(dimensions)[0]

    print(f"[OK] Embedding records: {len(embedding_records)}")
    print(f"[OK] All chunk IDs match")
    print(f"[OK] Embedding dimension: {embedding_dimension}")
    print(f"[OK] All embeddings are numeric and valid")

    return embedding_dimension


def semantic_search(query, embedding_records, top_k=5):
    model = SentenceTransformer(EXPECTED_MODEL_NAME)

    query_embedding = model.encode(
        query,
        normalize_embeddings=True
    )

    results = []

    for record in embedding_records:
        chunk_embedding = np.array(record["embedding"])

        # Since embeddings are normalized, dot product is cosine similarity.
        score = float(np.dot(query_embedding, chunk_embedding))

        results.append({
            "score": score,
            "chunk_id": record["chunk_id"],
            "source_file": record["metadata"]["source_file"],
            "section_title": record["metadata"]["section_title"],
            "text": record["text"],
        })

    results.sort(key=lambda row: row["score"], reverse=True)

    return results[:top_k]


def test_semantic_retrieval(embedding_records):
    print("\nTesting semantic retrieval...\n")

    query = "When should a product be reordered?"

    results = semantic_search(
        query=query,
        embedding_records=embedding_records,
        top_k=5
    )

    print(f"Query: {query}\n")

    for index, result in enumerate(results, start=1):
        print(
            f"{index}. Score: {result['score']:.4f} | "
            f"Chunk: {result['chunk_id']} | "
            f"Source: {result['source_file']} | "
            f"Section: {result['section_title']}"
        )

    top_sources = {result["source_file"] for result in results}
    top_text = " ".join(result["text"].lower() for result in results)

    if "inventory_policy.txt" not in top_sources:
        raise ValueError("Semantic search did not retrieve inventory_policy.txt in top results.")

    if "reorder" not in top_text:
        raise ValueError("Semantic search results do not contain the word 'reorder'.")

    print("\n[OK] Semantic retrieval returned relevant chunks")


def main():
    chunks = load_jsonl(CHUNKS_FILE)
    embedding_records = load_jsonl(EMBEDDINGS_FILE)

    check_embedding_file(chunks, embedding_records)
    test_semantic_retrieval(embedding_records)

    print("\nEmbedding test completed successfully.")


if __name__ == "__main__":
    main()