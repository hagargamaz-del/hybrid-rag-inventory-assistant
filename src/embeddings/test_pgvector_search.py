from pathlib import Path
import os
import psycopg2
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5433"),
        dbname=os.getenv("DB_NAME", "inventory_rag"),
        user=os.getenv("DB_USER", "inventory_user"),
        password=os.getenv("DB_PASSWORD", "inventory_password"),
    )


def vector_to_pgvector_literal(vector):
    return "[" + ",".join(str(float(value)) for value in vector) + "]"


def check_table_loaded(cursor):
    print("Checking pgvector table...\n")

    cursor.execute("SELECT COUNT(*) FROM rag_document_chunks;")
    row_count = cursor.fetchone()[0]

    if row_count != 22:
        raise ValueError(f"Expected 22 chunks in rag_document_chunks, found {row_count}")

    cursor.execute("""
        SELECT DISTINCT vector_dims(embedding)
        FROM rag_document_chunks;
    """)
    dimensions = [row[0] for row in cursor.fetchall()]

    if dimensions != [384]:
        raise ValueError(f"Expected embedding dimension 384, found {dimensions}")

    print(f"[OK] rag_document_chunks row count: {row_count}")
    print(f"[OK] Embedding dimension: {dimensions[0]}")


def search_pgvector(cursor, query, model, top_k=5):
    query_embedding = model.encode(
        query,
        normalize_embeddings=True
    )

    query_vector = vector_to_pgvector_literal(query_embedding)

    cursor.execute(
        """
        SELECT
            chunk_id,
            source_file,
            section_title,
            ROUND((1 - (embedding <=> %s::vector))::numeric, 4) AS similarity,
            LEFT(text, 350) AS text_preview
        FROM rag_document_chunks
        ORDER BY embedding <=> %s::vector
        LIMIT %s;
        """,
        (query_vector, query_vector, top_k),
    )

    return cursor.fetchall()


def test_reorder_query(cursor, model):
    print("\nTesting pgvector semantic search...\n")

    query = "When should a product be reordered?"
    results = search_pgvector(cursor, query, model, top_k=5)

    print(f"Query: {query}\n")

    for index, row in enumerate(results, start=1):
        chunk_id, source_file, section_title, similarity, text_preview = row

        print(
            f"{index}. Similarity: {similarity} | "
            f"Chunk: {chunk_id} | "
            f"Source: {source_file} | "
            f"Section: {section_title}"
        )
        print(f"   Preview: {text_preview[:180]}...\n")

    top_sources = {row[1] for row in results}
    top_text = " ".join(row[4].lower() for row in results)

    if "inventory_policy.txt" not in top_sources:
        raise ValueError("pgvector search did not retrieve inventory_policy.txt.")

    if "reorder" not in top_text:
        raise ValueError("pgvector search results do not contain reorder-related content.")

    print("[OK] pgvector search returned relevant reorder policy chunks")


def test_supplier_query(cursor, model):
    print("\nTesting supplier policy retrieval...\n")

    query = "What should we do with suppliers that have long delivery times?"
    results = search_pgvector(cursor, query, model, top_k=5)

    print(f"Query: {query}\n")

    for index, row in enumerate(results, start=1):
        chunk_id, source_file, section_title, similarity, _ = row

        print(
            f"{index}. Similarity: {similarity} | "
            f"Chunk: {chunk_id} | "
            f"Source: {source_file} | "
            f"Section: {section_title}"
        )

    top_sources = {row[1] for row in results}

    if "supplier_policy.txt" not in top_sources:
        raise ValueError("pgvector search did not retrieve supplier_policy.txt.")

    print("\n[OK] pgvector search returned relevant supplier policy chunks")


def main():
    print(f"Loading embedding model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)
    print("[OK] Embedding model loaded\n")

    with get_connection() as connection:
        with connection.cursor() as cursor:
            check_table_loaded(cursor)
            test_reorder_query(cursor, model)
            test_supplier_query(cursor, model)

    print("\npgvector search test completed successfully.")


if __name__ == "__main__":
    main()