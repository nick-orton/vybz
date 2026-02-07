"""
src/vybz/client/session.py

The Client-Side Session Controller.
Manages the lifecycle of the remote connection, local codebase snapshots,
and active agent metadata.
"""

from pathlib import Path
from typing import Optional, AsyncGenerator, List

from vybz.client.api import VybzApiClient, AgentListing
from vybz.shared.codebase import CodeBase
from vybz import ui


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
        Starts a remote session and snapshots the local codebase.
        
        Args:
            agent_id: The ID of the persona to activate.
            codebase_root: Optional local path to snapshot.
            
        Returns:
            str: The remote session ID.
        """
        # 1. Local Snapshot
        context_str = ""
        if codebase_root:
            ui.print_system(f"Snapshotting codebase at: {codebase_root.resolve()}")
            self.codebase = CodeBase(codebase_root)
            context_str = self.codebase.render()

        # 2. Remote Init
        self.session_id = await self.client.start_session(agent_id, context_str)

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

    async def refresh_context(self) -> bool:
        """
        Re-snapshots the local filesystem and uploads it to the remote session.
        """
        if not self.codebase or not self.session_id:
            ui.print_warning("No codebase loaded to refresh.")
            return False

        ui.print_system("Refreshing local CodeBase snapshot...")
        # Re-instantiate to walk the disk again
        self.codebase = CodeBase(self.codebase.root_path)
        context_str = self.codebase.render()

        success = await self.client.update_context(self.session_id, context_str)
        if success:
            ui.print_success("Remote context updated.")
        return success

    async def switch_agent(self, agent_id: str) -> bool:
        """
        Switches the active persona by starting a new remote session.
        Preserves the current codebase context if active.
        """
        context_str = self.codebase.render() if self.codebase else ""
        
        try:
            # Note: Switching agents in the current ADK implementation creates a 
            # new session ID.
            await self.initialize(agent_id, self.codebase.root_path if self.codebase else None)
            ui.print_success(f"Switched to {self.active_agent.name}")
            return True
        except Exception as e:
            ui.print_error(f"Failed to switch agent: {e}")
            return False

    async def close(self):
        """Clean up network resources."""
        await self.client.close()

