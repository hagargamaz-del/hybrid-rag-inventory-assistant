from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.rag.answer_generator import RAGAnswerGenerator


app = FastAPI(
    title="Inventory RAG Assistant",
    description=(
        "A hybrid RAG API that combines structured SQL analytics "
        "with vector-based document retrieval for inventory intelligence."
    ),
    version="1.0.0",
)

rag_generator = RAGAnswerGenerator()


class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, description="User business question")
    sql_limit: Optional[int] = Field(5, ge=1, le=20)
    vector_top_k: Optional[int] = Field(5, ge=1, le=20)
    include_retrieval_output: Optional[bool] = Field(
        False,
        description="Whether to include raw SQL/vector retrieval output in the API response.",
    )


def make_json_safe(value: Any) -> Any:
    """
    Convert non-JSON-safe Python/PostgreSQL values into JSON-safe values.
    Handles Decimal, date, datetime, dictionaries, and lists.
    """

    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, (date, datetime)):
        return value.isoformat()

    if isinstance(value, dict):
        return {key: make_json_safe(item) for key, item in value.items()}

    if isinstance(value, list):
        return [make_json_safe(item) for item in value]

    return value


@app.get("/")
def root() -> Dict[str, str]:
    return {
        "message": "Inventory RAG Data Engineering Assistant API",
        "docs": "/docs",
        "health": "/health",
        "ask_endpoint": "/ask",
    }


@app.get("/health")
def health_check() -> Dict[str, str]:
    return {
        "status": "ok",
        "service": "inventory-rag-api",
    }


@app.post("/ask")
def ask_question(request: AskRequest) -> Dict[str, Any]:
    try:
        response = rag_generator.generate_answer(
            question=request.question,
            sql_limit=request.sql_limit,
            vector_top_k=request.vector_top_k,
        )

        api_response = {
            "question": response["question"],
            "retrieval_mode": response["retrieval_mode"],
            "answer": response["answer"],
            "sources": response["sources"],
        }

        if request.include_retrieval_output:
            api_response["retrieval_output"] = response["retrieval_output"]

        return make_json_safe(api_response)

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(error)}",
        )