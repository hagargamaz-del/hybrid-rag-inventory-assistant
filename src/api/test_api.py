import requests


BASE_URL = "http://127.0.0.1:8000"


def test_health():
    response = requests.get(f"{BASE_URL}/health", timeout=30)

    if response.status_code != 200:
        raise ValueError(f"Health check failed: {response.status_code} - {response.text}")

    data = response.json()

    if data.get("status") != "ok":
        raise ValueError(f"Unexpected health response: {data}")

    print("[OK] Health endpoint works")


def test_ask_stockout_hybrid():
    payload = {
        "question": "Which products are at stockout risk and what policy explains the reorder action?",
        "sql_limit": 5,
        "vector_top_k": 5,
    }

    response = requests.post(f"{BASE_URL}/ask", json=payload, timeout=120)

    if response.status_code != 200:
        raise ValueError(f"/ask failed: {response.status_code} - {response.text}")

    data = response.json()

    print("\nStockout hybrid response:")
    print(f"Retrieval mode: {data['retrieval_mode']}")
    print(f"Answer preview: {data['answer'][:500]}...")

    if data["retrieval_mode"] != "hybrid":
        raise ValueError("Expected retrieval_mode = hybrid")

    if "WiFi Extender" not in data["answer"]:
        raise ValueError("Expected answer to mention WiFi Extender")

    if "vw_stockout_risk" not in data["sources"]["sql_sources"]:
        raise ValueError("Expected SQL source vw_stockout_risk")

    document_sources_text = " ".join(data["sources"]["document_sources"])

    if "inventory_policy.txt" not in document_sources_text:
        raise ValueError("Expected document source inventory_policy.txt")

    print("[OK] /ask hybrid stockout question works")


def test_ask_sql_only():
    payload = {
        "question": "What are the top 5 selling products?",
        "sql_limit": 5,
        "vector_top_k": 5,
    }

    response = requests.post(f"{BASE_URL}/ask", json=payload, timeout=120)

    if response.status_code != 200:
        raise ValueError(f"/ask failed: {response.status_code} - {response.text}")

    data = response.json()

    print("\nTop-selling SQL response:")
    print(f"Retrieval mode: {data['retrieval_mode']}")
    print(f"Answer preview: {data['answer'][:500]}...")

    if data["retrieval_mode"] != "sql":
        raise ValueError("Expected retrieval_mode = sql")

    if "External SSD" not in data["answer"]:
        raise ValueError("Expected answer to mention External SSD")

    if "vw_sales_by_product" not in data["sources"]["sql_sources"]:
        raise ValueError("Expected SQL source vw_sales_by_product")

    print("[OK] /ask SQL-only question works")


def test_ask_vector_only():
    payload = {
        "question": "Explain the warehouse movement procedure.",
        "sql_limit": 5,
        "vector_top_k": 5,
    }

    response = requests.post(f"{BASE_URL}/ask", json=payload, timeout=120)

    if response.status_code != 200:
        raise ValueError(f"/ask failed: {response.status_code} - {response.text}")

    data = response.json()

    print("\nWarehouse vector response:")
    print(f"Retrieval mode: {data['retrieval_mode']}")
    print(f"Answer preview: {data['answer'][:500]}...")

    if data["retrieval_mode"] != "vector":
        raise ValueError("Expected retrieval_mode = vector")

    document_sources_text = " ".join(data["sources"]["document_sources"])

    if "warehouse_sop.txt" not in document_sources_text:
        raise ValueError("Expected document source warehouse_sop.txt")

    print("[OK] /ask vector-only question works")


def main():
    print("Testing FastAPI backend...\n")

    test_health()
    test_ask_stockout_hybrid()
    test_ask_sql_only()
    test_ask_vector_only()

    print("\nFastAPI backend test completed successfully.")


if __name__ == "__main__":
    main()