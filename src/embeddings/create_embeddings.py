from pathlib import Path
import json
from sentence_transformers import SentenceTransformer

PROJECT_ROOT = Path(__file__).resolve().parents[2]

CHUNKS_FILE = PROJECT_ROOT / "data" / "processed" / "document_chunks.jsonl"
EMBEDDINGS_FILE = PROJECT_ROOT / "data" / "processed" / "chunk_embeddings.jsonl"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def load_chunks():
    if not CHUNKS_FILE.exists():
        raise FileNotFoundError(f"Missing chunks file: {CHUNKS_FILE}")

    chunks = []

    with open(CHUNKS_FILE, mode="r", encoding="utf-8") as file:
        for line in file:
            chunks.append(json.loads(line))

    if not chunks:
        raise ValueError("No chunks found.")

    return chunks


def save_embeddings(records):
    EMBEDDINGS_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(EMBEDDINGS_FILE, mode="w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")


def main():
    print("Loading document chunks...")
    chunks = load_chunks()
    print(f"[OK] Loaded {len(chunks)} chunks")

    print(f"\nLoading embedding model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)
    print("[OK] Embedding model loaded")

    texts = [chunk["text"] for chunk in chunks]

    print("\nGenerating embeddings...")
    embeddings = model.encode(
        texts,
        batch_size=16,
        show_progress_bar=True,
        normalize_embeddings=True
    )

    records = []

    for chunk, embedding in zip(chunks, embeddings):
        records.append({
            "chunk_id": chunk["chunk_id"],
            "text": chunk["text"],
            "metadata": chunk["metadata"],
            "embedding_model": MODEL_NAME,
            "embedding_dimension": len(embedding),
            "embedding": embedding.tolist()
        })

    save_embeddings(records)

    print(f"\n[OK] Generated embeddings for {len(records)} chunks")
    print(f"[OK] Embedding dimension: {records[0]['embedding_dimension']}")
    print(f"[OK] Output file: {EMBEDDINGS_FILE}")
    print("\nEmbedding generation completed successfully.")


if __name__ == "__main__":
    main()