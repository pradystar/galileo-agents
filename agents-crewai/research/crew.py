"""
Customer Support Crew for TechGadgets Inc.

This module defines the multi-agent workflow for handling customer support inquiries.
The crew consists of:
1. Support Agent - First-line support, searches FAQs and troubleshooting guides
2. Escalation Specialist - Handles complex issues, searches policies

Workflow:
    User Query → Support Agent → Escalation Specialist → Final Resolution

Usage:
    cd agents-crewai/research
    PYTHONPATH=../.. uv run python crew.py "My device won't turn on and I want a refund"
"""

import sys

from crewai import Crew, Process, Task
from dotenv import load_dotenv

from agents import create_escalation_specialist, create_support_agent
from prompts import (
    ESCALATION_TASK_DESCRIPTION,
    ESCALATION_TASK_EXPECTED_OUTPUT,
    SUPPORT_TASK_DESCRIPTION,
    SUPPORT_TASK_EXPECTED_OUTPUT,
)
from shared import logger

load_dotenv()


def create_customer_support_crew(query: str) -> Crew:
    """
    Create a Customer Support Crew to handle a customer inquiry.

    Args:
        query: The customer's question or issue

    Returns:
        Configured Crew ready to process the inquiry
    """
    # Create agents
    support_agent = create_support_agent()
    escalation_specialist = create_escalation_specialist()

    # Create tasks
    support_task = Task(
        description=SUPPORT_TASK_DESCRIPTION.format(query=query),
        expected_output=SUPPORT_TASK_EXPECTED_OUTPUT,
        agent=support_agent,
    )

    escalation_task = Task(
        description=ESCALATION_TASK_DESCRIPTION.format(
            query=query, support_response="{support_task.output}"
        ),
        expected_output=ESCALATION_TASK_EXPECTED_OUTPUT,
        agent=escalation_specialist,
        context=[support_task],  # This task depends on support_task
    )

    # Create and return the crew
    crew = Crew(
        agents=[support_agent, escalation_specialist],
        tasks=[support_task, escalation_task],
        process=Process.sequential,  # Tasks run in order
        verbose=True,
    )

    return crew


def run_support_query(query: str) -> str:
    """
    Process a customer support query through the crew.

    Args:
        query: The customer's question or issue

    Returns:
        The crew's final response
    """
    crew = create_customer_support_crew(query)
    result = crew.kickoff()
    return str(result)


def main():
    """Main entry point for running the customer support crew."""
    # Default query if none provided
    default_query = "My device won't turn on and I want a refund"

    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = default_query

    logger.info("=" * 60)
    logger.info("TechGadgets Inc. Customer Support")
    logger.info("=" * 60)
    logger.info(f"Customer Query: {query}")
    logger.info("=" * 60)

    result = run_support_query(query)

    logger.info("=" * 60)
    logger.info("FINAL RESOLUTION")
    logger.info("=" * 60)
    logger.info(result)


if __name__ == "__main__":
    main()
