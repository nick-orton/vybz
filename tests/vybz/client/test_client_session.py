import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
from vybz.client.session import ClientSessionManager
from vybz.client.api import AgentListing

@pytest.mark.asyncio
async def test_client_session_init_flow():
    """
    Verify that initialize() correctly snapshots the codebase and 
    communicates with the API client.
    """
    manager = ClientSessionManager()
    
    # Mock API Client
    mock_client = AsyncMock()
    mock_client.start_session.return_value = "session-uuid-123"
    mock_client.list_agents.return_value = [
        AgentListing(id="junior-dev", name="Junior", description="...")
    ]
    manager.client = mock_client

    # Mock CodeBase to avoid actual disk walk
    with patch("vybz.client.session.CodeBase") as MockCB:
        MockCB.return_value.render.return_value = "# CodeBase Data"
        MockCB.return_value.root_path = Path("/tmp")

        # Act
        sid = await manager.initialize("junior-dev", Path("/tmp"))

        # Assert
        assert sid == "session-uuid-123"
        assert manager.active_agent.name == "Junior"
        assert manager.codebase is not None
        
        # Verify API was called with the rendered context
        mock_client.start_session.assert_called_with("junior-dev", "# CodeBase Data")

if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(test_client_session_init_flow())
        print("[SUCCESS] ClientSessionManager logic verified.")
    except Exception as e:
        print(f"[FAIL] {e}")
