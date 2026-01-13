---
status: "Completed"
type: "Blueprint"
last_updated: "2026-01-12"
references: designs/unit-testing-architecture.md
---

# Unit Testing Pilot Implementation

This blueprint details the setup of the testing harness and the creation of the
first unit test for the `Skill` domain object.

## 1. Dependencies
*   **Action:** Update `pyproject.toml`.
*   **Add:** `pytest`, `pytest-mock`.

## 2. Configuration: `tests/conftest.py`
*   **Purpose:** Configure the test environment.
*   **Logic:**
    *   Add `src` to `sys.path` so tests can import `vybz` modules without 
        installation quirks.
    *   Define a `mock_genai_client` fixture (even if not used in the pilot, 
        it's critical for the framework).

## 3. Pilot Test: `tests/vybz/test_skill.py`
*   **Target:** `src/vybz/skill.py`.
*   **Test Cases:**
    *   `test_skill_load_valid`: Create a dummy TOML file using `tmp_path`, 
        load it, verify attributes.
    *   `test_skill_load_missing`: Verify `FileNotFoundError`.
    *   `test_skill_render`: Verify the markdown output string contains 
        expected headers.

## 4. Verification
*   Run `pytest` from the project root.
*   Expect: 3 passed tests.
```

---

### Code Generation (The Delta)

#### 1. Update `pyproject.toml`
*Adding the testing dependencies.*

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "vybz"
version = "0.1.0"
description = "AI-Orchestrated Vibe Coding Workbench"
readme = "README.md"
requires-python = ">=3.11"
authors = [
  { name = "Vybz Team", email = "vybz@orton.info" },
]
classifiers = [
    "Programming Language :: Python :: 3",
    "Operating System :: POSIX :: Linux",
    "Operating System :: POSIX :: BSD",
]
dependencies = [
    "google-genai>=1.57",
    "markdown-it-py>=3.0.0", 
    "python-dotenv",
    "pathspec>=0.11.0",
    "prompt_toolkit>=3.0.0", 
    "rich>=13.0",
    "pytest>=7.0",       # <--- ADDED
    "pytest-mock>=3.10", # <--- ADDED
]

[project.scripts]
vybz = "vybz.tools.work:main"
vybz-commit = "vybz.tools.autocommit_gen:main"
vybz-fmt = "vybz.tools.mdformat:main"

[tool.setuptools.package-data]
vybz = ["agents/*.toml", "agents/skills/*.toml"]

[tool.pytest.ini_options]
minversion = "6.0"
addopts = "-ra -q"
testpaths = [
    "tests",
]
```

#### 2. Create `tests/conftest.py`
*Setting up the environment and global mocks.*

```python
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
```

#### 3. Create `tests/vybz/test_skill.py`
*The Pilot Test.*

```python
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
```

### Senior Dev Peer Review & Verification

*   **Structure:** The tests are isolated in `tests/`, keeping `src/` clean.
*   **Safety:** We utilize `tmp_path` (a pytest builtin) to create temporary TOML files. This ensures we don't accidentally rely on the real `src/vybz/agents/skills` folder, which might change and break tests.
*   **Coverage:** We cover the Happy Path (Valid TOML), the Sad Path (Missing File), and the Output Logic (Render).
