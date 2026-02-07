"""
tests/vybz/services/test_session.py

Unit tests for the SessionManager service.
Verifies multi-agent state management, chat creation, and context refreshing.
"""
import pytest
from unittest.mock import MagicMock, patch
from google.genai import types

from vybz.services.session import SessionManager
from vybz.shared.agent import Agent
from vybz.shared.codebase import CodeBase

class TestSessionManager:

    @pytest.fixture
    def mock_client(self):
        """Mocks the Google GenAI Client."""
        client = MagicMock()
        # Mock chat object returned by create
        mock_chat = MagicMock()
        mock_chat2 = MagicMock()
        client.chats.create.side_effect = [mock_chat, mock_chat2]
        return client

    @pytest.fixture
    def mock_agent_a(self):
        """Returns a primary mock agent."""
        agent = MagicMock(spec=Agent)
        agent.id = "agent-a"
        agent.name = "Agent A"
        return agent

    @pytest.fixture
    def mock_agent_b(self):
        """Returns a secondary mock agent."""
        agent = MagicMock(spec=Agent)
        agent.id = "agent-b"
        agent.name = "Agent B"
        return agent

    @pytest.fixture
    def mock_codebase(self):
        """Returns a mock CodeBase."""
        cb = MagicMock(spec=CodeBase)
        cb.root_path = "/tmp/fake/root"
        return cb

    @pytest.fixture
    def manager(self, mock_client, mock_agent_a, mock_codebase):
        """Returns an initialized SessionManager instance with dependencies patched."""
        with patch("vybz.services.session.ContextAssembler") as mock_assembler:
            mock_assembler.build_system_instruction.return_value = "System Prompt"
            return SessionManager(
                client=mock_client,
                model_id="gemini-test",
                initial_agent=mock_agent_a,
                codebase=mock_codebase
            )

    def test_init_activates_initial_session(self, manager, mock_client, mock_agent_a):
        """Verify __init__ immediately creates a chat for the initial agent."""
        # Assert active pointers
        assert manager.active_agent == mock_agent_a
        assert manager.active_chat is not None
        assert "agent-a" in manager.sessions

        # Verify API call
        mock_client.chats.create.assert_called_once()
        _, kwargs = mock_client.chats.create.call_args
        assert kwargs["model"] == "gemini-test"
        # Verify config type usage
        assert isinstance(kwargs["config"], types.GenerateContentConfig)
        assert kwargs["config"].system_instruction == "System Prompt"

    def test_switch_agent_new_session(self, manager, mock_client, mock_agent_b):
        """Verify switching to a new agent creates a new session."""
        # Arrange
        with patch("vybz.services.session.Squad") as mock_squad:
            mock_squad.get_agent.return_value = mock_agent_b

            # Act
            returned_agent = manager.switch_agent("agent-b")

        # Assert
        assert returned_agent == mock_agent_b
        assert manager.active_agent == mock_agent_b
        assert "agent-b" in manager.sessions
        # Should have called create twice now (once for A in init, once for B)
        assert mock_client.chats.create.call_count == 2

    def test_switch_agent_existing_session(self, manager, mock_client, mock_agent_a):
        """Verify switching back to an existing agent reuses the session."""
        # Arrange - Switch to A (who is already active/loaded from init)
        with patch("vybz.services.session.Squad") as mock_squad:
            mock_squad.get_agent.return_value = mock_agent_a

            # Act
            manager.switch_agent("agent-a")

        # Assert
        # Should NOT call create again (count remains 1 from init)
        assert mock_client.chats.create.call_count == 1
        assert manager.active_agent == mock_agent_a

    def test_switch_agent_lookup_failure(self, manager):
        """Verify ValueError bubbles up if Squad fails."""
        with patch("vybz.services.session.Squad") as mock_squad:
            mock_squad.get_agent.side_effect = ValueError("Agent not found")

            with pytest.raises(ValueError):
                manager.switch_agent("ghost-agent")

    def test_refresh_context_rebuilds_sessions(self, manager, mock_client, mock_agent_a, mock_codebase):
        """
        Verify refresh_context:
        1. Re-snapshots CodeBase.
        2. Iterates sessions.
        3. Extracts history.
        4. Creates new chat objects.
        """
        # Arrange
        # Mock the existing chat to return some history
        old_chat = manager.sessions["agent-a"]
        mock_history = [{"role": "user", "parts": ["Hi"]}]
        old_chat.get_history.return_value = mock_history

        # Mock CodeBase constructor to verify re-instantiation
        with patch("vybz.services.session.CodeBase", return_value=mock_codebase) as MockCodeBaseClass, \
             patch("vybz.services.session.Squad") as mock_squad:

            # Squad needs to return the agent object during rebuild loop
            mock_squad.get_agent.return_value = mock_agent_a

            # Act
            count = manager.refresh_context()

            # Assert
            assert count == 1
            # CodeBase should be re-initialized
            MockCodeBaseClass.assert_called_with(mock_codebase.root_path)

            # Client.chats.create should be called again (Init + Refresh = 2)
            assert mock_client.chats.create.call_count == 2

            # Verify history was passed to the new chat
            _, kwargs = mock_client.chats.create.call_args
            assert kwargs["history"] == mock_history

            # Verify session dictionary updated
            assert manager.sessions["agent-a"] != old_chat

    def test_refresh_context_handles_errors(self, manager):
        """Verify that a failure in one session refresh doesn't crash the method."""
        # Arrange
        # Force an error during history extraction for the active session
        bad_chat = MagicMock()
        bad_chat.get_history.side_effect = Exception("API Error")
        manager.sessions["agent-a"] = bad_chat

        # Act
        with patch("vybz.services.session.CodeBase"), \
             patch("vybz.services.session.ui") as mock_ui:

            count = manager.refresh_context()

        # Assert
        assert count == 0 # No sessions successfully refreshed
        mock_ui.print_error.assert_called() # Error logged

    def test_load_file_success(self, manager, tmp_path):
        """Verify load_file reads content and updates manual_context."""
        # Arrange
        target_file = tmp_path / "secrets.txt"
        target_file.write_text("Secret Data", encoding="utf-8")

        # Act
        result = manager.load_file(str(target_file))

        # Assert
        assert result == str(target_file)
        assert str(target_file) in manager.manual_context
        assert manager.manual_context[str(target_file)] == "Secret Data"

    def test_load_file_not_found(self, manager):
        """Verify load_file raises FileNotFoundError for missing files."""
        with pytest.raises(FileNotFoundError):
            manager.load_file("/non/existent/path")

    def test_create_chat_passes_manual_context(self, manager, mock_agent_a):
        """Verify that manual context is passed to the prompt assembler."""
        # Arrange
        manager.manual_context = {"/path/to/file": "content"}
        
        with patch("vybz.services.session.ContextAssembler") as mock_assembler:
            # Act
            manager._create_chat(mock_agent_a)
            
            # Assert
            mock_assembler.build_system_instruction.assert_called_with(
                mock_agent_a, 
                manager.codebase, 
                manager.manual_context
            )
