"""
tests/vybz/commands/test_core.py

Unit tests for individual Command implementations.
Verifies that commands correctly manipulate the ReplSession and SessionManager.
"""
import pytest
from unittest.mock import MagicMock, patch, ANY
from pathlib import Path

from vybz.repl import ReplSession
from vybz.agent import Agent
from vybz.commands.core import (
    ExitCommand,
    ClearCommand,
    UpdateCommand,
    HelpCommand,
    AgentCommand,
    SaveCommand,
    SetModeCommand,
    ThemeCommand
)
from prompt_toolkit.enums import EditingMode

# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def mock_session():
    """Returns a mock ReplSession with necessary attributes."""
    session = MagicMock(spec=ReplSession)
    session.session_manager = MagicMock()
    session.session = MagicMock() # PromptSession
    session.last_response = None

    return session

# -----------------------------------------------------------------------------
# System Commands
# -----------------------------------------------------------------------------

def test_exit_command(mock_session):
    cmd = ExitCommand()
    with pytest.raises(EOFError):
        cmd.execute(mock_session, [])

def test_clear_command(mock_session):
    cmd = ClearCommand()
    with patch("vybz.commands.core.ui") as mock_ui:
        assert cmd.execute(mock_session, []) is True
        mock_ui.console.clear.assert_called_once()
        mock_ui.render_session_header.assert_called_once()

def test_update_command(mock_session):
    cmd = UpdateCommand()
    mock_session.session_manager.refresh_context.return_value = 5

    with patch("vybz.commands.core.ui") as mock_ui:
        assert cmd.execute(mock_session, []) is True
        mock_ui.print_success.assert_called()
        mock_session.session_manager.refresh_context.assert_called_once()

def test_help_command(mock_session):
    cmd = HelpCommand()
    with patch("vybz.commands.core.AssetLoader") as mock_loader, \
         patch("vybz.commands.core.ui") as mock_ui:

        mock_loader.load_text.return_value = "Help Content"

        assert cmd.execute(mock_session, []) is True
        mock_loader.load_text.assert_called_with("repl_help.txt")
        mock_ui.print_panel.assert_called_with("Help Content", title="Help Menu")

# -----------------------------------------------------------------------------
# Agent Command
# -----------------------------------------------------------------------------

def test_agent_command_list(mock_session):
    """Verify /agent without args lists available agents."""
    cmd = AgentCommand()
    with patch("vybz.commands.core.Squad") as mock_squad, \
         patch("vybz.commands.core.ui") as mock_ui, \
         patch("vybz.commands.core.AssetLoader") as mock_loader:

        mock_squad.list_agents.return_value = ["pm", "dev"]
        mock_loader.load_text.return_value = "Template"

        assert cmd.execute(mock_session, []) is True
        mock_ui.print_from_template.assert_called()

def test_agent_command_switch_success(mock_session):
    """Verify /agent <name> switches agent."""
    cmd = AgentCommand()
    new_agent = MagicMock(spec=Agent)
    new_agent.get_identity.return_value = "New Agent"

    mock_session.session_manager.switch_agent.return_value = new_agent

    with patch("vybz.commands.core.ui") as mock_ui:
        assert cmd.execute(mock_session, ["pm"]) is True

        # Verify call to manager
        mock_session.session_manager.switch_agent.assert_called_with("pm")
        # Verify UI update
        mock_ui.render_session_header.assert_called()

def test_agent_command_switch_fail(mock_session):
    """Verify /agent handles invalid agent names gracefully."""
    cmd = AgentCommand()
    mock_session.session_manager.switch_agent.side_effect = ValueError("Not found")

    with patch("vybz.commands.core.ui") as mock_ui, \
         patch("vybz.commands.core.Squad"):

        assert cmd.execute(mock_session, ["ghost"]) is False
        mock_ui.print_error.assert_called()

# -----------------------------------------------------------------------------
# Save Command
# -----------------------------------------------------------------------------

def test_save_command_no_response(mock_session):
    """Verify /save fails if no response exists."""
    cmd = SaveCommand()
    mock_session.last_response = None

    with patch("vybz.commands.core.ui") as mock_ui:
        assert cmd.execute(mock_session, []) is True
        mock_ui.print_error.assert_called_with("Nothing to save. Generate something first.")

def test_save_command_success(mock_session):
    """Verify /save delegates to ArtifactProcessor."""
    cmd = SaveCommand()
    mock_session.last_response = "Some content"
    mock_session.session_manager.codebase = None # Greenfield

    with patch("vybz.commands.core.ArtifactProcessor") as MockProcessor, \
         patch("vybz.commands.core.ui") as mock_ui:

        processor_instance = MockProcessor.return_value
        mock_artifact = MagicMock()
        processor_instance.parse.return_value = [mock_artifact]
        processor_instance.save.return_value = "Saved successfully"

        assert cmd.execute(mock_session, []) is True

        processor_instance.parse.assert_called_with("Some content")
        processor_instance.save.assert_called_with(mock_artifact, ANY)
        mock_ui.print_success.assert_called_with("Saved successfully")

def test_save_command_multiple(mock_session):
    """Verify /save handles multiple artifacts."""
    cmd = SaveCommand()
    mock_session.last_response = "Multi content"
    mock_session.session_manager.codebase = None

    with patch("vybz.commands.core.ArtifactProcessor") as MockProcessor, \
         patch("vybz.commands.core.ui") as mock_ui:

        processor_instance = MockProcessor.return_value
        processor_instance.parse.return_value = [MagicMock(), MagicMock()]
        processor_instance.save.side_effect = ["Saved A", "Saved B"]

        assert cmd.execute(mock_session, []) is True

        assert processor_instance.save.call_count == 2
        mock_ui.print_success.assert_called_with("Batch Save: Processed 2 artifacts.")

# -----------------------------------------------------------------------------
# Config Commands
# -----------------------------------------------------------------------------

def test_set_mode_command_success(mock_session):
    cmd = SetModeCommand()
    with patch("vybz.commands.core.ui") as mock_ui:
        assert cmd.execute(mock_session, ["vi"]) is True
        assert mock_session.session.editing_mode == EditingMode.VI
        mock_ui.print_success.assert_called()

def test_set_mode_command_invalid(mock_session):
    cmd = SetModeCommand()
    with patch("vybz.commands.core.ui") as mock_ui:
        assert cmd.execute(mock_session, ["invalid"]) is True
        mock_ui.print_error.assert_called()

def test_theme_command(mock_session):
    cmd = ThemeCommand()
    with patch("vybz.commands.core.ui") as mock_ui:
        mock_ui.set_theme.return_value = True

        assert cmd.execute(mock_session, ["matrix"]) is True
        mock_ui.set_theme.assert_called_with("matrix")
        mock_ui.print_success.assert_called()

