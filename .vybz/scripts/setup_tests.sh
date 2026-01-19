#!/bin/sh
# setup_tests.sh
# Automates the creation of the Vybz Unit Testing Infrastructure.
# POSIX compliant (FreeBSD/Linux).

set -e # Exit on error

echo ">> 1. Creating directory structure..."
mkdir -p tests/vybz
echo "   [OK] Created tests/vybz/"

echo ">> 2. Generating tests/conftest.py..."
cat << 'EOF' > tests/conftest.py
"""
tests/conftest.py

Global pytest configuration and fixtures.
"""
import sys
import os
from pathlib import Path
import pytest

# 1. Path Manipulation
# Ensure 'src' is in python path so we can import 'vybz'
# This allows running tests without `pip install -e .`
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

@pytest.fixture
def mock_genai_client(mocker):
    """
    Mocks the Google GenAI Client to prevent actual API calls.
    """
    mock_client = mocker.Mock()
    # Mock the chat session creation
    mock_chat = mocker.Mock()
    mock_client.chats.create.return_value = mock_chat
    
    return mock_client

@pytest.fixture
def temp_skills_dir(tmp_path):
    """
    Creates a temporary directory structure for testing skill loading.
    Returns the Path object to the 'skills' directory.
    """
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    return skills_dir
EOF
echo "   [OK] Written tests/conftest.py"

echo ">> 3. Generating tests/vybz/test_skill.py..."
cat << 'EOF' > tests/vybz/test_skill.py
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
EOF
echo "   [OK] Written tests/vybz/test_skill.py"

echo ">> 4. Updating pyproject.toml dependencies..."
if [ ! -f "pyproject.toml" ]; then
    echo "   [ERROR] pyproject.toml not found in current directory."
    exit 1
fi

# Check if pytest is already there to avoid duplicates
if grep -q "pytest" pyproject.toml; then
    echo "   [SKIP] pytest already present in pyproject.toml."
else
    # Use awk to insert dependencies after the opening bracket of dependencies = [
    # This is safer than sed across different OS versions (BSD vs GNU)
    awk '/dependencies = \[/ { print; print "    \"pytest>=7.0\","; print "    \"pytest-mock>=3.10\","; next }1' pyproject.toml > pyproject.toml.tmp && mv pyproject.toml.tmp pyproject.toml
    echo "   [OK] Injected pytest and pytest-mock into pyproject.toml"
fi

echo ""
echo "--------------------------------------------------------"
echo "Setup Complete."
echo "Run the following to install dependencies and run tests:"
echo "  pip install -e ."
echo "  pytest"
echo "--------------------------------------------------------"
