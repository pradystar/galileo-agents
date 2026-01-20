"""RAG Agent - Q&A over documents with vector search."""
import os
import sys

from dotenv import load_dotenv

load_dotenv()

# IMPORTANT: Initialize Traceloop BEFORE importing langchain libraries
# LangChain may set up its own TracerProvider during import, which would override
# our resource_attributes if we initialize Traceloop after the import.
from traceloop.sdk import Traceloop

Traceloop.init(
    app_name="rag-agent",
    resource_attributes={
        "galileo.project.name": "galileo-agents",
        "galileo.logstream.name": "rag-agent",
    },
    disable_batch=True,
)

# Now import langchain after Traceloop is initialized
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from opentelemetry import trace
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

from prompt import RAG_AGENT_SYSTEM_PROMPT, SAMPLE_DOCUMENTS
from shared import logger
from tools import create_knowledge_base, search_documents

# Add console exporter for debugging if enabled
if os.getenv("TRACELOOP_CONSOLE_EXPORTER_ENABLED", "false").lower() == "true":
    tracer_provider = trace.get_tracer_provider()
    if hasattr(tracer_provider, "add_span_processor"):
        console_processor = BatchSpanProcessor(ConsoleSpanExporter())
        tracer_provider.add_span_processor(console_processor)

# Knowledge base setup
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
_, retriever = create_knowledge_base(SAMPLE_DOCUMENTS, embeddings)


@tool
def retrieve_documents(query: str) -> str:
    """Search the knowledge base for relevant documents about RAG, embeddings, and vector search."""
    _, formatted_result = search_documents(query, retriever)
    return formatted_result


def create_rag_agent():
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    return create_agent(llm, [retrieve_documents], system_prompt=RAG_AGENT_SYSTEM_PROMPT)


def main(query: str = "What is RAG and how does it work?"):
    logger.info(f"RAG Agent - Query: {query}")
    agent = create_rag_agent()
    result = agent.invoke({"messages": [("user", query)]})
    response = result["messages"][-1].content
    logger.info(f"Response: {response}")
    return response


if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What is RAG and how does it work?"
    main(query)
