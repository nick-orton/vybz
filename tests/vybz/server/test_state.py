"""
tests/vybz/server/test_state.py

Unit tests for the ServerState singleton.
Verifies initialization, agent registry lookups, and session lifecycle management.
"""
import sys
import pytest
from unittest.mock import MagicMock, patch, ANY, AsyncMock

# We must mock google.labs.adk BEFORE importing vybz.server.state
# because the module imports it at the top level.
mock_adk = MagicMock()
mock_sessions_module = MagicMock()

sys.modules["google.adk"] = mock_adk
sys.modules["google.adk.sessions"] = mock_sessions_module

from vybz.server.state import ServerState

class TestServerState:
    """
    Tests for the ServerState container.
    """

    @pytest.fixture
    def state(self):
        """Returns a fresh ServerState instance."""
        return ServerState()

    @pytest.fixture
    def mock_adk_agent(self):
        """Returns a mock ADK Agent object."""
        agent = MagicMock()
        agent.name = "Test Agent"
        return agent

    def test_initialize_loads_squad(self, state, mock_adk_agent):
        """
        Verify that initialize() coordinates Config, Library, and Hydrator
        to populate the agent registry.
        """
        # Arrange
        mock_templates = {"junior-dev": MagicMock()}

        with patch("vybz.server.state.ConfigLoader") as MockConfig, \
             patch("vybz.server.state.Library") as MockLibrary:

            # Setup Config
            MockConfig.load.return_value = {"model": "custom-model"}

            # Setup Hydrator behavior on the instance
            # Since hydrator is created in __init__, we mock the method on the existing instance
            state.hydrator.hydrate_squad_templates = MagicMock(return_value=mock_templates)

            # Act
            state.initialize()

            # Assert
            assert state.model_id == "custom-model"
            MockLibrary.assert_called_once()
            state.hydrator.hydrate_squad_templates.assert_called_with(
                MockLibrary.return_value
            )
            assert state.agent_templates == mock_templates

    @pytest.mark.asyncio
    async def test_create_session_with_context(self, state, mock_adk_agent):
        """
        Verify session creation:
        1. Clones VybzAgent.
        2. Hydrates ADK Agent.
        3. Creates Runner.
        4. Creates Session via Service.
        5. Injects context.
        """
        # Arrange
        # 1. Setup State
        state.agent_templates = {"dev": MagicMock()}
        state.library = MagicMock()
        state.library.get_agent_path.return_value = "/fake/path/dev.toml"
        state.model_id = "test-model"

        context_str = "# CodeBase Snapshot..."

        # 2. Mock Session Service response
        mock_session_obj = MagicMock()
        mock_session_obj.id = "session-uuid"
        mock_session_obj.state = {}
        # Make create_session awaitable
        state.session_service.create_session = AsyncMock(return_value=mock_session_obj)
        state.session_service.get_session = AsyncMock(return_value=mock_session_obj)

        # 3. Patch Dependencies
        with patch("vybz.server.state.VybzAgent") as MockVybzAgentClass, \
             patch("vybz.server.state.adk.Runner") as MockRunnerClass, \
             patch("vybz.server.state.ContextAssembler") as MockAssembler:

            mock_vybz_instance = MagicMock()
            MockVybzAgentClass.from_toml.return_value = mock_vybz_instance

            # Setup Hydrator return on instance
            state.hydrator.hydrate_agent = MagicMock(return_value=mock_adk_agent)

            # Act
            session_id = await state.create_session("dev", context=context_str)

            # Assert
            # 1. Verify Vybz Agent Clone
            MockVybzAgentClass.from_toml.assert_called()

            # 2. Verify ADK Agent Hydration
            state.hydrator.hydrate_agent.assert_called_with(mock_vybz_instance, "test-model")

            # 3. Verify Runner Instantiation
            MockRunnerClass.assert_called_with(
                agent=mock_adk_agent,
                app_name="vybzd",
                session_service=state.session_service
            )

            # 4. Verify Session Creation
            state.session_service.create_session.assert_called_with(
                    app_name="vybzd",
                    user_id=state.user_id,
                    state={
                        "vybz_agent": mock_vybz_instance,
                        "manual_context": {},
                        "codebase_context": context_str
                    }
            )

            # 5. Verify Context Injection into Session State
            #assert mock_session_obj.state["vybz_agent"] == mock_vybz_instance
            #assert mock_session_obj.state["codebase_context"] == context_str

            # 6. Verify Return
            assert session_id == "session-uuid"
            assert "session-uuid" in state.runners

    def test_get_runner_success(self, state):
        """Verify retrieval of active runner."""
        sid = "unique-id"
        mock_runner = MagicMock()
        state.runners[sid] = mock_runner
        result = state.get_runner(sid)
        assert result == mock_runner

    def test_get_runner_not_found(self, state):
        """Verify error for invalid session ID."""
        with pytest.raises(ValueError):
            state.get_runner("missing-id")
