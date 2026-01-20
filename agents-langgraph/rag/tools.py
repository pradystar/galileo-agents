"""RAG tools with instrumented retrieval."""
import json

from langchain_core.documents import Document
from opentelemetry import trace


def create_knowledge_base(documents: list[dict], embeddings) -> tuple:
    """Create an in-memory vector store from documents."""
    from langchain_community.vectorstores import FAISS

    docs = [
        Document(page_content=doc["content"], metadata={"id": doc["id"], "title": doc["title"]})
        for doc in documents
    ]
    vector_store = FAISS.from_documents(docs, embeddings)
    retriever = vector_store.as_retriever(search_kwargs={"k": 3})
    return vector_store, retriever


def format_docs(docs: list[Document]) -> str:
    """Format retrieved documents for display."""
    return "\n\n".join(
        f"[{i}] {doc.metadata.get('title', 'Unknown')}:\n{doc.page_content}"
        for i, doc in enumerate(docs, 1)
    )


def search_documents(query: str, retriever) -> tuple[list[Document], str]:
    """Search documents with instrumented retrieval span.

    Creates an OTEL span with attributes compatible with Galileo's otel_v2 processor:
    - db.operation: "query" (identifies as retriever span)
    - gen_ai.input.messages: query as message list
    - gen_ai.output.messages: retrieved chunks as message list

    Returns:
        Tuple of (raw documents, formatted string for agent)
    """
    tracer = trace.get_tracer(__name__)

    with tracer.start_as_current_span("document_retrieval") as span:
        # Set db.operation to identify as retriever span
        span.set_attribute("db.operation", "query")

        # Set input as gen_ai.input.messages format
        input_messages = [{"role": "user", "content": query}]
        span.set_attribute("gen_ai.input.messages", json.dumps(input_messages))

        # Perform the actual retrieval
        docs = retriever.invoke(query)

        if not docs:
            # Empty retrieval result - must be a list for RETRIEVER spans
            output_messages = [{"role": "assistant", "content": []}]
            span.set_attribute("gen_ai.output.messages", json.dumps(output_messages))
            return [], "No relevant documents found."

        # Format retrieved documents with 'content' field (required for RETRIEVER spans)
        # and metadata containing id/title
        documents_list = [
            {
                "content": doc.page_content,
                "metadata": {
                    "id": doc.metadata.get("id", ""),
                    "title": doc.metadata.get("title", ""),
                },
            }
            for doc in docs
        ]

        # Set output as gen_ai.output.messages with documents as content list
        output_messages = [{"role": "assistant", "content": documents_list}]
        span.set_attribute("gen_ai.output.messages", json.dumps(output_messages))

        # Return both raw docs and formatted string
        return docs, format_docs(docs)
