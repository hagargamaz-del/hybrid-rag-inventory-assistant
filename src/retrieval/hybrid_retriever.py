from typing import Any, Dict

from src.retrieval.sql_retriever import SQLRetriever
from src.retrieval.vector_retriever import VectorRetriever


class HybridRetriever:
    """
    Hybrid retrieval layer for the RAG assistant.

    It decides whether a question should use:
    1. SQL retrieval for structured business data.
    2. Vector retrieval for unstructured policy/document knowledge.
    3. Hybrid retrieval for questions requiring both.
    """

    def __init__(self):
        self.sql_retriever = SQLRetriever()
        self.vector_retriever = VectorRetriever()

    def classify_question(self, question: str) -> str:
        if not question or not question.strip():
            raise ValueError("Question cannot be empty.")

        question_lower = question.lower()

        sql_keywords = [
            "stockout",
            "stock out",
            "low stock",
            "reorder",
            "top selling",
            "top products",
            "selling products",
            "sales",
            "revenue",
            "supplier",
            "delivery",
            "current stock",
            "inventory level",
            "monthly",
            "trend",
            "business overview",
        ]

        document_keywords = [
            "policy",
            "rule",
            "procedure",
            "sop",
            "recommend",
            "recommended",
            "what should",
            "explain",
            "guideline",
            "according to",
            "handle",
            "investigate",
            "classification",
        ]

        has_sql_intent = any(keyword in question_lower for keyword in sql_keywords)
        has_document_intent = any(keyword in question_lower for keyword in document_keywords)

        if has_sql_intent and has_document_intent:
            return "hybrid"

        if has_sql_intent:
            return "sql"

        if has_document_intent:
            return "vector"

        return "vector"

    def retrieve(
        self,
        question: str,
        sql_limit: int = 5,
        vector_top_k: int = 5,
    ) -> Dict[str, Any]:
        retrieval_mode = self.classify_question(question)

        sql_output = None
        vector_output = None

        if retrieval_mode in ["sql", "hybrid"]:
            sql_output = self.sql_retriever.search(
                question=question,
                limit=sql_limit,
            )

        if retrieval_mode in ["vector", "hybrid"]:
            vector_output = self.vector_retriever.search(
                query=question,
                top_k=vector_top_k,
            )

        return {
            "question": question,
            "retrieval_mode": retrieval_mode,
            "sql_output": sql_output,
            "vector_output": vector_output,
        }

    def format_context(self, retrieval_output: Dict[str, Any]) -> str:
        lines = []

        lines.append(f"Question: {retrieval_output['question']}")
        lines.append(f"Retrieval Mode: {retrieval_output['retrieval_mode']}")
        lines.append("")

        if retrieval_output["sql_output"]:
            lines.append("=" * 80)
            lines.append("STRUCTURED SQL RESULTS")
            lines.append("=" * 80)
            lines.append(self.sql_retriever.format_results(retrieval_output["sql_output"]))
            lines.append("")

        if retrieval_output["vector_output"]:
            lines.append("=" * 80)
            lines.append("UNSTRUCTURED DOCUMENT CONTEXT")
            lines.append("=" * 80)
            lines.append(self.vector_retriever.format_results(retrieval_output["vector_output"]))
            lines.append("")

        return "\n".join(lines)