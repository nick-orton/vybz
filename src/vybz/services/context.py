"""
context.py

Responsible for assembling the System Instructions (Context) for LLM interactions.
Centralizes the logic for combining Persona, Time, and Codebase.
"""

import datetime
from typing import Dict, Optional
from vybz.shared.agent import Agent
from vybz.shared.codebase import CodeBase


class ContextAssembler:
    """
    Stateless builder for system prompts.
    """

    @staticmethod
    def build_system_instruction(
        agent: Agent, 
        codebase_root: str | None = None,
        manual_context: Dict[str, str] | None = None
    ) -> str:
        """
        Constructs the full system prompt.

        Args:
            agent: The active Agent persona.
            codebase_root: The optional absolute path to the project root.
            manual_context: Dictionary of {filename: content} for manually loaded files.

        Returns:
            str: The fully formatted system instruction.
        """
        # 1. Base Agent Role & Skills
        sys_instructions = agent.construct_agent_role_profile()

        # 2. Date Knowledge
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        sys_instructions += f"\n\n### SYSTEM METADATA\nCurrent Date: {current_date}\n"

        # 3. Agentic RAG Instructions
        if codebase_root:
            sys_instructions += (
                f"\n\n### FILESYSTEM ACCESS\n"
                f"You have access to the filesystem at: `{codebase_root}`\n"
                f"Use `list_files` to explore the directory structure and `read_file` to examine code.\n"
                f"Do not hallucinate file contents; always read them if you are unsure.\n"
            )

        # 4. Manual Context Injection
        if manual_context:
            sys_instructions += "\n\n### MANUAL CONTEXT\n"
            for filename, content in manual_context.items():
                sys_instructions += f"#### File: {filename}\n```\n{content}\n```\n"

        return sys_instructions
