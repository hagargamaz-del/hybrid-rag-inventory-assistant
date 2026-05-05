from pathlib import Path
import json
import os
import psycopg2
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EMBEDDINGS_FILE = PROJECT_ROOT / "data" / "processed" / "chunk_embeddings.jsonl"

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


def load_embedding_records():
    if not EMBEDDINGS_FILE.exists():
        raise FileNotFoundError(f"Missing embeddings file: {EMBEDDINGS_FILE}")

    records = []

    with open(EMBEDDINGS_FILE, mode="r", encoding="utf-8") as file:
        for line in file:
            records.append(json.loads(line))

    if not records:
        raise ValueError("No embedding records found.")

    return records


def vector_to_pgvector_literal(vector):
    return "[" + ",".join(str(float(value)) for value in vector) + "]"


def insert_embedding_records(connection, records):
    insert_sql = """
        INSERT INTO rag_document_chunks (
            chunk_id,
            source_file,
            title,
            document_type,
            department,
            section_number,
            section_title,
            chunk_index,
            word_count,
            char_count,
            text,
            metadata,
            embedding_model,
            embedding
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::vector
        );
    """

    print(f"\nLoading {len(records)} embedding records into PostgreSQL...\n")

    with connection.cursor() as cursor:
        for record in records:
            metadata = record["metadata"]
            embedding_literal = vector_to_pgvector_literal(record["embedding"])

            cursor.execute(
                insert_sql,
                (
                    record["chunk_id"],
                    metadata["source_file"],
                    metadata["title"],
                    metadata["document_type"],
                    metadata["department"],
                    metadata["section_number"],
                    metadata["section_title"],
                    metadata["chunk_index"],
                    metadata["word_count"],
                    metadata["char_count"],
                    record["text"],
                    json.dumps(metadata),
                    record["embedding_model"],
                    embedding_literal,
                ),
            )

    connection.commit()
    print("[OK] Embedding records loaded successfully")


def main():
    records = load_embedding_records()
    print(f"[OK] Loaded {len(records)} records from {EMBEDDINGS_FILE}")

    with get_connection() as connection:
        run_sql_file(connection, PROJECT_ROOT / "sql" / "create_vector_tables.sql")
        insert_embedding_records(connection, records)

    print("\npgvector loading completed successfully.")


if __name__ == "__main__":
    main()