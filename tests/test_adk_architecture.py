import asyncio
import sys
from unittest.mock import MagicMock, patch, AsyncMock

# Mock dependencies before import
sys.modules["google.adk"] = MagicMock()
sys.modules["google.adk.sessions"] = MagicMock()
sys.modules["google.genai"] = MagicMock()

def test_runner_architecture():
    """
    Verifies that creating a session sets up the correct Runner/Agent structure.
    """
    from vybz.server.state import ServerState

    # Setup
    state = ServerState()
    state.library = MagicMock()
    state.hydrator = MagicMock()
    state.session_service = AsyncMock()
    state._refresh_session_instructions = AsyncMock()

    # Mock templates
    mock_vybz_agent = MagicMock()
    state.agent_templates = {"junior": mock_vybz_agent}
    state.library.get_agent_path.return_value = "path"

    # Mock hydration return
    mock_adk_agent = MagicMock()
    state.hydrator.hydrate_agent.return_value = mock_adk_agent

    # Mock session creation
    mock_session = MagicMock()
    mock_session.id = "sess-1"
    mock_session.state = {}
    state.session_service.create_session.return_value = mock_session

    with patch("vybz.server.state.VybzAgent.from_toml", return_value=mock_vybz_agent), \
         patch("vybz.server.state.FileSystemTools"), \
         patch("vybz.server.state.Runner") as MockRunner:

        # Execute
        sid = asyncio.run(state.create_session("junior", "# Context"))

        # Verify
        # 1. Runner created with specific agent instance
        MockRunner.assert_called_with(
            agent=mock_adk_agent,
            app_name=state.app_name,
            session_service=state.session_service
        )

        # 2. Runner stored
        assert sid in state.runners

        # 3. Instruction updated
        assert mock_adk_agent.instruction is not None
        print("[SUCCESS] Runner/Agent Architecture verified.")

if __name__ == "__main__":
    test_runner_architecture()
