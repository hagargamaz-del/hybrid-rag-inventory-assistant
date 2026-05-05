# Hybrid RAG Data Engineering Assistant

A data engineering portfolio project that combines **structured SQL analytics** with **RAG-based document retrieval** to answer inventory, sales, supplier, and warehouse policy questions.

The system uses PostgreSQL, pgvector, FastAPI, Streamlit, and sentence-transformer embeddings to provide grounded answers with SQL and document sources.

---

## Project Overview

This project demonstrates a production-style RAG pipeline for business data.

It can answer questions such as:

- Which products are at stockout risk?
- What are the top-selling products?
- Which suppliers have long delivery times?
- What policy explains the reorder action?
- How should negative inventory be investigated?
- What is the monthly sales trend?

Unlike a basic chatbot, this project combines:

- **Structured data retrieval** using PostgreSQL and SQL views
- **Unstructured document retrieval** using embeddings and pgvector
- **Hybrid retrieval** that combines SQL results with policy document context
- **FastAPI backend**
- **Streamlit chatbot interface**
- **RAG evaluation workflow**

---

## Business Problem

Inventory teams often need answers that require both database analytics and internal policy knowledge.

For example:

> Which products are at stockout risk and what policy explains the reorder action?

This question requires:

1. SQL analysis from inventory tables
2. Policy retrieval from internal business documents
3. A final answer grounded in both sources

This project solves that using a hybrid RAG architecture.

---

## Architecture

```text
User Question
    |
    v
Streamlit Chatbot
    |
    v
FastAPI /ask Endpoint
    |
    v
RAG Answer Generator
    |
    v
Hybrid Retriever
    |
    +--------------------+--------------------+
    |                                         |
    v                                         v
SQL Retriever                         Vector Retriever
PostgreSQL Views                      pgvector Search
    |                                         |
    v                                         v
Structured Results                    Document Chunks
    |                                         |
    +--------------------+--------------------+
                         |
                         v
             Grounded Answer + Sources
```

## Screenshots

### Streamlit Chatbot

<img width="1199" height="683" alt="Screenshot 2026-05-05 162829" src="https://github.com/user-attachments/assets/1c4474d3-b334-4394-a1bf-11a802521544" />
<img width="1371" height="796" alt="Screenshot 2026-05-05 162811" src="https://github.com/user-attachments/assets/81d11d52-5f2a-46d9-9c2b-2166645d54b8" />


