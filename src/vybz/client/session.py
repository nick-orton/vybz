"""
src/vybz/client/session.py

The Client-Side Session Controller.
Manages the lifecycle of the remote connection, local codebase snapshots,
and active agent metadata.
"""

from pathlib import Path
from typing import Optional, AsyncGenerator, List

from vybz.client.api import VybzApiClient, AgentListing
from vybz.client import ui
from vybz.shared.codebase import CodeBase


class ClientSessionManager:
    """
    Orchestrates the interaction between the TUI and the vybzd engine.
    Maintains local state necessary for UI rendering (Active Agent, Context status).
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 8000):
        self.client = VybzApiClient(host=host, port=port)
        self.session_id: Optional[str] = None

        # Local state for UI feedback
        self.active_agent: Optional[AgentListing] = None
        self.codebase: Optional[CodeBase] = None
        self.model_id: str = "unknown"

    async def connect(self) -> bool:
        """
        Verifies connectivity with the vybzd server.

        Returns:
            bool: True if server is healthy.
        """
        try:
            health = await self.client.get_health()
            self.model_id = health.get("model", "unknown")
            return health.get("status") == "ok"
        except Exception as e:
            ui.print_error(f"Could not connect to vybzd: {e}")
            return False

    async def initialize(self, agent_id: str, codebase_root: Optional[Path] = None) -> str:
        """
        Starts a remote session and provides the codebase root path.

        Args:
            agent_id: The ID of the persona to activate.
            codebase_root: Optional local path to provide to the agent tools.

        Returns:
            str: The remote session ID.
        """
        # 1. Resolve Root Path
        path_str = ""
        if codebase_root:
            self.codebase = CodeBase(codebase_root)
            path_str = str(codebase_root.resolve())
            ui.print_system(f"Linking remote session to codebase: {path_str}")

        # 2. Remote Init (Sending path string, not file dump)
        self.session_id = await self.client.start_session(agent_id, path_str)

        # 3. Resolve metadata for UI
        agents = await self.client.list_agents()
        for a in agents:
            if a.id == agent_id:
                self.active_agent = a
                break

        # Fallback if agent not in listing (should not happen)
        if not self.active_agent:
            self.active_agent = AgentListing(id=agent_id, name=agent_id, description="")

        return self.session_id

    async def chat(self, text: str) -> AsyncGenerator[str, None]:
        """
        Streams a prompt to the server and yields response chunks.
        """
        if not self.session_id:
            raise RuntimeError("Session not initialized.")

        async for chunk in self.client.chat_stream(text):
            yield chunk

    async def switch_agent(self, agent_id: str) -> bool:
        """
        Switches the active persona by starting a new remote session.
        Preserves the current codebase context if active.
        """
        try:
            await self.initialize(agent_id, self.codebase.root_path if self.codebase else None)
            ui.print_success(f"Switched to {self.active_agent.name}")
            return True
        except Exception as e:
            ui.print_error(f"Failed to switch agent: {e}")
            return False

    async def close(self):
        """Clean up network resources."""
        await self.client.close()
