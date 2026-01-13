"""
test_repl_update_bug.py

Reproduction of the session loss bug during context refresh.
"""
import pytest
from unittest.mock import MagicMock, patch
from vybz.repl import ReplSession
from vybz.agent import Agent

def test_refresh_context_preserves_active_chat_with_mismatched_id_name(mock_genai_client):
    """
    Bug Reproduction:
    _refresh_context uses active_agent.name instead of active_agent.id
    to restore the active_chat pointer. This causes active_chat to become
    None if name != id.
    """
    # 1. Arrange
    # Create an agent where ID and Name are explicitly different
    agent_id = "test-agent-id"
    agent_name = "Test Agent Name"

    mock_agent = Agent(
        id=agent_id,
        name=agent_name,
        version="1",
        role_spec="role",
        operating_context="context",
        task_directive="task"
    )

    # Mock Squad to return our agent when requested during rebuild
    with patch("vybz.repl.Squad") as mock_squad:
        mock_squad.get_agent.return_value = mock_agent

        # Initialize Session
        repl = ReplSession(
            client=mock_genai_client,
            agent=mock_agent,
            model_id="gemini-3-pro-preview"
        )

        # Verify initial state (Pre-Update)
        assert repl.active_agent.id == agent_id
        assert repl.active_chat is not None
        assert agent_id in repl.sessions
        # Ensure the session is keyed by ID
        assert repl.sessions[agent_id] == repl.active_chat

        # 2. Act
        # Trigger the /update logic
        repl._refresh_context()

        # 3. Assert
        # This assertion fails in the buggy implementation because
        # repl.active_chat becomes None
        assert repl.active_chat is not None, "active_chat was lost (set to None) after /update"

        # Verify it points to the correct session object
        assert repl.active_chat == repl.sessions[agent_id]
