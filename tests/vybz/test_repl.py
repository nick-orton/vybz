"""
tests/vybz/test_repl.py

Unit tests for the ReplSession (Presentation Layer).
Verifies Command Parsing and Delegation to SessionManager.
"""
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from vybz.repl import ReplSession
from vybz.agent import Agent
from vybz.context_engine import CodeBase

# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def mock_agent():
    """Returns a mock Agent object."""
    agent = MagicMock(spec=Agent)
    agent.id = "test-agent"
    agent.name = "Test Agent"
    agent.get_identity.return_value = "Test Agent (v1)"
    return agent

@pytest.fixture
def mock_session_manager():
    """Returns a mock SessionManager."""
    sm = MagicMock()
    sm.active_agent.id = "test-agent"
    sm.active_agent.name = "Test Agent"
    sm.model_id = "gemini-test"
    sm.codebase = None
    return sm

@pytest.fixture
def repl(mock_agent, mock_session_manager, tmp_path):
    """
    Returns an initialized ReplSession with dependencies mocked.
    Patches PromptSession and SessionManager.
    """
    with patch("vybz.repl.PromptSession"), \
         patch("vybz.repl.SessionManager", return_value=mock_session_manager):

        session = ReplSession(
            client=MagicMock(),
            agent=mock_agent,
            model_id="gemini-test",
            log_file=tmp_path / "vybz.log"
        )
    return session

# -----------------------------------------------------------------------------
# Initialization Tests
# -----------------------------------------------------------------------------

def test_repl_init_delegates_to_manager(repl, mock_session_manager):
    """Verify ReplSession initializes SessionManager correctly."""
    assert repl.session_manager == mock_session_manager

# -----------------------------------------------------------------------------
# Command Handler Tests
# -----------------------------------------------------------------------------

def test_handle_command_exit(repl):
    """Verify exit commands raise EOFError."""
    with pytest.raises(EOFError):
        repl._handle_command("/exit")

def test_handle_command_clear(repl, mock_session_manager):
    """Verify /clear calls UI clear and re-renders header."""
    with patch("vybz.repl.ui") as mock_ui:
        assert repl._handle_command("/clear") is True
        mock_ui.console.clear.assert_called_once()
        mock_ui.render_session_header.assert_called_once()

def test_handle_command_update(repl, mock_session_manager):
    """Verify /update delegates to SessionManager.refresh_context."""
    # Arrange
    mock_session_manager.refresh_context.return_value = 1

    # Act
    with patch("vybz.repl.ui"):
        assert repl._handle_command("/update") is True

    # Assert
    mock_session_manager.refresh_context.assert_called_once()

def test_handle_command_agent_switch_success(repl, mock_session_manager):
    """Verify /agent <name> delegates to SessionManager.switch_agent."""
    # Arrange
    new_agent = MagicMock(spec=Agent)
    new_agent.get_identity.return_value = "New Agent"
    mock_session_manager.switch_agent.return_value = new_agent

    # Act
    with patch("vybz.repl.ui"):
        assert repl._handle_command("/agent pm") is True

    # Assert
    mock_session_manager.switch_agent.assert_called_with("pm")

def test_handle_command_agent_switch_fail(repl, mock_session_manager):
    """Verify /agent handles ValueError from SessionManager."""
    # Arrange
    mock_session_manager.switch_agent.side_effect = ValueError("Not found")

    # Act
    with patch("vybz.repl.ui") as mock_ui, \
         patch("vybz.repl.Squad") as mock_squad:
        mock_squad.list_agents.return_value = ["a", "b"]

        assert repl._handle_command("/agent ghost") is True # Handled, so returns True

    # Assert
    mock_ui.print_error.assert_called()

# -----------------------------------------------------------------------------
# Input Handler Tests
# -----------------------------------------------------------------------------

def test_handle_input_delegates_to_chat(repl, mock_session_manager):
    """Verify user input is sent to the active chat stream."""
    # Arrange
    mock_chat = MagicMock()
    mock_session_manager.active_chat = mock_chat
    mock_chat.send_message_stream.return_value = [] # Empty stream

    # Act
    with patch("vybz.repl.ui"):
        repl._handle_input("Hello")

    # Assert
    mock_chat.send_message_stream.assert_called_with("Hello")

def test_handle_input_no_active_chat(repl, mock_session_manager):
    """Verify robust handling when no chat is active."""
    # Arrange
    mock_session_manager.active_chat = None

    # Act
    with patch("vybz.repl.ui") as mock_ui:
        repl._handle_input("Hello")

    # Assert
    mock_ui.print_error.assert_called_with("No active chat session.")
