"""
tests/vybz/commands/test_core.py

Unit tests for Agent and Session orchestration commands.
Refactored for asynchronous execution and vybzd engine compatibility.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from pathlib import Path

from vybz.repl import ReplSession
from vybz.client.api import AgentListing, SkillDTO
from vybz.commands.core import (
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
    """Returns a mock ReplSession with an async session manager."""
    session = MagicMock(spec=ReplSession)

    # Mock the ClientSessionManager
    sm = MagicMock()
    sm.client = MagicMock()
    sm.active_agent = MagicMock()
    sm.active_agent.name = "Test Agent"
    sm.codebase = None
    sm.model_id = "gemini-test"
    sm.session_id = "uuid-123"

    # Async methods on manager
    sm.refresh_context = AsyncMock()
    sm.switch_agent = AsyncMock()

    # Async methods on client
    sm.client.list_agents = AsyncMock()
    sm.client.list_session_skills = AsyncMock()
    sm.client.uplevel_skill = AsyncMock()
    sm.client.downlevel_skill = AsyncMock()
    sm.client.load_file_content = AsyncMock()

    session.session_manager = sm
    session.session = MagicMock()
    session.last_response = None
    return session

# -----------------------------------------------------------------------------
# Session Orchestration Tests
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_agent_command_list(mock_session):
    """Verify /agent without args lists agents from the client."""
    cmd = AgentCommand()
    sm = mock_session.session_manager

    # Arrange
    sm.client.list_agents.return_value = [
        AgentListing(id="pm", name="PM", description="..."),
        AgentListing(id="dev", name="Dev", description="...")
    ]

    with patch("vybz.commands.core.ui") as mock_ui, \
         patch("vybz.commands.core.AssetLoader") as mock_loader:

        mock_loader.load_text.return_value = "Template"

        # Act
        assert await cmd.execute(mock_session, []) is True

        # Assert
        sm.client.list_agents.assert_called_once()
        mock_ui.print_from_template.assert_called()

@pytest.mark.asyncio
async def test_agent_command_switch_success(mock_session):
    """Verify /agent <name> switches agent via manager."""
    cmd = AgentCommand()
    sm = mock_session.session_manager
    sm.switch_agent.return_value = True
    sm.active_agent.name = "New Agent"

    with patch("vybz.commands.core.ui") as mock_ui:
        assert await cmd.execute(mock_session, ["pm"]) is True
        sm.switch_agent.assert_called_with("pm")
        mock_ui.render_session_header.assert_called()

@pytest.mark.asyncio
async def test_agent_command_switch_fail(mock_session):
    """Verify /agent handles switch failures."""
    cmd = AgentCommand()
    sm = mock_session.session_manager
    sm.switch_agent.return_value = False

    with patch("vybz.commands.core.ui") as mock_ui:
        # Command still returns True to continue the REPL loop
        assert await cmd.execute(mock_session, ["ghost"]) is True
        mock_ui.render_session_header.assert_not_called()

@pytest.mark.asyncio
async def test_load_command_success(mock_session, tmp_path):
    """Verify /load reads local file and uploads to client."""
    cmd = LoadCommand()
    sm = mock_session.session_manager
    sm.client.load_file_content.return_value = True

    # Create a real temp file to satisfy Path.is_file()
    test_file = tmp_path / "test.py"
    test_file.write_text("print(1)", encoding="utf-8")

    with patch("vybz.commands.core.ui") as mock_ui:
        assert await cmd.execute(mock_session, [str(test_file)]) is True
        sm.client.load_file_content.assert_called_once()
        mock_ui.print_success.assert_called()

@pytest.mark.asyncio
async def test_load_command_missing_args(mock_session):
    cmd = LoadCommand()
    with patch("vybz.commands.core.ui") as mock_ui:
        assert await cmd.execute(mock_session, []) is True
        mock_ui.print_error.assert_called_with("Usage: /load <path>")

@pytest.mark.asyncio
async def test_load_command_error(mock_session, tmp_path):
    """Verify error handling when upload fails."""
    cmd = LoadCommand()
    sm = mock_session.session_manager
    sm.client.load_file_content.side_effect = Exception("Upload Failed")

    test_file = tmp_path / "test.py"
    test_file.touch()

    with patch("vybz.commands.core.ui") as mock_ui:
        assert await cmd.execute(mock_session, [str(test_file)]) is True
        mock_ui.print_error.assert_called()

# -----------------------------------------------------------------------------
# Dynamic Skill Tests
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_skills_command_renders_table(mock_session):
    cmd = SkillsCommand()
    sm = mock_session.session_manager
    sm.client.list_session_skills.return_value = [
        SkillDTO(id="test", name="T", description="D", instructions="I")
    ]

    with patch("vybz.commands.core.ui") as mock_ui:
        assert await cmd.execute(mock_session, []) is True
        sm.client.list_session_skills.assert_called_with(sm.session_id)
        mock_ui.console.print.assert_called_once()

@pytest.mark.asyncio
async def test_uplevel_command_success(mock_session, tmp_path):
    cmd = UplevelCommand()
    sm = mock_session.session_manager
    sm.client.uplevel_skill.return_value = True

    skill_dir = tmp_path / "new-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("---\nname: new-skill\n---", encoding="utf-8")

    with patch("vybz.commands.core.Skill") as MockSkill, \
         patch("vybz.commands.core.ui") as mock_ui:

        mock_skill_obj = MagicMock()
        mock_skill_obj.id = "new-skill"
        mock_skill_obj.name = "New Skill"
        mock_skill_obj.description = "Desc"
        mock_skill_obj.instructions = "Inst"
        MockSkill.from_directory.return_value = mock_skill_obj

        assert await cmd.execute(mock_session, [str(skill_dir)]) is True
        sm.client.uplevel_skill.assert_called_once()
        mock_ui.print_success.assert_called()

@pytest.mark.asyncio
async def test_downlevel_command_success(mock_session):
    cmd = DownlevelCommand()
    sm = mock_session.session_manager
    sm.client.downlevel_skill.return_value = True

    with patch("vybz.commands.core.ui") as mock_ui:
        assert await cmd.execute(mock_session, ["unwanted"]) is True
        sm.client.downlevel_skill.assert_called_with(sm.session_id, "unwanted")
        mock_ui.print_success.assert_called()
