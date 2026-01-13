"""
tests/vybz/test_artifact.py

Unit test suite for the ArtifactProcessor and Artifact domain model.
Validates parsing strategies, routing logic, and filesystem persistence.
"""
import pytest
import textwrap
from pathlib import Path
from vybz.artifact import Artifact, ArtifactProcessor


@pytest.fixture
def processor():
    """Returns a stateless ArtifactProcessor instance."""
    return ArtifactProcessor()


class TestArtifactParsing:
    """
    Validates the 'parse' contract: transforming raw LLM text into
    structured Artifact objects.
    """

    def test_parse_valid_design_block(self, processor):
        """Happy Path: Standard Markdown block with YAML frontmatter."""
        # Arrange
        llm_output = textwrap.dedent("""
        Here is the design:
        ```markdown
        ---
        type: Design
        ---
        # Login System
        The content.
        ```
        """)

        # Act
        artifact = processor.parse(llm_output)

        # Assert
        assert artifact.type == "Design"
        assert artifact.directory == "designs"
        assert artifact.filename == "login-system.md"
        assert "The content." in artifact.content

    def test_parse_fallback_raw_text(self, processor):
        """Sad Path: Agent forgets code blocks but provides valid YAML."""
        # Arrange
        raw_text = """---
type: Intent
---
# Raw Intent
Just raw text.
"""
        # Act
        artifact = processor.parse(raw_text)

        # Assert
        assert artifact.content == raw_text
        assert artifact.type == "Intent"
        assert artifact.directory == "intents"
        assert artifact.filename == "raw-intent.md"

    def test_parse_nested_blocks_bug(self, processor):
        """
        Regression Test: Ensure nested code blocks don't truncate the outer block.
        Reference: tests/vybz/test_repl_save_bug.py
        """
        # Arrange
        llm_output = """
Here is the document:
```markdown
---
type: Design
---
# Nested Test

## Section 1
Start.

## Code
```python
def hello():
    print("world")
```

## Section 3
End.
```
"""
        # Act
        artifact = processor.parse(llm_output)

        # Assert
        assert "def hello():" in artifact.content
        assert "## Section 3" in artifact.content, "Artifact truncated after inner block"

    def test_parse_filename_sanitization(self, processor):
        """Verify H1 titles are converted to safe kebab-case filenames."""
        # Arrange
        text = "```\n---\ntype: Design\n---\n# My Cool Feature! (v2)\n```"

        # Act
        artifact = processor.parse(text)

        # Assert
        assert artifact.filename == "my-cool-feature-v2.md"

    def test_parse_default_filename_timestamp(self, processor):
        """Verify fallback filename generation when H1 is missing."""
        # Arrange
        text = "```\n---\ntype: Design\n---\nNo header here.\n```"

        # Act
        artifact = processor.parse(text)

        # Assert
        assert artifact.filename.startswith("artifact-")
        assert artifact.filename.endswith(".md")

    @pytest.mark.parametrize("yaml_type, expected_dir", [
        ("Design", "designs"),
        ("Blueprint", "blueprints"),
        ("Intent", "intents"),
        ("Bug", "output"),    # Fallback for unknown types
        ("Unknown", "output")
    ])
    def test_parse_routing(self, processor, yaml_type, expected_dir):
        """Data-Driven Test: Verify routing logic based on YAML type."""
        text = f"```\n---\ntype: {yaml_type}\n---\n# Title\n```"
        artifact = processor.parse(text)
        assert artifact.directory == expected_dir


class TestArtifactPersistence:
    """
    Validates the 'save' contract: writing Artifact objects to disk.
    Uses 'tmp_path' to ensure tests are hermetic and do not touch real files.
    """

    def test_save_new_file(self, processor, tmp_path):
        """Verify saving a new file creates directories and content."""
        # Arrange
        artifact = Artifact(
            content="File Content",
            filename="test.md",
            directory="designs",
            type="Design"
        )

        # Act
        msg = processor.save(artifact, root_path=tmp_path)

        # Assert
        target_file = tmp_path / "designs" / "test.md"
        assert target_file.exists()
        assert target_file.read_text(encoding="utf-8").strip() == "File Content"
        assert "Saved Design" in msg

    def test_save_overwrite_existing(self, processor, tmp_path):
        """Verify overwriting an existing file returns specific feedback."""
        # Arrange
        artifact = Artifact(
            content="New Content",
            filename="overwrite.md",
            directory="intents",
            type="Intent"
        )

        # Pre-create the file
        target_dir = tmp_path / "intents"
        target_dir.mkdir()
        (target_dir / "overwrite.md").write_text("Old Content", encoding="utf-8")

        # Act
        msg = processor.save(artifact, root_path=tmp_path)

        # Assert
        target_file = target_dir / "overwrite.md"
        assert target_file.read_text(encoding="utf-8").strip() == "New Content"
        assert "Overwrote Intent" in msg

    def test_save_ensures_newline(self, processor, tmp_path):
        """Verify files are saved with a trailing newline (POSIX standard)."""
        # Arrange
        artifact = Artifact(
            content="No newline at end",
            filename="newline.md",
            directory="output",
            type="Output"
        )

        # Act
        processor.save(artifact, root_path=tmp_path)

        # Assert
        content = (tmp_path / "output" / "newline.md").read_text(encoding="utf-8")
        assert content.endswith("\n")
