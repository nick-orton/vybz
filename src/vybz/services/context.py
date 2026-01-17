"""
context.py

Responsible for assembling the System Instructions (Context) for LLM interactions.
Centralizes the logic for combining Persona, Time, and Codebase.
"""

import datetime
from vybz.agent import Agent
from vybz.context_engine import CodeBase


class ContextAssembler:
    """
    Stateless builder for system prompts.
    """

    @staticmethod
    def build_system_instruction(agent: Agent, codebase: CodeBase | None) -> str:
        """
        Constructs the full system prompt.

        Args:
            agent: The active Agent persona.
            codebase: The optional filesystem snapshot.

        Returns:
            str: The fully formatted system instruction.
        """
        # 1. Base Agent Role & Skills
        sys_instructions = agent.construct_agent_role_profile()

        # 2. Date Knowledge
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        sys_instructions += f"\n\n### SYSTEM METADATA\nCurrent Date: {current_date}\n"

        # 3. CodeBase Injection
        if codebase:
            sys_instructions += "\n\n" + codebase.render()

        return sys_instructions
