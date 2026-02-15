"""
src/vybz/client/api.py

The Vybz Network Client.
Wraps httpx and websockets to provide a clean interface for the CLI to 
interact with the vybzd engine.
"""

import json
import asyncio
from typing import List, Optional, AsyncGenerator, Dict, Any
from pathlib import Path

import httpx
import websockets
from pydantic import BaseModel

class AgentListing(BaseModel):
    """Metadata for an agent persona."""
    id: str
    name: str
    description: str

class SkillDTO(BaseModel):
    """Data transfer object for agent skills."""
    id: str
    name: str
    description: str
    instructions: str

class FileLoadDTO(BaseModel):
    """Data transfer object for surgical context injection."""
    filename: str
    content: str

class VybzApiClient:
    """
    Async client for the vybzd engine.
    Handles session lifecycle, state mutation, and real-time chat streaming.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 8000):
        self.base_url = f"http://{host}:{port}"
        self.ws_url = f"ws://{host}:{port}"
        self.session_id: Optional[str] = None
        self._http_client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)

    async def close(self) -> None:
        """Closes the underlying HTTP client."""
        await self._http_client.aclose()

    async def get_health(self) -> Dict[str, Any]:
        """Checks server health and returns metadata."""
        try:
            response = await self._http_client.get("/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise ConnectionError(f"Engine unreachable at {self.base_url}: {e}")

    async def list_agents(self) -> List[AgentListing]:
        """Retrieves the list of available agents from the engine."""
        response = await self._http_client.get("/agents")
        response.raise_for_status()
        return [AgentListing(**a) for a in response.json()]

    async def start_session(self, agent_id: str, context: str = "") -> str:
        """
        Initializes a session on the server.
        
        Args:
            agent_id: The ID of the agent to chat with.
            context: The absolute root path of the codebase.
            
        Returns:
            str: The session UUID.
        """
        payload = {"agent_id": agent_id, "context": context}
        response = await self._http_client.post("/session/init", json=payload)
        response.raise_for_status()
        
        data = response.json()
        self.session_id = data["session_id"]
        return self.session_id

    # -------------------------------------------------------------------------
    # Session Mutation Methods (Phase 3)
    # -------------------------------------------------------------------------

    async def list_session_skills(self, session_id: str) -> List[SkillDTO]:
        """Retrieves the list of active skills for a specific session."""
        response = await self._http_client.get(f"/session/{session_id}/skills")
        response.raise_for_status()
        return [SkillDTO(**s) for s in response.json()]

    async def uplevel_skill(self, session_id: str, skill_data: SkillDTO) -> bool:
        """
        Uploads and injects a local skill into the remote session.
        Returns True if successful.
        """
        response = await self._http_client.post(
            f"/session/{session_id}/skills/uplevel",
            json=skill_data.model_dump()
        )
        response.raise_for_status()
        return response.json().get("status") == "success"

    async def downlevel_skill(self, session_id: str, skill_id: str) -> bool:
        """
        Requests the removal of a skill from the remote session.
        Returns True if successful.
        """
        response = await self._http_client.post(
            f"/session/{session_id}/skills/downlevel",
            json={"skill_id": skill_id}
        )
        response.raise_for_status()
        return response.json().get("status") == "success"

    async def load_file_content(self, session_id: str, filename: str, content: str) -> bool:
        """
        Surgically injects raw file content into the remote session context.
        Returns True if successful.
        """
        payload = FileLoadDTO(filename=filename, content=content)
        response = await self._http_client.post(
            f"/session/{session_id}/load",
            json=payload.model_dump()
        )
        response.raise_for_status()
        return response.json().get("status") == "success"

    # -------------------------------------------------------------------------
    # Streaming
    # -------------------------------------------------------------------------

    async def chat_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        """
        Connects to the session WebSocket and streams chunks of the response.
        
        Args:
            prompt: The user input string.
            
        Yields:
            str: Text chunks as they arrive from the engine.
        """
        if not self.session_id:
            raise RuntimeError("Session not initialized. Call start_session first.")

        uri = f"{self.ws_url}/session/{self.session_id}/chat"
        
        async with websockets.connect(uri) as ws:
            # 1. Send the prompt
            await ws.send(json.dumps({"content": prompt}))
            
            # 2. Consume the stream
            try:
                async for message in ws:
                    yield str(message)
            except websockets.ConnectionClosed:
                pass
