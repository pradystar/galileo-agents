"""RAG Agent - Q&A over documents with vector search."""
import sys

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from prompt import RAG_AGENT_SYSTEM_PROMPT, SAMPLE_DOCUMENTS
from shared import logger
from tools import create_knowledge_base, search_documents

load_dotenv()

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
