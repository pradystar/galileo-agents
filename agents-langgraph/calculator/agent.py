"""Calculator Agent - Two-level graph: outer workflow wraps inner agent."""
import sys
from typing import Annotated

from dotenv import load_dotenv

load_dotenv()  # must be before setup_telemetry so env vars are available

from langchain.agents import create_agent
from langchain_core.messages import AnyMessage, HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from prompt import CALCULATOR_AGENT_SYSTEM_PROMPT
from shared import logger
from shared.telemetry import setup_telemetry
from tools import calculate, convert_units

setup_telemetry()


@tool
def calc_tool(expression: str) -> str:
    """Evaluate a mathematical expression."""
    result = calculate(expression)
    if result["success"]:
        return f"{result['expression']} = {result['result']}"
    return f"Error: {result['error']}"


@tool
def convert_tool(value: float, from_unit: str, to_unit: str) -> str:
    """Convert a value between units."""
    result = convert_units(value, from_unit, to_unit)
    if result["success"]:
        return f"{result['original']} = {result['converted']}"
    return f"Error: {result['error']}"


def create_calculator_agent():
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    return create_agent(llm, [calc_tool, convert_tool], system_prompt=CALCULATOR_AGENT_SYSTEM_PROMPT, name="calculator")


class WorkflowState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


def create_workflow():
    """Create outer workflow graph that wraps the calculator agent as a subgraph."""
    agent = create_calculator_agent()

    def run_agent(state: WorkflowState) -> WorkflowState:
        result = agent.invoke(
            {"messages": state["messages"]},
            config={"tags": ["agent:calculator"]},
        )
        return {"messages": result["messages"]}

    workflow = StateGraph(WorkflowState)
    workflow.add_node("calculator_agent", run_agent)
    workflow.add_edge(START, "calculator_agent")
    workflow.add_edge("calculator_agent", END)
    return workflow.compile()


def main(query: str = "Convert 100 km to mi"):
    logger.info(f"Calculator Agent - Query: {query}")
    workflow = create_workflow()
    result = workflow.invoke(
        {"messages": [HumanMessage(content=query)]},
        config={"metadata": {"session.id": "session-collector-1"}},
    )
    response = result["messages"][-1].content
    logger.info(f"Response: {response}")
    return response


if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Convert 100 km to mi"
    main(query)
