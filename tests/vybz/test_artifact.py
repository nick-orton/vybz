"""
tests/vybz/test_artifact.py

Unit test suite for the ArtifactProcessor and Artifact domain model.
Validates polymorphic parsing strategies, routing logic, and filesystem persistence.
"""
import pytest
import textwrap
from pathlib import Path
from vybz.commands.artifact import Artifact, ArtifactProcessor


@pytest.fixture
def processor():
    """Returns a stateless ArtifactProcessor instance."""
    return ArtifactProcessor()


class TestArtifactParsing:
    """
    Validates the 'parse' contract: transforming raw LLM text into
    a LIST of structured Artifact objects.
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
        artifacts = processor.parse(llm_output)

        # Assert
        assert len(artifacts) == 1
        artifact = artifacts[0]
        assert artifact.type == "Design"
        assert artifact.directory == ".vybz/designs"
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
        artifacts = processor.parse(raw_text)

        # Assert
        assert len(artifacts) == 1
        artifact = artifacts[0]
        assert artifact.content == raw_text
        assert artifact.type == "Intent"
        assert artifact.directory == ".vybz/intents"
        assert artifact.filename == "raw-intent.md"

    def test_parse_nested_blocks_bug(self, processor):
        """
        Regression Test: Ensure nested code blocks don't truncate the outer block.
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
        artifacts = processor.parse(llm_output)

        # Assert
        assert len(artifacts) == 1
        artifact = artifacts[0]
        assert "def hello():" in artifact.content
        assert "## Section 3" in artifact.content, "Artifact truncated after inner block"

    def test_parse_filename_sanitization(self, processor):
        """Verify H1 titles are converted to safe kebab-case filenames."""
        # Arrange
        text = "```\n---\ntype: Design\n---\n# My Cool Feature! (v2)\n```"

        # Act
        artifacts = processor.parse(text)

        # Assert
        assert artifacts[0].filename == "my-cool-feature-v2.md"

    def test_parse_default_filename_timestamp(self, processor):
        """Verify fallback filename generation when H1 is missing."""
        # Arrange
        text = "```\n---\ntype: Design\n---\nNo header here.\n```"

        # Act
        artifacts = processor.parse(text)

        # Assert
        assert artifacts[0].filename.startswith("artifact-")
        assert artifacts[0].filename.endswith(".md")

    @pytest.mark.parametrize("yaml_type, expected_dir", [
        ("Design", ".vybz/designs"),
        ("Blueprint", ".vybz/blueprints"),
        ("Intent", ".vybz/intents"),
        ("Bug", ".vybz/bugs"),
        ("Critique", ".vybz/critiques"),
        ("Unknown", ".vybz/output") # Fallback for unknown types
    ])
    def test_parse_routing(self, processor, yaml_type, expected_dir):
        """Data-Driven Test: Verify routing logic based on YAML type."""
        text = f"```\n---\ntype: {yaml_type}\n---\n# Title\n```"
        artifacts = processor.parse(text)
        assert artifacts[0].directory == expected_dir

    def test_parse_diff_block(self, processor):
        """Verify parsing of code blocks tagged as 'diff'."""
        # Arrange
        text = textwrap.dedent("""
        Here is the patch:
        ```diff
        --- a/src/vybz/client/ui.py
        +++ b/src/vybz/client/ui.py
        @@ -10,1 +10,1 @@
        - old
        + new
        ```
        """)

        # Act
        artifacts = processor.parse(text)

        # Assert
        assert len(artifacts) == 1
        artifact = artifacts[0]
        assert artifact.type == "Diff"
        assert artifact.filename == "src-vybz-client-ui.py.diff"
        assert artifact.directory == ".vybz/output"
        assert "+++ b/src/vybz/client/ui.py" in artifact.content

    def test_parse_extracts_multiple_artifacts(self, processor):
        """
        Verify that if a response contains multiple artifacts (Design, Diff, Code),
        ALL are extracted.
        """
        # Arrange
        text = textwrap.dedent("""
        Here is the design:
        ```markdown
        ---
        type: Design
        ---
        # My Feature
        ```
        And the code:
        ```diff
        --- a/file.py
        +++ b/file.py
        @@ -1,1 +1,1 @@
        -a
        +b
        ```
        And a script:
        ```python
        # filename: script.py
        print("hi")
        ```
        """)

        # Act
        artifacts = processor.parse(text)

        # Assert
        assert len(artifacts) == 3

        # Verify Types
        types = [a.type for a in artifacts]
        assert "Design" in types
        assert "Diff" in types
        assert "Code" in types

        # Verify Filenames
        filenames = [a.filename for a in artifacts]
        assert "my-feature.md" in filenames
        assert "file.py.diff" in filenames
        assert "script.py" in filenames

    def test_parse_bug_routing(self, processor):
        """
        Verify that artifacts with 'type: Bug' are correctly routed to the 'intents/' directory.
        """
        # Arrange
        text = textwrap.dedent("""
        Here is the bug report:
        ```markdown
        ---
        type: Bug
        status: Draft
        ---
        # UI Crash on Load
        Description of the crash...
        ```
        """)

        # Act
        artifacts = processor.parse(text)

        # Assert
        assert artifacts[0].type == "Bug"
        assert artifacts[0].directory == ".vybz/bugs"
        assert artifacts[0].filename == "ui-crash-on-load.md"


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
