"""
tests/vybz/client/test_api.py

Unit tests for the Vybz Network Client.
Uses AsyncMock to simulate HTTP and WebSocket interactions.
"""

import json
import pytest
import websockets
from websockets.protocol import State
from unittest.mock import AsyncMock, MagicMock, patch
from vybz.client.api import VybzApiClient, AgentListing, SkillDTO

@pytest.mark.asyncio
class TestVybzApiClient:
    """
    Tests for VybzApiClient focusing on API contract and async streaming.
    """

    @pytest.fixture
    async def client(self):
        """Provides a client instance and ensures it is closed."""
        api_client = VybzApiClient(host="localhost", port=8000)
        yield api_client
        await api_client.close()

    async def test_get_health_success(self, client, mocker):
        """Happy Path: Verify health check parsing."""
        # Arrange
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok", "model": "test-model"}
        mock_response.raise_for_status = MagicMock()

        mocker.patch.object(client._http_client, "get", AsyncMock(return_value=mock_response))

        # Act
        result = await client.get_health()

        # Assert
        assert result["status"] == "ok"
        client._http_client.get.assert_called_once_with("/health")

    async def test_list_agents_success(self, client, mocker):
        """Happy Path: Verify agent listing and Pydantic model hydration."""
        # Arrange
        mock_data = [
            {"id": "junior", "name": "Junior Dev", "description": "Desc A"},
            {"id": "pm", "name": "PM Lead", "description": "Desc B"}
        ]
        mock_response = MagicMock()
        mock_response.json.return_value = mock_data
        mock_response.raise_for_status = MagicMock()

        mocker.patch.object(client._http_client, "get", AsyncMock(return_value=mock_response))

        # Act
        agents = await client.list_agents()

        # Assert
        assert len(agents) == 2
        assert isinstance(agents[0], AgentListing)
        assert agents[0].id == "junior"
        assert agents[1].name == "PM Lead"

    async def test_start_session_success(self, client, mocker):
        """Happy Path: Verify session initialization and ID capture."""
        # Arrange
        mock_response = MagicMock()
        mock_response.json.return_value = {"session_id": "uuid-1234"}
        mock_response.raise_for_status = MagicMock()

        mocker.patch.object(client._http_client, "post", AsyncMock(return_value=mock_response))

        # Act
        sid = await client.start_session("junior", context="# Code")

        # Assert
        assert sid == "uuid-1234"
        assert client.session_id == "uuid-1234"
        client._http_client.post.assert_called_once()
        # Verify payload
        args, kwargs = client._http_client.post.call_args
        assert kwargs["json"] == {"agent_id": "junior", "context": "# Code"}

    async def test_uplevel_skill_success(self, client, mocker):
        """Happy Path: Verify skill transmission."""
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success"}

        mocker.patch.object(client._http_client, "post", AsyncMock(return_value=mock_response))

        skill = SkillDTO(id="s1", name="S1", description="D", instructions="I")

        # Act
        success = await client.uplevel_skill("sid-1", skill)

        # Assert
        assert success is True
        client._http_client.post.assert_called_with(
            "/session/sid-1/skills/uplevel",
            json=skill.model_dump()
        )

    async def test_chat_stream_success(self, client, mocker):
        """
        Happy Path: Verify WebSocket streaming logic.
        Mocks the async context manager and async iterator of the websocket.
        """
        # Arrange
        client.session_id = "active-sess"
        prompt = "Hello"

        # 1. Mock the WebSocket object
        mock_ws = AsyncMock(spec=websockets.WebSocketClientProtocol)
        mock_ws.state = State.OPEN
        # The websocket object is an async iterator
        mock_ws.__aiter__.return_value = ["chunk1", "chunk2", "\x04"]

        with patch("websockets.connect", AsyncMock(return_value=mock_ws)) as mock_connect:
            # First call
            chunks = [c async for c in client.chat_stream("first prompt")]
            assert chunks == ["chunk1", "chunk2"]
            assert mock_connect.call_count == 1

            # Verify JSON was sent
            mock_ws.send.assert_called_with(json.dumps({"content": "first prompt"}))

            # Second call - should reuse the same connection (mock_connect call count remains 1)
            mock_ws.__aiter__.return_value = ["chunk3", "\x04"]
            chunks2 = [c async for c in client.chat_stream("second prompt")]
            assert chunks2 == ["chunk3"]
            assert mock_connect.call_count == 1

            # Final cleanup
            await client.close()
            assert client._ws is None
            mock_ws.close.assert_called_once()

    async def test_chat_stream_no_session_raises_error(self, client):
        """Sad Path: chat_stream should fail if start_session wasn't called."""
        # Arrange
        client.session_id = None

        # Act & Assert
        with pytest.raises(RuntimeError) as exc:
            async for _ in client.chat_stream("hi"):
                pass

        assert "Session not initialized" in str(exc.value)

    async def test_api_error_propagation(self, client, mocker):
        """Sad Path: Verify that HTTP errors (e.g. 500) propagate."""
        # Arrange
        mock_response = MagicMock()
        # Simulate httpx error
        mock_response.raise_for_status.side_effect = Exception("Server Error")

        mocker.patch.object(client._http_client, "get", AsyncMock(return_value=mock_response))

        # Act & Assert
        with pytest.raises(Exception) as exc:
            await client.get_health()

        assert "Server Error" in str(exc.value)
