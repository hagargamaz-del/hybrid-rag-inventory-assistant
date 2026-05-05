import csv
import time
from pathlib import Path
from typing import Dict, List

import requests


PROJECT_ROOT = Path(__file__).resolve().parents[1]

QUESTIONS_FILE = PROJECT_ROOT / "evaluation" / "questions.csv"
RESULTS_FILE = PROJECT_ROOT / "evaluation" / "evaluation_results.csv"

API_URL = "http://127.0.0.1:8000"


def read_questions() -> List[Dict[str, str]]:
    if not QUESTIONS_FILE.exists():
        raise FileNotFoundError(f"Missing evaluation file: {QUESTIONS_FILE}")

    with open(QUESTIONS_FILE, mode="r", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def call_api(question: str) -> Dict:
    payload = {
        "question": question,
        "sql_limit": 5,
        "vector_top_k": 5,
        "include_retrieval_output": False,
    }

    response = requests.post(
        f"{API_URL}/ask",
        json=payload,
        timeout=180,
    )

    response.raise_for_status()
    return response.json()


def split_required_keywords(required_keywords: str) -> List[str]:
    if not required_keywords:
        return []

    return [
        keyword.strip()
        for keyword in required_keywords.split(";")
        if keyword.strip()
    ]


def check_mode(actual_mode: str, expected_mode: str) -> bool:
    return actual_mode.strip().lower() == expected_mode.strip().lower()


def check_sql_source(response: Dict, expected_sql_source: str) -> bool:
    if not expected_sql_source:
        return True

    sql_sources = response.get("sources", {}).get("sql_sources", [])
    sql_sources_text = " ".join(sql_sources).lower()

    return expected_sql_source.lower() in sql_sources_text


def check_document_source(response: Dict, expected_document_source: str) -> bool:
    if not expected_document_source:
        return True

    document_sources = response.get("sources", {}).get("document_sources", [])
    document_sources_text = " ".join(document_sources).lower()

    return expected_document_source.lower() in document_sources_text


def check_answer_keywords(response: Dict, required_keywords: str) -> bool:
    answer = response.get("answer", "").lower()
    keywords = split_required_keywords(required_keywords)

    for keyword in keywords:
        if keyword.lower() not in answer:
            return False

    return True


def evaluate_question(row: Dict[str, str]) -> Dict[str, str]:
    question = row["question"]

    start_time = time.perf_counter()
    response = call_api(question)
    end_time = time.perf_counter()

    latency_seconds = round(end_time - start_time, 3)

    actual_mode = response.get("retrieval_mode", "")

    mode_pass = check_mode(
        actual_mode=actual_mode,
        expected_mode=row["expected_mode"],
    )

    sql_source_pass = check_sql_source(
        response=response,
        expected_sql_source=row["expected_sql_source"],
    )

    document_source_pass = check_document_source(
        response=response,
        expected_document_source=row["expected_document_source"],
    )

    keyword_pass = check_answer_keywords(
        response=response,
        required_keywords=row["required_keywords"],
    )

    overall_pass = all([
        mode_pass,
        sql_source_pass,
        document_source_pass,
        keyword_pass,
    ])

    return {
        "question": question,
        "expected_mode": row["expected_mode"],
        "actual_mode": actual_mode,
        "mode_pass": mode_pass,
        "expected_sql_source": row["expected_sql_source"],
        "sql_source_pass": sql_source_pass,
        "expected_document_source": row["expected_document_source"],
        "document_source_pass": document_source_pass,
        "required_keywords": row["required_keywords"],
        "keyword_pass": keyword_pass,
        "latency_seconds": latency_seconds,
        "overall_pass": overall_pass,
        "answer_preview": response.get("answer", "")[:300].replace("\n", " "),
    }


def write_results(results: List[Dict[str, str]]) -> None:
    if not results:
        raise ValueError("No evaluation results to write.")

    fieldnames = list(results[0].keys())

    with open(RESULTS_FILE, mode="w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)


def print_summary(results: List[Dict[str, str]]) -> None:
    total = len(results)
    passed = sum(1 for result in results if result["overall_pass"])
    failed = total - passed

    average_latency = sum(
        float(result["latency_seconds"])
        for result in results
    ) / total

    print("\nEvaluation Summary")
    print("=" * 80)
    print(f"Total questions: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Pass rate: {(passed / total) * 100:.1f}%")
    print(f"Average latency: {average_latency:.3f} seconds")
    print(f"Results file: {RESULTS_FILE}")

    if failed > 0:
        print("\nFailed questions:")
        for result in results:
            if not result["overall_pass"]:
                print("-" * 80)
                print(f"Question: {result['question']}")
                print(f"Expected mode: {result['expected_mode']}")
                print(f"Actual mode: {result['actual_mode']}")
                print(f"Mode pass: {result['mode_pass']}")
                print(f"SQL source pass: {result['sql_source_pass']}")
                print(f"Document source pass: {result['document_source_pass']}")
                print(f"Keyword pass: {result['keyword_pass']}")
                print(f"Answer preview: {result['answer_preview']}")


def main():
    print("Running RAG API evaluation...\n")

    questions = read_questions()
    results = []

    for index, row in enumerate(questions, start=1):
        print(f"[{index}/{len(questions)}] Evaluating: {row['question']}")

        try:
            result = evaluate_question(row)
            results.append(result)

            status = "PASS" if result["overall_pass"] else "FAIL"
            print(
                f"    {status} | "
                f"mode={result['actual_mode']} | "
                f"latency={result['latency_seconds']}s"
            )

        except Exception as error:
            result = {
                "question": row["question"],
                "expected_mode": row["expected_mode"],
                "actual_mode": "ERROR",
                "mode_pass": False,
                "expected_sql_source": row["expected_sql_source"],
                "sql_source_pass": False,
                "expected_document_source": row["expected_document_source"],
                "document_source_pass": False,
                "required_keywords": row["required_keywords"],
                "keyword_pass": False,
                "latency_seconds": -1,
                "overall_pass": False,
                "answer_preview": str(error),
            }

            results.append(result)
            print(f"    ERROR | {error}")

    write_results(results)
    print_summary(results)


if __name__ == "__main__":
    main()