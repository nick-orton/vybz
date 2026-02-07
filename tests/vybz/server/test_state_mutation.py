"""
tests/vybz/server/test_state_mutation.py

Unit tests for the ServerState mutation logic.
Verifies session-scoped skill management and manual context injection.
"""

import sys
import pytest
from unittest.mock import MagicMock, patch, ANY, AsyncMock

# Mock ADK before imports
mock_adk = MagicMock()
mock_sessions = MagicMock()
sys.modules["google.adk"] = mock_adk
sys.modules["google.adk.sessions"] = mock_sessions

from vybz.server.state import ServerState
from vybz.shared.agent import Agent as VybzAgent
from vybz.shared.skill import Skill as VybzSkill

@pytest.mark.asyncio
class TestServerStateMutation:

    @pytest.fixture
    def state(self):
        """Returns a ServerState instance with basic mock registry."""
        s = ServerState()
        s.agent_templates = {"junior": MagicMock()} # Fixed attribute name
        s.library = MagicMock()
        # Mock session service
        s.session_service = MagicMock()
        s.session_service.create_session = AsyncMock()
        s.session_service.get_session = AsyncMock()
        return s

    @pytest.fixture
    def active_session(self, state):
        """Creates a mock session and injects it into the state."""
        session_id = "test-session-uuid"
        mock_session = MagicMock()
        mock_session.id = session_id
        mock_session.state = {
            "vybz_agent": MagicMock(spec=VybzAgent),
            "manual_context": {},
            "codebase_context": "# Initial Code"
        }
        mock_session.agent = MagicMock() # The ADK Agent instance

        # Configure service to return this session
        state.session_service.get_session.return_value = mock_session

        # Configure runner
        mock_runner = MagicMock()
        mock_runner.agent = mock_session.agent
        state.runners[session_id] = mock_runner

        return session_id, mock_session

    async def test_get_session_skills(self, state, active_session):
        """Verify listing skills for a specific session."""
        sid, session = active_session
        mock_skill = MagicMock(spec=VybzSkill)
        session.state["vybz_agent"].skills = [mock_skill]

        # Act
        skills = await state.get_session_skills(sid)

        # Assert
        assert len(skills) == 1
        assert skills[0] == mock_skill

    async def test_uplevel_session_skill(self, state, active_session):
        """Verify adding a skill to a session agent."""
        sid, session = active_session
        skill_data = {
            "id": "new-skill",
            "name": "New Skill",
            "description": "Desc",
            "instructions": "Be helpful"
        }

        with patch("vybz.server.state.VybzSkill") as MockSkillClass, \
             patch("vybz.services.context.ContextAssembler.build_system_instruction") as mock_assembler:

            mock_assembler.return_value = "New System Prompt"

            # Act
            await state.uplevel_session_skill(sid, skill_data)

            # Assert
            # 1. Skill instantiated
            MockSkillClass.assert_called_with(
                id="new-skill", name="New Skill", description="Desc", instructions="Be helpful"
            )
            # 2. Agent mutated
            session.state["vybz_agent"].add_skill.assert_called_once()
            # 3. Instructions Refreshed
            assert "New System Prompt" in session.agent.instruction

    async def test_downlevel_session_skill_success(self, state, active_session):
        """Verify removing a skill and refreshing instructions."""
        sid, session = active_session
        session.state["vybz_agent"].remove_skill.return_value = True

        # Act
        result = await state.downlevel_session_skill(sid, "old-skill")

        # Assert
        assert result is True
        session.state["vybz_agent"].remove_skill.assert_called_with("old-skill")
        # Instruction update should have been triggered
        assert session.agent.instruction is not None

    async def test_load_session_context(self, state, active_session):
        """Verify manual context is stored and instructions refreshed."""
        sid, session = active_session
        filename = "config.yaml"
        content = "key: value"

        with patch("vybz.services.context.ContextAssembler.build_system_instruction") as mock_assembler:
            mock_assembler.return_value = "Prompt with Manual Context"

            # Act
            await state.load_session_context(sid, filename, content)

            # Assert
            assert session.state["manual_context"][filename] == content
            # Verify refresh
            mock_assembler.assert_called_with(ANY, codebase=None, manual_context=session.state["manual_context"])
            assert session.agent.instruction.startswith("Prompt with Manual Context")

    async def test_refresh_instructions_appends_codebase(self, state, active_session):
        """Verify that refresh logic combines persona prompt with codebase string."""
        sid, session = active_session
        session.state["codebase_context"] = "CODEBASE_CONTENT"

        with patch("vybz.services.context.ContextAssembler.build_system_instruction") as mock_assembler:
            mock_assembler.return_value = "PERSONA_PROMPT"

            # Act
            await state._refresh_session_instructions(sid)

            # Assert
            expected = "PERSONA_PROMPT\n\nCODEBASE_CONTENT"
            assert session.agent.instruction == expected
