from pathlib import Path
import json
import re
from collections import defaultdict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOCUMENTS_DIR = PROJECT_ROOT / "data" / "documents"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_FILE = PROCESSED_DIR / "document_chunks.jsonl"

MAX_WORDS_PER_CHUNK = 120
OVERLAP_WORDS = 25


def read_text_file(file_path):
    with open(file_path, mode="r", encoding="utf-8") as file:
        return file.read().strip()


def extract_metadata(text, source_file):
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    title = lines[0] if lines else source_file

    metadata = {
        "source_file": source_file,
        "title": title,
        "document_type": extract_field(text, "Document Type"),
        "department": extract_field(text, "Department"),
        "version": extract_field(text, "Version"),
    }

    return metadata


def extract_field(text, field_name):
    pattern = rf"^{re.escape(field_name)}:\s*(.+)$"

    for line in text.splitlines():
        match = re.match(pattern, line.strip(), flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()

    return "Unknown"


def extract_sections(text):
    """
    Extract sections such as:
    1. Purpose
    2. Reorder Rules
    3. Stockout Risk Classification
    """

    lines = text.splitlines()
    sections = []

    current_section = None

    section_pattern = re.compile(r"^(\d+)\.\s+(.+)$")

    for line in lines:
        clean_line = line.strip()
        match = section_pattern.match(clean_line)

        if match:
            if current_section:
                sections.append(current_section)

            current_section = {
                "section_number": match.group(1),
                "section_title": match.group(2),
                "content_lines": [],
            }
        else:
            if current_section and clean_line:
                current_section["content_lines"].append(clean_line)

    if current_section:
        sections.append(current_section)

    return sections


def split_words_with_overlap(text, max_words, overlap_words):
    words = text.split()

    if len(words) <= max_words:
        return [text]

    chunks = []
    start = 0

    while start < len(words):
        end = start + max_words
        chunk_words = words[start:end]
        chunks.append(" ".join(chunk_words))

        if end >= len(words):
            break

        start = end - overlap_words

    return chunks


def create_chunks_for_document(file_path):
    text = read_text_file(file_path)
    base_metadata = extract_metadata(text, file_path.name)
    sections = extract_sections(text)

    chunks = []

    for section in sections:
        section_number = section["section_number"]
        section_title = section["section_title"]
        section_body = " ".join(section["content_lines"]).strip()

        if not section_body:
            continue

        chunk_text = (
            f"{base_metadata['title']}\n"
            f"Document Type: {base_metadata['document_type']}\n"
            f"Department: {base_metadata['department']}\n"
            f"Section {section_number}: {section_title}\n\n"
            f"{section_body}"
        )

        section_chunks = split_words_with_overlap(
            chunk_text,
            max_words=MAX_WORDS_PER_CHUNK,
            overlap_words=OVERLAP_WORDS,
        )

        for chunk_index, section_chunk in enumerate(section_chunks, start=1):
            chunk_id = (
                f"{file_path.stem}"
                f"_s{section_number.zfill(2)}"
                f"_c{str(chunk_index).zfill(2)}"
            )

            chunks.append({
                "chunk_id": chunk_id,
                "text": section_chunk,
                "metadata": {
                    **base_metadata,
                    "section_number": section_number,
                    "section_title": section_title,
                    "chunk_index": chunk_index,
                    "word_count": len(section_chunk.split()),
                    "char_count": len(section_chunk),
                }
            })

    return chunks


def write_jsonl(chunks, output_file):
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, mode="w", encoding="utf-8") as file:
        for chunk in chunks:
            file.write(json.dumps(chunk, ensure_ascii=False) + "\n")


def main():
    print("Chunking business documents...\n")

    document_files = sorted(DOCUMENTS_DIR.glob("*.txt"))

    if not document_files:
        raise FileNotFoundError(f"No .txt documents found in {DOCUMENTS_DIR}")

    all_chunks = []

    for file_path in document_files:
        chunks = create_chunks_for_document(file_path)
        all_chunks.extend(chunks)

        print(f"[OK] {file_path.name}: {len(chunks)} chunks")

    write_jsonl(all_chunks, OUTPUT_FILE)

    chunks_by_source = defaultdict(int)
    for chunk in all_chunks:
        chunks_by_source[chunk["metadata"]["source_file"]] += 1

    print("\nChunk summary:")
    for source_file, count in chunks_by_source.items():
        print(f"- {source_file}: {count} chunks")

    print(f"\nTotal chunks created: {len(all_chunks)}")
    print(f"Output file: {OUTPUT_FILE}")
    print("\nDocument chunking completed successfully.")


if __name__ == "__main__":
    main()