"""
Customer Support Agents for TechGadgets Inc.

This module defines the Support Agent and Escalation Specialist agents
that work together to handle customer inquiries.
"""

from crewai import Agent

from prompts import (
    ESCALATION_SPECIALIST_BACKSTORY,
    ESCALATION_SPECIALIST_GOAL,
    ESCALATION_SPECIALIST_ROLE,
    SUPPORT_AGENT_BACKSTORY,
    SUPPORT_AGENT_GOAL,
    SUPPORT_AGENT_ROLE,
)
from tools import search_faqs, search_policies, search_troubleshooting


def create_support_agent(llm: str = "gpt-4o-mini") -> Agent:
    """
    Create the first-line Support Agent.

    This agent handles initial customer inquiries by searching FAQs
    and troubleshooting guides.

    Args:
        llm: The language model to use (default: gpt-4o-mini)

    Returns:
        Configured Support Agent
    """
    return Agent(
        role=SUPPORT_AGENT_ROLE,
        goal=SUPPORT_AGENT_GOAL,
        backstory=SUPPORT_AGENT_BACKSTORY,
        tools=[search_faqs, search_troubleshooting],
        llm=llm,
        verbose=True,
    )


def create_escalation_specialist(llm: str = "gpt-4o-mini") -> Agent:
    """
    Create the Escalation Specialist agent.

    This agent handles complex issues by searching policies and
    creating comprehensive escalation summaries.

    Args:
        llm: The language model to use (default: gpt-4o-mini)

    Returns:
        Configured Escalation Specialist Agent
    """
    return Agent(
        role=ESCALATION_SPECIALIST_ROLE,
        goal=ESCALATION_SPECIALIST_GOAL,
        backstory=ESCALATION_SPECIALIST_BACKSTORY,
        tools=[search_policies],
        llm=llm,
        verbose=True,
    )
