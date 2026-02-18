"""Content Crew - Writer and Editor agents for blog post creation."""
import sys

from crewai import Crew, LLM, Task
from dotenv import load_dotenv

from agents import create_editor_agent, create_writer_agent
from shared import logger

load_dotenv()


def create_crew(topic: str):
    llm = LLM(model="gpt-4o-mini", temperature=0.7)
    writer = create_writer_agent(llm)
    editor = create_editor_agent(llm)

    write_task = Task(
        description=f"Write a draft blog post about: {topic}",
        expected_output="A complete draft blog post with introduction, main points, and conclusion.",
        agent=writer,
    )
    edit_task = Task(
        description="Review and improve the draft blog post. Focus on clarity, engagement, and flow.",
        expected_output="A polished, publication-ready blog post.",
        agent=editor,
        context=[write_task],
    )

    return Crew(agents=[writer, editor], tasks=[write_task, edit_task], verbose=True)


def main(topic: str = "The Future of AI Agents"):
    logger.info(f"Content Crew - Topic: {topic}")
    crew = create_crew(topic)
    result = crew.kickoff()
    logger.info(f"Result: {result}")
    return result


if __name__ == "__main__":
    topic = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "The Future of AI Agents"
    main(topic)
