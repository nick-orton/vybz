"""
tests/vybz/server/test_adapter.py

Unit tests for the ADK Adapter Layer.
Verifies the hydration of Vybz Agents/Skills into Google ADK objects.
"""
import sys
import pytest
from unittest.mock import MagicMock, patch, ANY
from pathlib import Path

# -----------------------------------------------------------------------------
# Dependency Mocking (Pre-Import)
# -----------------------------------------------------------------------------
mock_adk = MagicMock()
sys.modules["google.adk"] = mock_adk

from vybz.server.adapter import AdkHydrator
from vybz.shared.agent import Agent as VybzAgent
from vybz.shared.library import Library


class TestAdkHydrator:
    """
    Tests for the AdkHydrator service.
    """

    @pytest.fixture
    def hydrator(self):
        return AdkHydrator()

    @pytest.fixture
    def mock_vybz_agent(self):
        """Returns a mock Vybz Agent with necessary methods."""
        agent = MagicMock(spec=VybzAgent)
        agent.name = "Test Agent"
        agent.id = "test-agent"
        agent.construct_agent_role_profile.return_value = "System Prompt Content"
        return agent

    def test_hydrate_agent_attributes(self, hydrator, mock_vybz_agent):
        """
        Verify that a Vybz Agent is correctly converted to an ADK Agent
        with mapped attributes (name, system_prompt, model).
        """
        # Patch the adk module imported in adapter.py to handle import caching issues
        with patch("vybz.server.adapter.adk") as mock_adk_scoped:
            # Act
            adk_agent = hydrator.hydrate_agent(mock_vybz_agent, "gemini-3-flash-preview")

            # Assert
            # Verify call to construct prompt
            mock_vybz_agent.construct_agent_role_profile.assert_called_once()

            # Verify ADK Agent instantiation
            mock_adk_scoped.Agent.assert_called_with(
                name="test_agent",
                model="gemini-3-flash-preview",
                description="Test Agent",
                instruction="System Prompt Content",
                tools=[],
                planner=ANY
            )

            # Verify return value is whatever adk.Agent() returned
            assert adk_agent == mock_adk_scoped.Agent.return_value

    def test_hydrate_squad_success(self, hydrator, mock_vybz_agent):
        """
        Verify that hydrate_squad_templates iterates through the library, loads agents,
        and returns a populated registry.
        """
        # Arrange
        mock_library = MagicMock(spec=Library)
        mock_library.list_agents.return_value = ["junior-dev", "pm"]
        mock_library.get_agent_path.return_value = Path("/fake/path")

        # Mock the factory method on VybzAgent class
        with patch("vybz.server.adapter.VybzAgent") as MockAgentClass:
            MockAgentClass.from_toml.return_value = mock_vybz_agent

            # Act
            registry = hydrator.hydrate_squad_templates(mock_library)

        # Assert
        # Should attempt to load both agents
        assert len(registry) == 2
        assert "junior-dev" in registry
        assert "pm" in registry

        # Verify Library interactions
        assert mock_library.get_agent_path.call_count == 2
        mock_library.get_agent_path.assert_any_call("junior-dev")
        mock_library.get_agent_path.assert_any_call("pm")

        # Verify Factory usage (Dependency Injection of library)
        MockAgentClass.from_toml.assert_called_with(Path("/fake/path"), library=mock_library)

    def test_hydrate_squad_partial_failure(self, hydrator, mock_vybz_agent, capsys):
        """
        Verify that if one agent fails to load (e.g. bad TOML), the hydrator
        logs the error and continues to load the others (Fail Open).
        """
        # Arrange
        mock_library = MagicMock(spec=Library)
        mock_library.list_agents.return_value = ["good-agent", "bad-agent"]

        with patch("vybz.server.adapter.VybzAgent") as MockAgentClass:
            # First call succeeds, second raises Exception
            MockAgentClass.from_toml.side_effect = [
                mock_vybz_agent,
                RuntimeError("Corrupt TOML")
            ]

            # Act
            registry = hydrator.hydrate_squad_templates(mock_library)

        # Assert
        assert len(registry) == 1
        assert "good-agent" in registry
        assert "bad-agent" not in registry

        # Verify error printed (since adapter uses print(), not logger yet)
        captured = capsys.readouterr()
        assert "Failed to load agent template 'bad-agent': Corrupt TOML" in captured.out
