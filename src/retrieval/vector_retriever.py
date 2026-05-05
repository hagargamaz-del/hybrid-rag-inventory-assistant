from pathlib import Path
import os
from typing import Any, Dict, List, Optional

import psycopg2
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer


PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")


class VectorRetriever:
    """
    Reusable pgvector-based retriever for document chunks.

    This class:
    1. Converts the user query into an embedding.
    2. Searches PostgreSQL/pgvector for semantically similar chunks.
    3. Returns chunks with metadata and similarity scores.
    """

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    ):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def get_connection(self):
        return psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5433"),
            dbname=os.getenv("DB_NAME", "inventory_rag"),
            user=os.getenv("DB_USER", "inventory_user"),
            password=os.getenv("DB_PASSWORD", "inventory_password"),
        )

    @staticmethod
    def vector_to_pgvector_literal(vector) -> str:
        return "[" + ",".join(str(float(value)) for value in vector) + "]"

    def embed_query(self, query: str) -> str:
        if not query or not query.strip():
            raise ValueError("Query cannot be empty.")

        query_embedding = self.model.encode(
            query,
            normalize_embeddings=True,
        )

        return self.vector_to_pgvector_literal(query_embedding)

    def count_chunks(self) -> int:
        with self.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM rag_document_chunks;")
                return cursor.fetchone()[0]

    def search(
        self,
        query: str,
        top_k: int = 5,
        document_type: Optional[str] = None,
        minimum_similarity: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant document chunks.

        Parameters:
            query: User question.
            top_k: Number of chunks to retrieve.
            document_type: Optional filter, e.g. "Inventory Policy".
            minimum_similarity: Optional threshold, e.g. 0.35.

        Returns:
            List of retrieved chunks.
        """

        query_vector = self.embed_query(query)

        where_clauses = []
        params = []

        if document_type:
            where_clauses.append("document_type = %s")
            params.append(document_type)

        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        sql = f"""
            SELECT
                chunk_id,
                source_file,
                title,
                document_type,
                department,
                section_number,
                section_title,
                chunk_index,
                word_count,
                text,
                metadata,
                ROUND((1 - (embedding <=> %s::vector))::numeric, 4) AS similarity
            FROM rag_document_chunks
            {where_sql}
            ORDER BY embedding <=> %s::vector
            LIMIT %s;
        """

        final_params = [query_vector] + params + [query_vector, top_k]

        with self.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, final_params)
                rows = cursor.fetchall()

        results = []

        for row in rows:
            result = {
                "chunk_id": row[0],
                "source_file": row[1],
                "title": row[2],
                "document_type": row[3],
                "department": row[4],
                "section_number": row[5],
                "section_title": row[6],
                "chunk_index": row[7],
                "word_count": row[8],
                "text": row[9],
                "metadata": row[10],
                "similarity": float(row[11]),
            }

            if minimum_similarity is None or result["similarity"] >= minimum_similarity:
                results.append(result)

        return results

    @staticmethod
    def format_results(results: List[Dict[str, Any]]) -> str:
        if not results:
            return "No relevant document chunks were found."

        formatted_blocks = []

        for index, result in enumerate(results, start=1):
            block = (
                f"[Source {index}]\n"
                f"Chunk ID: {result['chunk_id']}\n"
                f"Source File: {result['source_file']}\n"
                f"Document Type: {result['document_type']}\n"
                f"Section: {result['section_number']} - {result['section_title']}\n"
                f"Similarity: {result['similarity']:.4f}\n"
                f"Text:\n{result['text']}"
            )

            formatted_blocks.append(block)

        return "\n\n" + ("-" * 80 + "\n\n").join(formatted_blocks)