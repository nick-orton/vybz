"""
tests/vybz/services/test_context.py

Unit tests for the ContextAssembler service.
Verifies the correct assembly of system prompts including Persona, Time, and Codebase.
"""
import pytest
from unittest.mock import MagicMock

from vybz.services.context import ContextAssembler
from vybz.shared.agent import Agent
from vybz.shared.codebase import CodeBase


class TestContextAssembler:
    """
    Tests for the ContextAssembler.build_system_instruction static method.
    """

    @pytest.fixture
    def mock_agent(self):
        """Returns a mock Agent with a fixed role profile."""
        agent = MagicMock(spec=Agent)
        agent.construct_agent_role_profile.return_value = "I am a Test Agent."
        return agent

    @pytest.fixture
    def mock_codebase(self):
        """Returns a mock CodeBase with fixed render output."""
        codebase = MagicMock(spec=CodeBase)
        codebase.render.return_value = "# CodeBase Snapshot"
        return codebase

    def test_build_system_instruction_with_codebase(self, mock_agent, mock_codebase, mocker):
        """
        Verify that the system instruction includes Agent profile, Date, and CodeBase
        when a CodeBase is provided.
        """
        # Arrange
        # Mock datetime to ensure deterministic test output regardless of when it runs
        mock_dt = mocker.patch("vybz.services.context.datetime")
        mock_dt.datetime.now.return_value.strftime.return_value = "2099-01-01"

        # Act (Pass root path string as per 3.6 architecture)
        result = ContextAssembler.build_system_instruction(mock_agent, "/mnt/project")

        # Assert
        # 1. Check Agent Role presence
        assert "I am a Test Agent." in result

        # 2. Check Date Injection
        assert "### SYSTEM METADATA" in result
        assert "Current Date: 2099-01-01" in result

        # 3. Check Filesystem Access section
        assert "### FILESYSTEM ACCESS" in result
        assert "/mnt/project" in result

    def test_build_system_instruction_without_codebase(self, mock_agent, mocker):
        """
        Verify that the system instruction omits CodeBase content when None is passed.
        """
        # Arrange
        mock_dt = mocker.patch("vybz.services.context.datetime")
        mock_dt.datetime.now.return_value.strftime.return_value = "2099-01-01"

        # Act
        result = ContextAssembler.build_system_instruction(mock_agent, None)

        # Assert
        assert "I am a Test Agent." in result
        assert "Current Date: 2099-01-01" in result

        # Verify CodeBase content is NOT present
        # Since we passed None, the render method (and our mock string) should never appear.
        # We check that the string effectively ends after the metadata section.
        assert "# CodeBase Snapshot" not in result
        assert result.strip().endswith("Current Date: 2099-01-01")

    def test_build_system_instruction_with_manual_context(self, mock_agent, mocker):
        """
        Verify that manually loaded files are injected into the system instruction.
        """
        # Arrange
        mocker.patch("vybz.services.context.datetime").datetime.now.return_value.strftime.return_value = "2099-01-01"
        
        manual_files = {
            "/path/to/extra.py": "print('extra')",
            "notes.txt": "Remember this."
        }

        # Act
        result = ContextAssembler.build_system_instruction(mock_agent, None, manual_context=manual_files)

        # Assert
        assert "### MANUAL CONTEXT" in result
        assert "#### File: /path/to/extra.py" in result
        assert "print('extra')" in result
        assert "#### File: notes.txt" in result
