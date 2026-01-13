"""
tests/vybz/test_skill.py

Unit tests for the Skill domain object.
"""
import pytest
from vybz.skill import Skill

def test_skill_from_toml_valid(temp_skills_dir):
    """
    Verify we can load a valid Skill TOML file.
    """
    # Arrange
    skill_file = temp_skills_dir / "test-skill.toml"
    toml_content = """
    name = "Test Skill"
    description = "A skill for testing."
    knowledge = ["Fact A", "Fact B"]
    abilities = ["Ability X"]
    """
    skill_file.write_text(toml_content, encoding="utf-8")

    # Act
    skill = Skill.from_toml(skill_file)

    # Assert
    assert skill.id == "test-skill"
    assert skill.name == "Test Skill"
    assert len(skill.knowledge) == 2
    assert "Ability X" in skill.abilities

def test_skill_from_toml_missing_file():
    """
    Verify FileNotFoundError is raised for non-existent files.
    """
    # Act & Assert
    with pytest.raises(FileNotFoundError):
        Skill.from_toml("non_existent_ghost_file.toml")

def test_skill_render(temp_skills_dir):
    """
    Verify the render method produces the expected Markdown format.
    """
    # Arrange
    skill = Skill(
        id="render-test",
        name="Render Test",
        description="Testing output",
        knowledge=["Knows Python"],
        abilities=["Can Code"]
    )

    # Act
    output = skill.render()

    # Assert
    assert "#### Render Test" in output
    assert "_Testing output_" in output
    assert "##### Knowledge" in output
    assert "* Knows Python" in output
    assert "##### Abilities" in output
    assert "* Can Code" in output
