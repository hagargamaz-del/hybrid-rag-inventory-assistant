import os
import requests
import streamlit as st


API_URL = os.getenv("RAG_API_URL", "http://127.0.0.1:8000")


st.set_page_config(
    page_title="Inventory RAG Assistant",
    page_icon="📦",
    layout="wide",
)


def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "last_response" not in st.session_state:
        st.session_state.last_response = None


def call_rag_api(question, sql_limit, vector_top_k, include_retrieval_output):
    payload = {
        "question": question,
        "sql_limit": sql_limit,
        "vector_top_k": vector_top_k,
        "include_retrieval_output": include_retrieval_output,
    }

    response = requests.post(
        f"{API_URL}/ask",
        json=payload,
        timeout=180,
    )

    response.raise_for_status()

    return response.json()


def check_api_health():
    try:
        response = requests.get(f"{API_URL}/health", timeout=10)

        if response.status_code == 200:
            return True, response.json()

        return False, {"error": response.text}

    except requests.exceptions.RequestException as error:
        return False, {"error": str(error)}


def display_sources(sources):
    sql_sources = sources.get("sql_sources", [])
    document_sources = sources.get("document_sources", [])

    if sql_sources:
        st.markdown("#### SQL Sources")
        for source in sql_sources:
            st.code(source, language="text")

    if document_sources:
        st.markdown("#### Document Sources")
        for source in document_sources:
            st.code(source, language="text")


def display_retrieval_output(retrieval_output):
    if not retrieval_output:
        return

    with st.expander("Raw Retrieval Output", expanded=False):
        st.json(retrieval_output)


def add_sample_question_buttons():
    st.markdown("### Sample Questions")

    sample_questions = [
        "Which products are at stockout risk and what policy explains the reorder action?",
        "What are the top 5 selling products?",
        "Which suppliers have long delivery times and what procurement policy should we follow?",
        "Explain the warehouse movement procedure.",
        "Show monthly revenue trend.",
        "Give me a business overview.",
    ]

    selected_question = None

    for question in sample_questions:
        if st.button(question, use_container_width=True):
            selected_question = question

    return selected_question


def render_sidebar():
    st.sidebar.title("Inventory RAG Assistant")
    st.sidebar.markdown(
        """
        This assistant combines:

        - SQL analytics over structured inventory data
        - pgvector semantic search over business documents
        - hybrid retrieval for business + policy questions
        """
    )

    st.sidebar.divider()

    api_ok, api_response = check_api_health()

    if api_ok:
        st.sidebar.success("FastAPI backend is running")
    else:
        st.sidebar.error("FastAPI backend is not reachable")
        st.sidebar.code(api_response.get("error", "Unknown error"), language="text")

    st.sidebar.divider()

    sql_limit = st.sidebar.slider(
        "SQL result limit",
        min_value=1,
        max_value=20,
        value=5,
    )

    vector_top_k = st.sidebar.slider(
        "Document chunks to retrieve",
        min_value=1,
        max_value=20,
        value=5,
    )

    include_retrieval_output = st.sidebar.checkbox(
        "Show raw retrieval output",
        value=False,
    )

    st.sidebar.divider()

    if st.sidebar.button("Clear chat history", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_response = None
        st.rerun()

    return sql_limit, vector_top_k, include_retrieval_output


def main():
    initialize_session_state()

    sql_limit, vector_top_k, include_retrieval_output = render_sidebar()

    st.title("📦 Hybrid RAG Data Engineering Assistant")
    st.markdown(
        """
        Ask business questions about inventory, sales, suppliers, stockout risk,
        warehouse procedures, and internal policy documents.
        """
    )

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### Chat")

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

                if message["role"] == "assistant" and "sources" in message:
                    with st.expander("Sources", expanded=False):
                        display_sources(message["sources"])

                    if message.get("retrieval_output"):
                        display_retrieval_output(message["retrieval_output"])

        user_question = st.chat_input("Ask a question about inventory, sales, suppliers, or policies...")

    with col2:
        selected_sample_question = add_sample_question_buttons()

    question_to_process = user_question or selected_sample_question

    if question_to_process:
        st.session_state.messages.append(
            {
                "role": "user",
                "content": question_to_process,
            }
        )

        with st.chat_message("user"):
            st.markdown(question_to_process)

        with st.chat_message("assistant"):
            with st.spinner("Retrieving SQL data, document context, and generating answer..."):
                try:
                    response = call_rag_api(
                        question=question_to_process,
                        sql_limit=sql_limit,
                        vector_top_k=vector_top_k,
                        include_retrieval_output=include_retrieval_output,
                    )

                    retrieval_mode = response["retrieval_mode"]
                    answer = response["answer"]
                    sources = response["sources"]
                    retrieval_output = response.get("retrieval_output")

                    st.markdown(f"**Retrieval mode:** `{retrieval_mode}`")
                    st.markdown(answer)

                    with st.expander("Sources", expanded=False):
                        display_sources(sources)

                    if include_retrieval_output:
                        display_retrieval_output(retrieval_output)

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": f"**Retrieval mode:** `{retrieval_mode}`\n\n{answer}",
                            "sources": sources,
                            "retrieval_output": retrieval_output,
                        }
                    )

                    st.session_state.last_response = response

                except requests.exceptions.ConnectionError:
                    error_message = (
                        "Could not connect to the FastAPI backend. "
                        "Make sure it is running at http://127.0.0.1:8000."
                    )
                    st.error(error_message)

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": error_message,
                        }
                    )

                except requests.exceptions.HTTPError as error:
                    error_message = f"API error: {error.response.text}"
                    st.error(error_message)

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": error_message,
                        }
                    )

                except Exception as error:
                    error_message = f"Unexpected error: {str(error)}"
                    st.error(error_message)

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": error_message,
                        }
                    )


if __name__ == "__main__":
    main()