import requests


BASE_URL = "http://127.0.0.1:8000"


def test_health():
    response = requests.get(f"{BASE_URL}/health", timeout=30)

    if response.status_code != 200:
        raise ValueError(f"Health check failed: {response.status_code} - {response.text}")

    data = response.json()

    if data.get("status") != "ok":
        raise ValueError(f"Unexpected health response: {data}")

    print("[OK] FastAPI backend is reachable")


def test_chatbot_payload():
    payload = {
        "question": "Which products are at stockout risk and what policy explains the reorder action?",
        "sql_limit": 5,
        "vector_top_k": 5,
        "include_retrieval_output": False,
    }

    response = requests.post(f"{BASE_URL}/ask", json=payload, timeout=120)

    if response.status_code != 200:
        raise ValueError(f"/ask failed: {response.status_code} - {response.text}")

    data = response.json()

    required_fields = [
        "question",
        "retrieval_mode",
        "answer",
        "sources",
    ]

    for field in required_fields:
        if field not in data:
            raise ValueError(f"API response missing field: {field}")

    if data["retrieval_mode"] != "hybrid":
        raise ValueError(f"Expected hybrid retrieval, got {data['retrieval_mode']}")

    if "WiFi Extender" not in data["answer"]:
        raise ValueError("Expected response to mention WiFi Extender")

    print("[OK] Chatbot API payload works")


def main():
    print("Testing Streamlit-to-FastAPI connection...\n")

    test_health()
    test_chatbot_payload()

    print("\nStreamlit API connection test completed successfully.")


if __name__ == "__main__":
    main()