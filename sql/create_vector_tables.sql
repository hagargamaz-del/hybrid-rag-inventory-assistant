CREATE EXTENSION IF NOT EXISTS vector;

DROP TABLE IF EXISTS rag_document_chunks CASCADE;

CREATE TABLE rag_document_chunks (
    id SERIAL PRIMARY KEY,
    chunk_id VARCHAR(150) UNIQUE NOT NULL,
    source_file VARCHAR(255) NOT NULL,
    title TEXT,
    document_type VARCHAR(150),
    department VARCHAR(255),
    section_number VARCHAR(50),
    section_title VARCHAR(255),
    chunk_index INT,
    word_count INT,
    char_count INT,
    text TEXT NOT NULL,
    metadata JSONB NOT NULL,
    embedding_model VARCHAR(255) NOT NULL,
    embedding vector(384) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_rag_chunks_source_file
ON rag_document_chunks(source_file);

CREATE INDEX idx_rag_chunks_document_type
ON rag_document_chunks(document_type);

CREATE INDEX idx_rag_chunks_metadata
ON rag_document_chunks USING GIN(metadata);