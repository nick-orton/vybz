import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

# Mock dependencies
import sys
sys.modules["google.adk"] = MagicMock()
sys.modules["google.adk.sessions"] = MagicMock()
sys.modules["google.genai"] = MagicMock()

from vybz.server.state import ServerState

@pytest.mark.asyncio
async def test_server_context_update():
    # Arrange
    state = ServerState()
    state.session_service = MagicMock()

    # Mock session data
    mock_session = MagicMock()
    mock_session.state = {"codebase_context": "OLD", "vybz_agent": MagicMock()}
    mock_session.agent = MagicMock() # The ADK agent

    state.session_service.get_session = AsyncMock(return_value=mock_session)

    mock_runner = MagicMock()
    mock_runner.agent = mock_session.agent
    state.get_runner = MagicMock(return_value=mock_runner)


    # Mock the assembler to verify prompt rebuilding
    with patch("vybz.server.state.ContextAssembler.build_system_instruction", return_value="PROMPT"):

        # Act
        await state.update_session_codebase("sess-1", "NEW_CONTEXT")

        # Assert
        # 1. State updated?
        assert mock_session.state["codebase_context"] == "NEW_CONTEXT"

        # 2. Agent instruction updated?
        # The logic appends context to the prompt
        assert mock_session.agent.instruction == "PROMPT\n\nNEW_CONTEXT"
        print("[SUCCESS] Server state accepted context update.")

if __name__ == "__main__":
    asyncio.run(test_server_context_update())
