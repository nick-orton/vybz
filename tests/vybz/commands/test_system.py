"""
tests/vybz/commands/test_system.py

Unit tests for local system and UI-centric REPL commands.
Verifies interaction with UI, ArtifactProcessor, and Prompt Toolkit.
"""
import pytest
from unittest.mock import MagicMock, patch, ANY
from pathlib import Path
from prompt_toolkit.enums import EditingMode

from vybz.repl import ReplSession
from vybz.commands.system import (
    ExitCommand,
    ClearCommand,
    HelpCommand,
    SaveCommand,
    SetModeCommand,
    ThemeCommand
)

@pytest.fixture
def mock_session():
    """Returns a mock ReplSession with necessary attributes."""
    session = MagicMock(spec=ReplSession)
    session.session_manager = MagicMock()
    session.session = MagicMock()
    session.last_response = None
    return session

def test_exit_command(mock_session):
    cmd = ExitCommand()
    with pytest.raises(EOFError):
        cmd.execute(mock_session, [])

def test_clear_command(mock_session):
    cmd = ClearCommand()
    with patch("vybz.commands.system.ui") as mock_ui:
        assert cmd.execute(mock_session, []) is True
        mock_ui.console.clear.assert_called_once()
        mock_ui.render_session_header.assert_called_once()

def test_help_command(mock_session):
    cmd = HelpCommand()
    with patch("vybz.commands.system.AssetLoader") as mock_loader, \
         patch("vybz.commands.system.ui") as mock_ui:

        mock_loader.load_text.return_value = "Help Content"
        assert cmd.execute(mock_session, []) is True
        mock_ui.print_panel.assert_called_with("Help Content", title="Help Menu")

def test_save_command_no_response(mock_session):
    cmd = SaveCommand()
    mock_session.last_response = None
    with patch("vybz.commands.system.ui") as mock_ui:
        assert cmd.execute(mock_session, []) is True
        mock_ui.print_error.assert_called_with("Nothing to save. Generate something first.")

def test_save_command_success(mock_session):
    cmd = SaveCommand()
    mock_session.last_response = "Some content"
    mock_session.session_manager.codebase = None

    with patch("vybz.commands.system.ArtifactProcessor") as MockProcessor, \
         patch("vybz.commands.system.ui") as mock_ui:

        processor_instance = MockProcessor.return_value
        mock_artifact = MagicMock()
        processor_instance.parse.return_value = [mock_artifact]
        processor_instance.save.return_value = "Saved successfully"

        assert cmd.execute(mock_session, []) is True
        processor_instance.parse.assert_called_with("Some content")
        mock_ui.print_success.assert_called_with("Saved successfully")

def test_set_mode_command_success(mock_session):
    cmd = SetModeCommand()
    with patch("vybz.commands.system.ui") as mock_ui:
        assert cmd.execute(mock_session, ["vi"]) is True
        assert mock_session.session.editing_mode == EditingMode.VI
        mock_ui.print_success.assert_called()

def test_theme_command(mock_session):
    cmd = ThemeCommand()
    with patch("vybz.commands.system.ui") as mock_ui:
        mock_ui.set_theme.return_value = True
        assert cmd.execute(mock_session, ["matrix"]) is True
        mock_ui.set_theme.assert_called_with("matrix")
        mock_ui.print_success.assert_called()
