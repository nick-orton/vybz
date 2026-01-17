"""
session.py

Manages the lifecycle of GenAI Chat Sessions, Agent switching, and Context refreshing.
Decoupled from the UI/REPL loop.
"""

from typing import Dict, Any, Optional
from google import genai
from google.genai import types

from vybz.agent import Agent
from vybz.context_engine import CodeBase
from vybz.squad import Squad
from vybz.services.context import ContextAssembler
from vybz import ui


class SessionManager:
    """
    Controller for multi-agent chat sessions.
    Maintains the state of active conversations and handles context injection.
    """

    def __init__(
        self,
        client: genai.Client,
        model_id: str,
        initial_agent: Agent,
        codebase: Optional[CodeBase] = None
    ):
        self.client = client
        self.model_id = model_id
        self.codebase = codebase

        self.sessions: Dict[str, Any] = {}  # agent_id -> ChatSession
        self.active_agent: Agent = initial_agent
        self.active_chat: Any = None

        # Initialize the first session immediately
        self._activate_session(initial_agent)

    def _activate_session(self, agent: Agent) -> None:
        """Internal method to set active pointers and ensure chat exists."""
        self.active_agent = agent
        if agent.id not in self.sessions:
            self.sessions[agent.id] = self._create_chat(agent)
        self.active_chat = self.sessions[agent.id]

    def _create_chat(self, agent: Agent, history: list = None) -> Any:
        """Creates a new GenAI chat object with current context."""
        sys_instructions = ContextAssembler.build_system_instruction(agent, self.codebase)

        return self.client.chats.create(
            model=self.model_id,
            history=history,
            config=types.GenerateContentConfig(
                system_instruction=sys_instructions,
                temperature=0.7
            )
        )

    def switch_agent(self, agent_name: str) -> Agent:
        """
        Switches the active session to the named agent.
        Raises ValueError if agent not found.
        """
        agent = Squad.get_agent(agent_name)
        self._activate_session(agent)
        return agent

    def refresh_context(self) -> int:
        """
        Reloads CodeBase and Hot-Swaps all active sessions.
        Returns the number of sessions refreshed.
        """
        if self.codebase:
            # Re-snapshot filesystem
            self.codebase = CodeBase(self.codebase.root_path)

        count = 0
        for agent_id, old_chat in list(self.sessions.items()):
            try:
                # Extract history
                try:
                    history = old_chat.get_history()
                except AttributeError:
                    history = getattr(old_chat, "_history", [])

                # Rebuild chat
                agent = Squad.get_agent(agent_id)  # Reload agent def too
                new_chat = self._create_chat(agent, history)
                self.sessions[agent_id] = new_chat
                count += 1
            except Exception as e:
                ui.print_error(f"Failed to refresh session for {agent_id}: {e}")

        # Update active pointer
        if self.active_agent:
            self.active_chat = self.sessions.get(self.active_agent.id)

        return count
