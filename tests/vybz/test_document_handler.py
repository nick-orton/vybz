"""
tests/vybz/test_document_handler.py

Unit tests for the DocumentHandler strategy class.
Verifies parsing of YAML frontmatter, directory routing, and nested block extraction.
"""
import pytest
import textwrap
from unittest.mock import MagicMock, patch
from markdown_it.token import Token
from vybz.commands.artifact import DocumentHandler

class TestDocumentHandler:
    """
    Tests for the DocumentHandler class in src/vybz/commands/artifact.py
    """

    @pytest.fixture
    def handler(self):
        return DocumentHandler()

    # -------------------------------------------------------------------------
    # Recognition Tests (can_handle)
    # -------------------------------------------------------------------------

    def test_can_handle_valid_yaml(self, handler):
        """Verify it accepts blocks with '---' and 'type:'."""
        token = MagicMock(spec=Token)
        token.type = "fence"
        token.content = "---\ntype: Design\n---"
        assert handler.can_handle(token) is True

    def test_can_handle_case_insensitive_type(self, handler):
        """Verify it accepts 'Type:'."""
        token = MagicMock(spec=Token)
        token.type = "fence"
        token.content = "---\nType: Blueprint\n---"
        assert handler.can_handle(token) is True

    def test_can_handle_rejects_missing_type(self, handler):
        """Verify it rejects YAML blocks that lack a 'type' field."""
        token = MagicMock(spec=Token)
        token.type = "fence"
        token.content = "---\nkey: value\n---"
        assert handler.can_handle(token) is False

    def test_can_handle_rejects_non_yaml(self, handler):
        """Verify it rejects standard code blocks."""
        token = MagicMock(spec=Token)
        token.type = "fence"
        token.content = "print('hello')"
        assert handler.can_handle(token) is False

    # -------------------------------------------------------------------------
    # Extraction Tests (extract)
    # -------------------------------------------------------------------------

    def test_extract_happy_path(self, handler):
        """
        Verify standard extraction:
        1. Parse Type -> Directory.
        2. Parse H1 -> Filename.
        """
        # Arrange
        content = textwrap.dedent("""
        ---
        type: Design
        ---
        # My Feature
        Content...
        """)
        token = MagicMock(spec=Token)
        token.content = content
        token.map = None # No map provided, use token content directly

        # Act
        artifact = handler.extract(token, "full_text_ignored")

        # Assert
        assert artifact.type == "Design"
        assert artifact.directory == ".vybz/designs"
        assert artifact.filename == "my-feature.md"
        assert artifact.content == content

    @pytest.mark.parametrize("yaml_type, expected_dir", [
        ("Design", ".vybz/designs"),
        ("Blueprint", ".vybz/blueprints"),
        ("Intent", ".vybz/intents"),
        ("Bug", ".vybz/bugs"),
        ("Critique", ".vybz/critiques"),
        ("UnknownType", ".vybz/output") # Fallback
    ])
    def test_extract_routing(self, handler, yaml_type, expected_dir):
        """Verify the routing table logic."""
        content = f"---\ntype: {yaml_type}\n---\n# Title"
        token = MagicMock(spec=Token)
        token.content = content
        token.map = None

        artifact = handler.extract(token, "")
        assert artifact.directory == expected_dir

    def test_extract_filename_sanitization(self, handler):
        """Verify robust filename generation from H1 headers."""
        content = "---\ntype: Design\n---\n# My Cool Feature! (v2.0) "
        token = MagicMock(spec=Token)
        token.content = content
        token.map = None

        artifact = handler.extract(token, "")
        # Expect: lowercase, spaces to dashes, non-alphanumeric removed
        assert artifact.filename == "my-cool-feature-v20.md"

    @patch("vybz.commands.artifact.datetime")
    def test_extract_fallback_filename(self, mock_dt, handler):
        """Verify fallback filename when no H1 header is present."""
        content = "---\ntype: Design\n---\nNo header here."
        token = MagicMock(spec=Token)
        token.content = content
        token.map = None

        mock_dt.datetime.now.return_value.strftime.return_value = "123456"

        artifact = handler.extract(token, "")
        assert artifact.filename == "artifact-123456.md"

    def test_extract_nested_blocks(self, handler):
        """
        Critical Regression Test: Verify that if the artifact contains nested
        code fences (e.g. a Design doc showing python code), the extraction
        captures the *outer* block correctly using the token map.
        """
        # Arrange: Construct a full text with nested fences
        full_text_lines = [
            "Preamble",
            "```markdown",          # Line 1 (Start of artifact)
            "---",
            "type: Design",
            "---",
            "# Nested Test",
            "",
            "## Code Example",
            "```python",            # Nested start
            "def foo(): pass",
            "```",                  # Nested end
            "End of doc.",
            "```",                  # Line 12 (End of artifact)
            "Postscript"
        ]
        full_text = "\n".join(full_text_lines)

        token = MagicMock(spec=Token)
        # Token map points to start line of the block (Line 1)
        token.map = [1, 12]
        # markdown-it usually strips the outer fences in .content,
        # but the handler logic re-extracts from full_text if .map exists
        token.content = "Placeholder"

        # Act
        artifact = handler.extract(token, full_text)

        # Assert
        # The content should include the inner python block
        assert "```python" in artifact.content
        assert "def foo(): pass" in artifact.content
        assert "End of doc." in artifact.content

        # It should NOT include the outer fences (handled by logic logic)
        # Note: The logic in DocumentHandler.extract constructs it via slicing lines
        assert artifact.content.startswith("---")
