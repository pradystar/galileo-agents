"""Weather Agent - Answers weather questions using tools."""

import sys

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from prompt import WEATHER_AGENT_SYSTEM_PROMPT
from tools import get_current_weather, get_forecast

from shared import logger

load_dotenv()


@tool
def weather_tool(city: str) -> str:
    """Get current weather for a city."""
    result = get_current_weather(city)
    return f"Weather in {result['city']}: {result['temperature_f']}F, {result['conditions']}, {result['humidity']}% humidity"


@tool
def forecast_tool(city: str, days: int = 3) -> str:
    """Get multi-day weather forecast for a city."""
    result = get_forecast(city, days)
    lines = [f"Forecast for {result['city']}:"]
    for day in result["forecast"]:
        lines.append(f"  Day {day['day']}: High {day['high_f']}F, Low {day['low_f']}F, {day['conditions']}")
    return "\n".join(lines)


def create_weather_agent():
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    return create_agent(llm, [weather_tool, forecast_tool], system_prompt=WEATHER_AGENT_SYSTEM_PROMPT)


def main(query: str = "What's the weather like in San Francisco?"):
    logger.info(f"Weather Agent - Query: {query}")
    agent = create_weather_agent()
    result = agent.invoke({"messages": [("user", query)]})
    response = result["messages"][-1].content
    logger.info(f"Response: {response}")
    return response


if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What's the weather like in San Francisco?"
    main(query)
