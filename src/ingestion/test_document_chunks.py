from pathlib import Path
import json
from collections import Counter

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHUNKS_FILE = PROJECT_ROOT / "data" / "processed" / "document_chunks.jsonl"

REQUIRED_METADATA_FIELDS = [
    "source_file",
    "title",
    "document_type",
    "department",
    "version",
    "section_number",
    "section_title",
    "chunk_index",
    "word_count",
    "char_count",
]

REQUIRED_KEYWORDS = [
    "reorder",
    "stockout",
    "supplier",
    "warehouse",
    "adjustment",
]


def load_chunks():
    if not CHUNKS_FILE.exists():
        raise FileNotFoundError(f"Missing chunks file: {CHUNKS_FILE}")

    chunks = []

    with open(CHUNKS_FILE, mode="r", encoding="utf-8") as file:
        for line in file:
            chunks.append(json.loads(line))

    return chunks


def check_basic_structure(chunks):
    print("Checking chunk structure...\n")

    if len(chunks) < 15:
        raise ValueError(f"Expected at least 15 chunks, found {len(chunks)}")

    chunk_ids = [chunk.get("chunk_id") for chunk in chunks]

    if len(chunk_ids) != len(set(chunk_ids)):
        raise ValueError("Duplicate chunk_id values found.")

    for chunk in chunks:
        if "chunk_id" not in chunk:
            raise ValueError("A chunk is missing chunk_id.")

        if "text" not in chunk or not chunk["text"].strip():
            raise ValueError(f"Chunk {chunk.get('chunk_id')} has empty text.")

        if "metadata" not in chunk:
            raise ValueError(f"Chunk {chunk.get('chunk_id')} is missing metadata.")

        metadata = chunk["metadata"]

        for field in REQUIRED_METADATA_FIELDS:
            if field not in metadata:
                raise ValueError(f"Chunk {chunk['chunk_id']} is missing metadata field: {field}")

        if metadata["word_count"] <= 0:
            raise ValueError(f"Chunk {chunk['chunk_id']} has invalid word_count.")

    print(f"[OK] Loaded {len(chunks)} chunks")
    print("[OK] All chunks have unique IDs")
    print("[OK] All chunks have text and required metadata")


def check_keyword_coverage(chunks):
    print("\nChecking keyword coverage...\n")

    all_text = "\n".join(chunk["text"].lower() for chunk in chunks)

    for keyword in REQUIRED_KEYWORDS:
        if keyword not in all_text:
            raise ValueError(f"Keyword not found in chunks: {keyword}")

        print(f"[OK] Keyword found in chunks: {keyword}")


def print_chunk_summary(chunks):
    print("\nChunk count by source document:\n")

    source_counts = Counter(chunk["metadata"]["source_file"] for chunk in chunks)

    for source_file, count in source_counts.items():
        print(f"- {source_file}: {count} chunks")

    word_counts = [chunk["metadata"]["word_count"] for chunk in chunks]

    print("\nChunk size summary:")
    print(f"- Minimum words: {min(word_counts)}")
    print(f"- Maximum words: {max(word_counts)}")
    print(f"- Average words: {sum(word_counts) / len(word_counts):.1f}")


def print_sample_chunks(chunks):
    print("\nSample chunks:\n")

    for chunk in chunks[:3]:
        metadata = chunk["metadata"]

        print("=" * 80)
        print(f"Chunk ID: {chunk['chunk_id']}")
        print(f"Source: {metadata['source_file']}")
        print(f"Document Type: {metadata['document_type']}")
        print(f"Section: {metadata['section_number']} - {metadata['section_title']}")
        print(f"Words: {metadata['word_count']}")
        print("\nText preview:")
        print(chunk["text"][:500])


def main():
    chunks = load_chunks()

    check_basic_structure(chunks)
    check_keyword_coverage(chunks)
    print_chunk_summary(chunks)
    print_sample_chunks(chunks)

    print("\nDocument chunk test completed successfully.")


if __name__ == "__main__":
    main()