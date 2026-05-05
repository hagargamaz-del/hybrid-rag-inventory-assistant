from pathlib import Path
import os
from typing import Any, Dict, List

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")


class SQLRetriever:
    """
    Reusable SQL retriever for structured business analytics.

    This class:
    1. Receives a natural-language business question.
    2. Routes it to a predefined safe SQL query.
    3. Executes the query against PostgreSQL.
    4. Returns structured results with metadata.
    """

    def get_connection(self):
        return psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5433"),
            dbname=os.getenv("DB_NAME", "inventory_rag"),
            user=os.getenv("DB_USER", "inventory_user"),
            password=os.getenv("DB_PASSWORD", "inventory_password"),
        )

    def route_query(self, question: str) -> str:
        if not question or not question.strip():
            raise ValueError("Question cannot be empty.")

        question_lower = question.lower()

        if any(
            keyword in question_lower
            for keyword in [
                "stockout",
                "stock out",
                "low stock",
                "reorder",
                "out of stock",
                "risk",
                "critical stock",
            ]
        ):
            return "stockout_risk"

        if (
            any(
                keyword in question_lower
                for keyword in [
                    "top selling",
                    "best selling",
                    "most sold",
                    "highest sales",
                    "highest revenue",
                    "top products",
                    "selling products",
                    "sold products",
                    "highest profit",
                    "most profitable",
                ]
            )
            or ("top" in question_lower and "selling" in question_lower)
            or ("top" in question_lower and "sold" in question_lower)
        ):
            return "top_selling_products"

        if any(
            keyword in question_lower
            for keyword in [
                "supplier",
                "delivery",
                "lead time",
                "reliability",
                "procurement",
            ]
        ):
            return "supplier_performance"

        if any(
            keyword in question_lower
            for keyword in [
                "monthly",
                "month",
                "trend",
                "revenue trend",
                "sales trend",
            ]
        ):
            return "monthly_sales"

        if any(
            keyword in question_lower
            for keyword in [
                "current stock",
                "stock level",
                "inventory level",
                "available stock",
                "lowest stock",
            ]
        ):
            return "current_stock"

        return "business_overview"

    def get_query_config(self, query_type: str) -> Dict[str, Any]:
        query_configs = {
            "stockout_risk": {
                "description": "Products that are currently at stockout or reorder risk.",
                "sql": """
                    SELECT
                        product_id,
                        product_name,
                        category,
                        current_stock,
                        reorder_level,
                        target_stock,
                        suggested_reorder_quantity,
                        risk_status
                    FROM vw_stockout_risk
                    ORDER BY
                        CASE
                            WHEN risk_status = 'CRITICAL_STOCKOUT' THEN 1
                            WHEN risk_status = 'REORDER_REQUIRED' THEN 2
                            WHEN risk_status = 'WATCHLIST' THEN 3
                            ELSE 4
                        END,
                        current_stock ASC
                    LIMIT %s;
                """,
            },
            "top_selling_products": {
                "description": "Top-selling products by total units sold.",
                "sql": """
                    SELECT
                        product_id,
                        product_name,
                        category,
                        supplier_name,
                        total_units_sold,
                        net_revenue,
                        estimated_profit
                    FROM vw_sales_by_product
                    ORDER BY total_units_sold DESC
                    LIMIT %s;
                """,
            },
            "supplier_performance": {
                "description": "Supplier performance based on delivery time, reliability, product count, and revenue.",
                "sql": """
                    SELECT
                        supplier_id,
                        supplier_name,
                        country,
                        avg_delivery_days,
                        reliability_score,
                        number_of_products,
                        total_units_sold,
                        total_revenue
                    FROM vw_supplier_performance
                    ORDER BY avg_delivery_days DESC, reliability_score ASC
                    LIMIT %s;
                """,
            },
            "monthly_sales": {
                "description": "Monthly sales trend based on orders, units sold, and revenue.",
                "sql": """
                    SELECT
                        month_start,
                        number_of_orders,
                        total_units_sold,
                        net_revenue
                    FROM vw_monthly_sales
                    ORDER BY month_start DESC
                    LIMIT %s;
                """,
            },
            "current_stock": {
                "description": "Current stock levels for products, ordered from lowest to highest stock.",
                "sql": """
                    SELECT
                        product_id,
                        product_name,
                        category,
                        current_stock,
                        reorder_level,
                        target_stock
                    FROM vw_current_stock
                    ORDER BY current_stock ASC
                    LIMIT %s;
                """,
            },
            "business_overview": {
                "description": "General business overview across revenue, products, orders, and stockout risk.",
                "sql": """
                    SELECT
                        (SELECT COUNT(*) FROM dim_products) AS number_of_products,
                        (SELECT COUNT(*) FROM dim_suppliers) AS number_of_suppliers,
                        (SELECT COUNT(*) FROM fact_orders) AS number_of_orders,
                        (SELECT COUNT(*) FROM fact_order_items) AS number_of_order_items,
                        (SELECT COUNT(*) FROM vw_stockout_risk) AS stockout_risk_products,
                        (SELECT ROUND(SUM(net_revenue), 2) FROM vw_sales_by_product) AS total_revenue;
                """,
            },
        }

        if query_type not in query_configs:
            raise ValueError(f"Unsupported query type: {query_type}")

        return query_configs[query_type]

    def execute_query(self, sql: str, params=None) -> List[Dict[str, Any]]:
        params = params or []

        with self.get_connection() as connection:
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(sql, params)
                rows = cursor.fetchall()

        return [dict(row) for row in rows]

    def search(self, question: str, limit: int = 5) -> Dict[str, Any]:
        query_type = self.route_query(question)
        query_config = self.get_query_config(query_type)

        if query_type == "business_overview":
            params = []
        else:
            params = [limit]

        results = self.execute_query(
            sql=query_config["sql"],
            params=params,
        )

        return {
            "question": question,
            "query_type": query_type,
            "description": query_config["description"],
            "row_count": len(results),
            "results": results,
        }

    @staticmethod
    def format_results(retrieval_output: Dict[str, Any]) -> str:
        results = retrieval_output["results"]

        if not results:
            return "No structured SQL results were found."

        lines = []

        lines.append(f"Question: {retrieval_output['question']}")
        lines.append(f"Query Type: {retrieval_output['query_type']}")
        lines.append(f"Description: {retrieval_output['description']}")
        lines.append(f"Rows Returned: {retrieval_output['row_count']}")
        lines.append("")

        for index, row in enumerate(results, start=1):
            lines.append(f"[Row {index}]")

            for key, value in row.items():
                lines.append(f"{key}: {value}")

            lines.append("")

        return "\n".join(lines)