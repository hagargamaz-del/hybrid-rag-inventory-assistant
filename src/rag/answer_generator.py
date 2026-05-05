from decimal import Decimal
from datetime import date, datetime
from typing import Any, Dict, List

from src.retrieval.hybrid_retriever import HybridRetriever


class RAGAnswerGenerator:
    """
    Grounded answer generator for the RAG assistant.

    This class:
    1. Calls the HybridRetriever.
    2. Receives SQL results and/or vector document chunks.
    3. Produces a clear business answer with explicit sources.

    Later, this class can be upgraded to use an LLM API.
    """

    def __init__(self):
        self.hybrid_retriever = HybridRetriever()

    @staticmethod
    def format_number(value: Any) -> str:
        if isinstance(value, Decimal):
            return f"{float(value):,.2f}"

        if isinstance(value, float):
            return f"{value:,.2f}"

        if isinstance(value, int):
            return f"{value:,}"

        if isinstance(value, (date, datetime)):
            return value.isoformat()

        return str(value)

    @staticmethod
    def format_money(value: Any) -> str:
        if value is None:
            return "$0.00"

        if isinstance(value, Decimal):
            return f"${float(value):,.2f}"

        if isinstance(value, (int, float)):
            return f"${value:,.2f}"

        return f"${value}"

    @staticmethod
    def get_document_sources(vector_output: List[Dict[str, Any]]) -> List[str]:
        if not vector_output:
            return []

        sources = []

        for chunk in vector_output:
            source = (
                f"{chunk['source_file']} | "
                f"Section {chunk['section_number']}: {chunk['section_title']} | "
                f"Similarity: {chunk['similarity']:.4f}"
            )
            sources.append(source)

        return sources

    @staticmethod
    def summarize_document_context(vector_output: List[Dict[str, Any]], max_chunks: int = 3) -> List[str]:
        if not vector_output:
            return []

        summaries = []

        for chunk in vector_output[:max_chunks]:
            text = chunk["text"].replace("\n", " ").strip()
            section = chunk["section_title"]
            source_file = chunk["source_file"]

            summaries.append(
                f"- {source_file}, section '{section}': {text[:350]}..."
            )

        return summaries

    def generate_answer(
        self,
        question: str,
        sql_limit: int = 5,
        vector_top_k: int = 5,
    ) -> Dict[str, Any]:
        retrieval_output = self.hybrid_retriever.retrieve(
            question=question,
            sql_limit=sql_limit,
            vector_top_k=vector_top_k,
        )

        answer = self.build_answer(retrieval_output)
        sources = self.build_sources(retrieval_output)

        return {
            "question": question,
            "retrieval_mode": retrieval_output["retrieval_mode"],
            "answer": answer,
            "sources": sources,
            "retrieval_output": retrieval_output,
        }

    def build_answer(self, retrieval_output: Dict[str, Any]) -> str:
        sql_output = retrieval_output["sql_output"]
        vector_output = retrieval_output["vector_output"]
        retrieval_mode = retrieval_output["retrieval_mode"]

        if sql_output:
            query_type = sql_output["query_type"]

            if query_type == "stockout_risk":
                return self.build_stockout_answer(sql_output, vector_output, retrieval_mode)

            if query_type == "top_selling_products":
                return self.build_top_selling_answer(sql_output, vector_output, retrieval_mode)

            if query_type == "supplier_performance":
                return self.build_supplier_answer(sql_output, vector_output, retrieval_mode)

            if query_type == "monthly_sales":
                return self.build_monthly_sales_answer(sql_output, vector_output, retrieval_mode)

            if query_type == "current_stock":
                return self.build_current_stock_answer(sql_output, vector_output, retrieval_mode)

            if query_type == "business_overview":
                return self.build_business_overview_answer(sql_output, vector_output, retrieval_mode)

        if vector_output:
            return self.build_document_only_answer(vector_output, retrieval_mode)

        return "I could not find enough structured data or document context to answer this question."

    def build_stockout_answer(
        self,
        sql_output: Dict[str, Any],
        vector_output: List[Dict[str, Any]],
        retrieval_mode: str,
    ) -> str:
        rows = sql_output["results"]

        lines = []
        lines.append("Stockout-risk analysis")
        lines.append("")
        lines.append(f"Retrieval mode: {retrieval_mode}")
        lines.append("")
        lines.append("The following products require attention:")

        for row in rows:
            lines.append(
                f"- {row['product_name']} ({row['category']}): "
                f"current stock = {row['current_stock']}, "
                f"reorder level = {row['reorder_level']}, "
                f"suggested reorder quantity = {row['suggested_reorder_quantity']}, "
                f"status = {row['risk_status']}."
            )

        if vector_output:
            lines.append("")
            lines.append("Relevant policy context:")
            lines.extend(self.summarize_document_context(vector_output, max_chunks=3))

        lines.append("")
        lines.append(
            "Business interpretation: products with CRITICAL_STOCKOUT should be treated as urgent replenishment cases. "
            "Products with REORDER_REQUIRED should be reordered according to the suggested reorder quantity."
        )

        return "\n".join(lines)

    def build_top_selling_answer(
        self,
        sql_output: Dict[str, Any],
        vector_output: List[Dict[str, Any]],
        retrieval_mode: str,
    ) -> str:
        rows = sql_output["results"]

        lines = []
        lines.append("Top-selling products")
        lines.append("")
        lines.append(f"Retrieval mode: {retrieval_mode}")
        lines.append("")

        for index, row in enumerate(rows, start=1):
            lines.append(
                f"{index}. {row['product_name']} ({row['category']}) "
                f"from {row['supplier_name']}: "
                f"{row['total_units_sold']} units sold, "
                f"net revenue = {self.format_money(row['net_revenue'])}, "
                f"estimated profit = {self.format_money(row['estimated_profit'])}."
            )

        if vector_output:
            lines.append("")
            lines.append("Relevant document context:")
            lines.extend(self.summarize_document_context(vector_output, max_chunks=2))

        return "\n".join(lines)

    def build_supplier_answer(
        self,
        sql_output: Dict[str, Any],
        vector_output: List[Dict[str, Any]],
        retrieval_mode: str,
    ) -> str:
        rows = sql_output["results"]

        lines = []
        lines.append("Supplier performance analysis")
        lines.append("")
        lines.append(f"Retrieval mode: {retrieval_mode}")
        lines.append("")
        lines.append("Suppliers with the longest delivery times are:")

        for row in rows:
            lines.append(
                f"- {row['supplier_name']} ({row['country']}): "
                f"average delivery = {row['avg_delivery_days']} days, "
                f"reliability score = {row['reliability_score']}, "
                f"products supplied = {row['number_of_products']}, "
                f"total revenue = {self.format_money(row['total_revenue'])}."
            )

        if vector_output:
            lines.append("")
            lines.append("Relevant procurement policy context:")
            lines.extend(self.summarize_document_context(vector_output, max_chunks=3))

        lines.append("")
        lines.append(
            "Business interpretation: suppliers with long delivery times should be considered high lead-time suppliers. "
            "If they also have low reliability, procurement should review alternatives or place replenishment orders earlier."
        )

        return "\n".join(lines)

    def build_monthly_sales_answer(
        self,
        sql_output: Dict[str, Any],
        vector_output: List[Dict[str, Any]],
        retrieval_mode: str,
    ) -> str:
        rows = sql_output["results"]

        lines = []
        lines.append("Monthly sales trend")
        lines.append("")
        lines.append(f"Retrieval mode: {retrieval_mode}")
        lines.append("")

        for row in rows:
            lines.append(
                f"- {row['month_start']}: "
                f"{row['number_of_orders']} orders, "
                f"{row['total_units_sold']} units sold, "
                f"net revenue = {self.format_money(row['net_revenue'])}."
            )

        return "\n".join(lines)

    def build_current_stock_answer(
        self,
        sql_output: Dict[str, Any],
        vector_output: List[Dict[str, Any]],
        retrieval_mode: str,
    ) -> str:
        rows = sql_output["results"]

        lines = []
        lines.append("Lowest current stock products")
        lines.append("")
        lines.append(f"Retrieval mode: {retrieval_mode}")
        lines.append("")

        for row in rows:
            lines.append(
                f"- {row['product_name']} ({row['category']}): "
                f"current stock = {row['current_stock']}, "
                f"reorder level = {row['reorder_level']}, "
                f"target stock = {row['target_stock']}."
            )

        if vector_output:
            lines.append("")
            lines.append("Relevant document context:")
            lines.extend(self.summarize_document_context(vector_output, max_chunks=2))

        return "\n".join(lines)

    def build_business_overview_answer(
        self,
        sql_output: Dict[str, Any],
        vector_output: List[Dict[str, Any]],
        retrieval_mode: str,
    ) -> str:
        row = sql_output["results"][0]

        lines = []
        lines.append("Business overview")
        lines.append("")
        lines.append(f"Retrieval mode: {retrieval_mode}")
        lines.append("")
        lines.append(f"- Number of products: {row['number_of_products']}")
        lines.append(f"- Number of suppliers: {row['number_of_suppliers']}")
        lines.append(f"- Number of orders: {row['number_of_orders']}")
        lines.append(f"- Number of order items: {row['number_of_order_items']}")
        lines.append(f"- Products at stockout/reorder risk: {row['stockout_risk_products']}")
        lines.append(f"- Total revenue: {self.format_money(row['total_revenue'])}")

        return "\n".join(lines)

    def build_document_only_answer(
        self,
        vector_output: List[Dict[str, Any]],
        retrieval_mode: str,
    ) -> str:
        lines = []
        lines.append("Document-based answer")
        lines.append("")
        lines.append(f"Retrieval mode: {retrieval_mode}")
        lines.append("")
        lines.append("Relevant document context:")
        lines.extend(self.summarize_document_context(vector_output, max_chunks=5))

        return "\n".join(lines)

    def build_sources(self, retrieval_output: Dict[str, Any]) -> Dict[str, Any]:
        sources = {
            "sql_sources": [],
            "document_sources": [],
        }

        sql_output = retrieval_output["sql_output"]
        vector_output = retrieval_output["vector_output"]

        if sql_output:
            query_type = sql_output["query_type"]

            if query_type == "stockout_risk":
                sources["sql_sources"].append("vw_stockout_risk")

            elif query_type == "top_selling_products":
                sources["sql_sources"].append("vw_sales_by_product")

            elif query_type == "supplier_performance":
                sources["sql_sources"].append("vw_supplier_performance")

            elif query_type == "monthly_sales":
                sources["sql_sources"].append("vw_monthly_sales")

            elif query_type == "current_stock":
                sources["sql_sources"].append("vw_current_stock")

            elif query_type == "business_overview":
                sources["sql_sources"].extend([
                    "dim_products",
                    "dim_suppliers",
                    "fact_orders",
                    "fact_order_items",
                    "vw_stockout_risk",
                    "vw_sales_by_product",
                ])

        if vector_output:
            sources["document_sources"] = self.get_document_sources(vector_output)

        return sources

    @staticmethod
    def print_response(response: Dict[str, Any]) -> None:
        print("=" * 90)
        print("QUESTION")
        print("=" * 90)
        print(response["question"])

        print("\n" + "=" * 90)
        print("ANSWER")
        print("=" * 90)
        print(response["answer"])

        print("\n" + "=" * 90)
        print("SOURCES")
        print("=" * 90)

        sql_sources = response["sources"]["sql_sources"]
        document_sources = response["sources"]["document_sources"]

        if sql_sources:
            print("\nSQL Sources:")
            for source in sql_sources:
                print(f"- {source}")

        if document_sources:
            print("\nDocument Sources:")
            for source in document_sources:
                print(f"- {source}")

        print()