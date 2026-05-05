from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOCUMENTS_DIR = PROJECT_ROOT / "data" / "documents"

REQUIRED_DOCUMENTS = [
    "inventory_policy.txt",
    "supplier_policy.txt",
    "returns_policy.txt",
    "warehouse_sop.txt",
    "product_handling_notes.txt",
]

REQUIRED_KEYWORDS = [
    "reorder",
    "stockout",
    "supplier",
    "inventory",
    "warehouse",
    "adjustment",
]


def read_document(file_path):
    with open(file_path, mode="r", encoding="utf-8") as file:
        return file.read()


def main():
    print("Checking business documents...\n")

    all_text = ""

    for document_name in REQUIRED_DOCUMENTS:
        file_path = DOCUMENTS_DIR / document_name

        if not file_path.exists():
            raise FileNotFoundError(f"Missing document: {file_path}")

        text = read_document(file_path)
        word_count = len(text.split())
        char_count = len(text)

        if word_count < 50:
            raise ValueError(f"{document_name} is too short. Word count: {word_count}")

        all_text += "\n" + text.lower()

        print(f"[OK] {document_name}: {word_count} words, {char_count} characters")

    print("\nChecking required RAG keywords...\n")

    for keyword in REQUIRED_KEYWORDS:
        if keyword.lower() not in all_text:
            raise ValueError(f"Keyword not found in documents: {keyword}")

        print(f"[OK] Keyword found: {keyword}")

    print("\nDocument preview:\n")

    sample_file = DOCUMENTS_DIR / "inventory_policy.txt"
    sample_text = read_document(sample_file)

    print(sample_text[:700])
    print("\nBusiness document test completed successfully.")


if __name__ == "__main__":
    main()