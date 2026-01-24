"""
tests/vybz/test_repl.py

Unit tests for the ReplSession (Presentation Layer).
Verifies Command Dispatching, TUI State Rendering, and Input Delegation.
"""
import pytest
from unittest.mock import MagicMock, patch, ANY
from pathlib import Path
from prompt_toolkit.enums import EditingMode

from vybz.repl import ReplSession
from vybz.agent import Agent
from vybz.context_engine import CodeBase

# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def mock_agent():
    """Returns a mock Agent object with necessary attributes."""
    agent = MagicMock(spec=Agent)
    agent.id = "test-agent"
    agent.name = "Test Agent"
    agent.get_identity.return_value = "Test Agent (v1)"
    return agent

@pytest.fixture
def mock_session_manager(mock_agent):
    """Returns a mock SessionManager with a controlled state."""
    sm = MagicMock()
    sm.active_agent = mock_agent
    sm.active_chat = MagicMock()
    sm.model_id = "gemini-test"
    sm.codebase = None
    return sm

@pytest.fixture
def repl(mock_session_manager, tmp_path):
    """
    Returns an initialized ReplSession with dependencies mocked.
    We patch PromptSession and CommandRegistry to isolate the REPL loop logic.
    """
    with patch("vybz.repl.PromptSession"), \
         patch("vybz.repl.CommandRegistry") as MockRegistry, \
         patch("vybz.repl.ui"): # Silence UI side effects during init

        session = ReplSession(
            mock_session_manager,
            log_file=tmp_path / "vybz.log",
            mode="vi"
        )
        # Expose the mock registry instance for tests to configure
        session.registry = MockRegistry.return_value

    return session

# -----------------------------------------------------------------------------
# Initialization & State Tests
# -----------------------------------------------------------------------------

def test_repl_init_state(repl, mock_session_manager):
    """Verify ReplSession initializes with correct defaults and delegates."""
    assert repl.session_manager == mock_session_manager
    # Registry should be initialized
    repl.registry.initialize.assert_called_once()

def test_get_prompt_tokens(repl, mock_session_manager):
    """Verify the left prompt reflects the active agent ID."""
    # Arrange
    mock_session_manager.active_agent.id = "junior-dev"

    # Act
    tokens = repl._get_prompt_tokens()

    # Assert
    # Format: [('class:agent', 'junior-dev '), ('class:separator', '❯ ')]
    assert tokens[0] == ("class:agent", "junior-dev ")
    assert tokens[1] == ("class:separator", "❯ ")

def test_get_prompt_tokens_fallback(repl, mock_session_manager):
    """Verify prompt fallback if no agent is active."""
    # Arrange
    mock_session_manager.active_agent = None

    # Act
    tokens = repl._get_prompt_tokens()

    # Assert
    assert tokens[0] == ("class:agent", "vybz ")

def test_get_rprompt_tokens(repl, mock_session_manager):
    """Verify right prompt reflects Input Mode and Context status."""
    # Arrange
    repl.session.editing_mode = EditingMode.VI
    mock_session_manager.codebase = MagicMock(spec=CodeBase) # Context Active

    # Act
    tokens = repl._get_rprompt_tokens()

    # Assert
    # Format: [('class:meta', 'VI | CTX')]
    assert tokens[0] == ("class:meta", "VI | CTX")

def test_get_rprompt_tokens_no_context(repl, mock_session_manager):
    """Verify right prompt reflects 'NO-CTX' when codebase is None."""
    # Arrange
    repl.session.editing_mode = EditingMode.EMACS
    mock_session_manager.codebase = None

    # Act
    tokens = repl._get_rprompt_tokens()

    # Assert
    assert tokens[0] == ("class:meta", "EMACS | NO-CTX")

# -----------------------------------------------------------------------------
# Command Dispatching Tests (The Command Pattern)
# -----------------------------------------------------------------------------

def test_handle_command_dispatches_to_registry(repl):
    """
    Verify _handle_command looks up the command in registry and executes it.
    """
    # Arrange
    mock_cmd = MagicMock()
    mock_cmd.execute.return_value = True
    repl.registry.get_command.return_value = mock_cmd

    # Act
    result = repl._handle_command("/test arg1")

    # Assert
    repl.registry.get_command.assert_called_with("/test")
    mock_cmd.execute.assert_called_with(repl, ["arg1"])
    assert result is True

def test_handle_command_unknown(repl):
    """Verify handling of unknown slash commands."""
    # Arrange
    repl.registry.get_command.return_value = None

    with patch("vybz.repl.ui") as mock_ui:
        # Act
        result = repl._handle_command("/unknown")

        # Assert
        mock_ui.print_error.assert_called_with("Unknown command '/unknown'. Type /help for list.")
        assert result is True # Should continue loop, not crash

def test_handle_command_not_a_command(repl):
    """Verify normal text input is ignored by command handler."""
    # Act
    result = repl._handle_command("just some text")

    # Assert
    assert result is False

# -----------------------------------------------------------------------------
# Input Handling Tests
# -----------------------------------------------------------------------------

def test_handle_input_delegates_to_stream(repl, mock_session_manager):
    """Verify user input is sent to the active chat stream and logged."""
    # Arrange
    mock_chat = mock_session_manager.active_chat
    mock_chat.send_message_stream.return_value = [
        MagicMock(text="Chunk 1"),
        MagicMock(text="Chunk 2")
    ]

    with patch("vybz.repl.ui") as mock_ui:
        # Act
        repl._handle_input("Hello World")

        # Assert
        mock_chat.send_message_stream.assert_called_with("Hello World")
        # Verify streaming to UI
        mock_ui.stream_chunk.assert_any_call("Chunk 1")
        mock_ui.stream_chunk.assert_any_call("Chunk 2")
        # Verify auto-save state capture
        assert repl.last_response == "Chunk 1Chunk 2"

def test_handle_input_no_active_chat(repl, mock_session_manager):
    """Verify robust handling when no chat is active (e.g. init failure)."""
    # Arrange
    mock_session_manager.active_chat = None

    with patch("vybz.repl.ui") as mock_ui:
        # Act
        repl._handle_input("Hello")

        # Assert
        mock_ui.print_error.assert_called_with("No active chat session.")

def test_handle_input_api_error(repl, mock_session_manager):
    """Verify API errors are caught and logged without crashing REPL."""
    # Arrange
    mock_chat = mock_session_manager.active_chat
    mock_chat.send_message_stream.side_effect = Exception("API 500")

    with patch("vybz.repl.ui") as mock_ui:
        # Act
        repl._handle_input("Crash me")

        # Assert
        mock_ui.print_error.assert_called()
        assert "API 500" in str(mock_ui.print_error.call_args)
