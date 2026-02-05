"""
tests/vybz/test_agent.py

Unit tests for the Agent domain object.
Verifies loading logic, specifically the dual-path skill resolution strategy.
"""
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import vybz.agent
from vybz.agent import Agent

@pytest.fixture
def mock_skill_class():
    """Mocks the Skill class to verify factory calls."""
    with patch("vybz.agent.Skill") as MockSkill:
        yield MockSkill

@pytest.fixture
def agent_env(tmp_path):
    """
    Sets up a temporary environment representing the source tree.
    Returns a tuple: (agent_toml_path, v2_skills_dir)
    """
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()

    # 2. V2 Skills Root (Standard)
    # We construct a fake src/vybz/skills structure
    v2_skills_dir = tmp_path / "src" / "vybz" / "skills"
    v2_skills_dir.mkdir(parents=True)

    # 3. Create a dummy Agent TOML
    agent_file = agents_dir / "test-agent.toml"
    agent_content = """
    name = "Test Agent"
    version = 1
    role_spec = "Role"
    operating_context = "Context"
    task_directive = "Task"
    skills = ["target-skill"]
    """
    agent_file.write_text(agent_content, encoding="utf-8")

    return agent_file, v2_skills_dir

def test_agent_load_missing_skill(agent_env, mock_skill_class):
    """
    Verify FileNotFoundError if skill is found in neither location.
    """
    agent_file, v2_dir = agent_env
    fake_agent_py = v2_dir.parent / "agent.py"

    with patch.object(vybz.agent, "__file__", str(fake_agent_py)):
        with pytest.raises(FileNotFoundError) as exc:
            Agent.from_toml(agent_file)

    assert "Skill 'target-skill' not found" in str(exc.value)
"""
tests/vybz/test_agent.py

Unit tests for the Agent domain object.
Verifies loading logic, specifically the dual-path skill resolution strategy.
"""
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from vybz.agent import Agent

@pytest.fixture
def mock_skill_class():
    """Mocks the Skill class to verify factory calls."""
    with patch("vybz.agent.Skill") as MockSkill:
        yield MockSkill

@pytest.fixture
def agent_env(tmp_path):
    """
    Sets up a temporary environment representing the source tree.
    Returns a tuple: (agent_toml_path, v2_skills_dir)
    """
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()

    # 2. V2 Skills Root
    v2_skills_dir = tmp_path / "src" / "vybz" / "skills"
    v2_skills_dir.mkdir(parents=True)

    # 3. Create a dummy Agent TOML
    agent_file = agents_dir / "test-agent.toml"
    agent_content = """
    name = "Test Agent"
    version = 1
    role_spec = "Role"
    operating_context = "Context"
    task_directive = "Task"
    skills = ["target-skill"]
    """
    agent_file.write_text(agent_content, encoding="utf-8")

    return agent_file, v2_skills_dir

def test_agent_load_skill_v2_success(agent_env, mock_skill_class):
    """
    Verify that an agent can load a v2 skill directory.
    """
    agent_file, v2_dir = agent_env

    # Arrange: Create V2 Skill
    (v2_dir / "target-skill").mkdir()
    (v2_dir / "target-skill" / "SKILL.md").touch()

    # Mock __file__ so Agent finds the v2_dir relative to itself
    fake_agent_py = v2_dir.parent / "agent.py"

    with patch.object(vybz.agent, "__file__", str(fake_agent_py)):
        Agent.from_toml(agent_file)

    # Assert
    mock_skill_class.from_directory.assert_called_once()

def test_agent_load_missing_skill(agent_env, mock_skill_class):
    """
    Verify FileNotFoundError if skill is found in neither location.
    """
    agent_file, v2_dir = agent_env

    # Arrange: Create NEITHER

    with pytest.raises(FileNotFoundError) as exc:
            Agent.from_toml(agent_file)

    assert "Skill 'target-skill' not found" in str(exc.value)
