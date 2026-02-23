"""
tests/vybz/test_agent.py

Unit tests for the Agent domain object.
Verifies loading logic, specifically the dual-path skill resolution strategy.
"""
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from vybz.shared.skill import Skill
from vybz.shared.agent import Agent

@pytest.fixture
def mock_skill_class():
    """Mocks the Skill class to verify factory calls."""
    with patch("vybz.shared.agent.Skill") as MockSkill:
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

    with patch.object(vybz.shared.agent, "__file__", str(fake_agent_py)):
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
from vybz.shared.agent import Agent

@pytest.fixture
def mock_skill_class():
    """Mocks the Skill class to verify factory calls."""
    with patch("vybz.shared.agent.Skill") as MockSkill:
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

def test_agent_load_skill_success(agent_env, mock_skill_class):
    """
    Verify that an agent loads skills via the Library
    """
    agent_file, v2_dir = agent_env

    # Arrange: Create V2 Skill
    (v2_dir / "target-skill").mkdir()
    (v2_dir / "target-skill" / "SKILL.md").touch()


    mock_library = MagicMock()
    mock_library.get_skill_path.return_value = v2_dir / "target-skill"

    Agent.from_toml(agent_file, library=mock_library)

    # Assert
    mock_skill_class.from_directory.assert_called_once()
    mock_library.get_skill_path.assert_called_with("target-skill")

def test_agent_load_missing_skill(agent_env, mock_skill_class):
    """
    Verify FileNotFoundError if Library fails to resolve skill.
    """
    agent_file, v2_dir = agent_env

    # Arrange: Create NEITHER
    mock_library = MagicMock()
    mock_library.get_skill_path.side_effect = FileNotFoundError("Skill 'target-skill' not found")

    with pytest.raises(FileNotFoundError) as exc:
            Agent.from_toml(agent_file, library=mock_library)

    assert "Skill 'target-skill' not found" in str(exc.value)

def test_agent_add_skill_lifecycle():
    """Verify adding and updating skills on an Agent instance."""
    # Arrange
    agent = Agent(
        id="test-agent", name="Tester", version="1",
        role_spec="", operating_context="", task_directive=""
    )
    skill_v1 = Skill(id="python", name="Python", description="v1", instructions="print(1)")
    skill_v2 = Skill(id="python", name="Python", description="v2", instructions="print(2)")

    # Act: Add new skill
    agent.add_skill(skill_v1)

    # Assert
    assert len(agent.skills) == 1
    assert agent.skills[0].description == "v1"

    # Act: Update existing skill (ID match)
    agent.add_skill(skill_v2)

    # Assert: Should not duplicate, should update content
    assert len(agent.skills) == 1
    assert agent.skills[0].description == "v2"

def test_agent_remove_skill_lifecycle():
    """Verify removing skills from an Agent instance and boolean feedback."""
    # Arrange
    s1 = Skill(id="s1", name="S1", description="", instructions="")
    agent = Agent(id="test", name="T", version="1", role_spec="", operating_context="", task_directive="", skills=[s1])

    # Act & Assert
    assert agent.remove_skill("s1") is True
    assert len(agent.skills) == 0

    # Act & Assert: Remove non-existent
    assert agent.remove_skill("ghost") is False
