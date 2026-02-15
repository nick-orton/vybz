"""
tests/vybz/commands/test_core.py

Unit tests for Agent and Session orchestration commands.
Verifies interaction with SessionManager and Squad.
"""
import pytest
from unittest.mock import MagicMock, patch, ANY
from pathlib import Path

from vybz.repl import ReplSession
from vybz.shared.skill import Skill
from vybz.shared.agent import Agent
from vybz.commands.core import (
    UpdateCommand,
    AgentCommand,
    LoadCommand,
    SkillsCommand,
    UplevelCommand,
    DownlevelCommand
)

# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def mock_session():
    """Returns a mock ReplSession with necessary attributes."""
    session = MagicMock(spec=ReplSession)
    session.session_manager = MagicMock()
    session.session = MagicMock()
    session.last_response = None
    session.logger = MagicMock()
    return session

# -----------------------------------------------------------------------------
# Session Orchestration Tests
# -----------------------------------------------------------------------------

def test_update_command(mock_session):
    cmd = UpdateCommand()
    mock_session.session_manager.refresh_context.return_value = 5

    with patch("vybz.commands.core.ui") as mock_ui:
        assert cmd.execute(mock_session, []) is True
        mock_ui.print_success.assert_called()
        mock_session.session_manager.refresh_context.assert_called_once()

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
        mock_session.session_manager.switch_agent.assert_called_with("pm")
        mock_ui.render_session_header.assert_called()

def test_agent_command_switch_fail(mock_session):
    """Verify /agent handles invalid agent names gracefully."""
    cmd = AgentCommand()
    mock_session.session_manager.switch_agent.side_effect = ValueError("Not found")

    with patch("vybz.commands.core.ui") as mock_ui, \
         patch("vybz.commands.core.Squad"):

        assert cmd.execute(mock_session, ["ghost"]) is False
        mock_ui.print_error.assert_called()

def test_load_command_success(mock_session):
    """Verify /load calls session manager and refreshes context."""
    cmd = LoadCommand()
    mock_session.session_manager.load_file.return_value = "/path/to/file.txt"

    with patch("vybz.commands.core.ui") as mock_ui:
        assert cmd.execute(mock_session, ["file.txt"]) is True
        mock_session.session_manager.load_file.assert_called_with("file.txt")
        mock_session.session_manager.refresh_context.assert_called_once()
        mock_ui.print_success.assert_called()

def test_load_command_missing_args(mock_session):
    cmd = LoadCommand()
    with patch("vybz.commands.core.ui") as mock_ui:
        assert cmd.execute(mock_session, []) is True
        mock_ui.print_error.assert_called()

def test_load_command_error(mock_session):
    cmd = LoadCommand()
    mock_session.session_manager.load_file.side_effect = FileNotFoundError("Missing")
    
    with patch("vybz.commands.core.ui") as mock_ui:
        assert cmd.execute(mock_session, ["bad.txt"]) is True
        mock_ui.print_error.assert_called()
        mock_session.session_manager.refresh_context.assert_not_called()

# -----------------------------------------------------------------------------
# Dynamic Skill Tests
# -----------------------------------------------------------------------------

def test_skills_command_renders_table(mock_session):
    cmd = SkillsCommand()
    mock_agent = mock_session.session_manager.active_agent
    mock_agent.skills = [Skill(id="test", name="T", description="D", instructions="")]

    with patch("vybz.commands.core.ui") as mock_ui:
        assert cmd.execute(mock_session, []) is True
        mock_ui.console.print.assert_called_once()

def test_uplevel_command_success(mock_session, tmp_path):
    cmd = UplevelCommand()
    skill_dir = tmp_path / "new-capability"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("---\nname: new-capability\n---", encoding="utf-8")

    with patch("vybz.commands.core.Skill") as MockSkill, \
         patch("vybz.commands.core.ui") as mock_ui:
        
        mock_skill_obj = MagicMock()
        mock_skill_obj.name = "New Capability"
        MockSkill.from_directory.return_value = mock_skill_obj

        assert cmd.execute(mock_session, [str(skill_dir)]) is True
        mock_session.session_manager.active_agent.add_skill.assert_called_with(mock_skill_obj)
        mock_session.session_manager.refresh_context.assert_called_once()

def test_downlevel_command_success(mock_session):
    cmd = DownlevelCommand()
    mock_session.session_manager.active_agent.remove_skill.return_value = True

    with patch("vybz.commands.core.ui") as mock_ui:
        assert cmd.execute(mock_session, ["unwanted"]) is True
        mock_session.session_manager.active_agent.remove_skill.assert_called_with("unwanted")
        mock_session.session_manager.refresh_context.assert_called_once()
