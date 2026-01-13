"""
tests/vybz/test_repl.py

Comprehensive unit tests for the ReplSession.
Focuses on State Management, Agent Switching, and Artifact Parsing/Persistence.
"""
import pytest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path
import datetime

from vybz.repl import ReplSession
from vybz.agent import Agent
from vybz.context_engine import CodeBase

# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def mock_agent():
    """Returns a standard Agent object."""
    return Agent(
        id="test-agent",
        name="Test Agent",
        version="1",
        role_spec="You are a test agent.",
        operating_context="Testing context.",
        task_directive="Do tests."
    )

@pytest.fixture
def mock_codebase(tmp_path):
    """Returns a mock CodeBase object."""
    cb = MagicMock(spec=CodeBase)
    cb.root_path = tmp_path / "project_root"
    cb.render.return_value = "# Mock CodeBase\n\n## Structure"
    return cb

@pytest.fixture
def repl(mock_genai_client, mock_agent, mock_codebase, tmp_path):
    """
    Returns an initialized ReplSession with dependencies mocked.
    Patches PromptSession to avoid TUI startup.
    """
    with patch("vybz.repl.PromptSession"):
        session = ReplSession(
            client=mock_genai_client,
            agent=mock_agent,
            model_id="gemini-3-test",
            codebase=mock_codebase,
            log_file=tmp_path / "vybz.log"
        )
    return session

# -----------------------------------------------------------------------------
# Initialization & System Prompt Tests
# -----------------------------------------------------------------------------

def test_repl_init(repl, mock_agent):
    """Verify session initializes with the correct active agent and chat."""
    assert repl.active_agent == mock_agent
    assert repl.active_agent.id in repl.sessions
    assert repl.active_chat is not None
    assert repl.sessions[mock_agent.id] == repl.active_chat

def test_build_system_instruction(repl, mock_agent):
    """Verify system instruction includes Role, Date, and CodeBase."""
    # Act
    sys_prompt = repl._build_system_instruction(mock_agent)

    # Assert
    assert "### ROLE SPECIFICATION" in sys_prompt
    assert mock_agent.role_spec in sys_prompt
    assert "### SYSTEM METADATA" in sys_prompt
    assert "Current Date:" in sys_prompt
    assert "# Mock CodeBase" in sys_prompt

# -----------------------------------------------------------------------------
# Agent Switching Tests
# -----------------------------------------------------------------------------

def test_switch_agent_by_name_success(repl, mock_genai_client):
    """Verify switching to a valid agent updates state and UI."""
    # Arrange
    new_agent = Agent(
        id="pm", name="PM Lead", version="1",
        role_spec="PM", operating_context="", task_directive=""
    )

    with patch("vybz.repl.Squad") as mock_squad, \
         patch("vybz.repl.ui") as mock_ui:

        mock_squad.get_agent.return_value = new_agent

        # Act
        result = repl._switch_to_agent_by_name("pm")

        # Assert
        assert result is True
        assert repl.active_agent.id == "pm"
        assert "pm" in repl.sessions
        # Verify a new chat was created for the PM
        assert mock_genai_client.chats.create.call_count == 2
        mock_ui.render_session_header.assert_called()

def test_switch_agent_invalid(repl):
    """Verify robust handling of invalid agent names."""
    with patch("vybz.repl.Squad") as mock_squad, \
         patch("vybz.repl.ui") as mock_ui:

        mock_squad.get_agent.side_effect = ValueError("Agent not found")
        mock_squad.list_agents.return_value = ["junior-dev", "pm"]

        # Act
        result = repl._switch_to_agent_by_name("ghost-agent")

        # Assert
        assert result is False
        assert repl.active_agent.id == "test-agent" # Should not have changed
        mock_ui.print_error.assert_called()

# -----------------------------------------------------------------------------
# Context Refresh Tests (/update)
# -----------------------------------------------------------------------------

def test_refresh_context(repl, mock_codebase):
    """Verify /update reloads codebase and rebuilds chat sessions."""
    # Arrange
    # Mock the CodeBase constructor to simulate a reload
    with patch("vybz.repl.CodeBase", return_value=mock_codebase) as MockCBClass, \
         patch("vybz.repl.ui"), \
         patch("vybz.repl.Squad") as mock_squad:

        mock_squad.get_agent.return_value = repl.active_agent
        # Act
        repl._refresh_context()

        # Assert
        # 1. CodeBase re-instantiated
        MockCBClass.assert_called_with(mock_codebase.root_path)

        # 2. Chat Session Rebuilt (client.chats.create called again)
        # Init called once, Update calls it again for the active agent
        assert repl.client.chats.create.call_count == 2

        # 3. Active Chat pointer updated
        assert repl.active_chat == repl.sessions[repl.active_agent.id]

# -----------------------------------------------------------------------------
# Save Command Tests (/save)
# -----------------------------------------------------------------------------

def test_cmd_save_success(repl, tmp_path):
    """Verify /save writes content to the correct location."""
    # Arrange
    repl.last_response = "```\n---\ntype: Design\n---\n# Save Test\nContent\n```"
    repl.codebase.root_path = tmp_path # Root is temp dir

    # Act
    with patch("vybz.repl.ui") as mock_ui:
        repl._cmd_save()

        # Assert
        expected_file = tmp_path / "designs" / "save-test.md"
        assert expected_file.exists()
        assert expected_file.read_text(encoding="utf-8").strip() == "---\ntype: Design\n---\n# Save Test\nContent"
        mock_ui.print_success.assert_called()

def test_cmd_save_overwrite_warning(repl, tmp_path):
    """Verify warning UI when overwriting existing file."""
    # Arrange
    repl.last_response = "```\n---\ntype: Intent\n---\n# Overwrite Test\n```"
    repl.codebase.root_path = tmp_path

    # Pre-create file
    target = tmp_path / "intents" / "overwrite-test.md"
    target.parent.mkdir()
    target.write_text("Old content")

    # Act
    with patch("vybz.repl.ui") as mock_ui:
        repl._cmd_save()

        # Assert
        assert target.read_text(encoding="utf-8").strip() == "---\ntype: Intent\n---\n# Overwrite Test"
        mock_ui.print_warning.assert_called()

def test_cmd_save_no_response(repl):
    """Verify handling when there is nothing to save."""
    repl.last_response = None
    with patch("vybz.repl.ui") as mock_ui:
        repl._cmd_save()
        mock_ui.print_error.assert_called_with("Nothing to save. Generate something first.")

# -----------------------------------------------------------------------------
# Command Handler Tests
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("command, expected_method", [
    ("/update", "_refresh_context"),
    ("/save", "_cmd_save"),
])
def test_handle_commands(repl, command, expected_method):
    """Verify slash commands trigger correct methods."""
    with patch.object(repl, expected_method) as mock_method:
        assert repl._handle_command(command) is True
        mock_method.assert_called_once()

def test_handle_command_exit(repl):
    """Verify exit commands raise EOFError."""
    with pytest.raises(EOFError):
        repl._handle_command("/exit")
