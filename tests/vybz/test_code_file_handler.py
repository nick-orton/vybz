"""
tests/vybz/test_code_file_handler.py

Unit tests for the CodeFileHandler strategy class.
Verifies identification of code blocks with explicit filename metadata
and the correct routing of those files.
"""
import pytest
import textwrap
from unittest.mock import MagicMock
from markdown_it.token import Token
from vybz.commands.artifact import CodeFileHandler

class TestCodeFileHandler:
    """
    Tests for the CodeFileHandler class in src/vybz/commands/artifact.py
    """

    @pytest.fixture
    def handler(self):
        return CodeFileHandler()

    # -------------------------------------------------------------------------
    # Recognition Tests (can_handle)
    # -------------------------------------------------------------------------

    @pytest.mark.parametrize("comment_style, path", [
        ("#", "src/main.py"),
        ("//", "src/utils.js"),
        ("#", "script.sh"),
    ])
    def test_can_handle_valid_filename_patterns(self, handler, comment_style, path):
        """Verify it recognizes blocks containing 'filename: path' comments."""
        content = f"{comment_style} filename: {path}\ncode()"
        token = MagicMock(spec=Token)
        token.type = "fence"
        token.content = content

        assert handler.can_handle(token) is True

    def test_can_handle_case_insensitive_label(self, handler):
        """Verify it accepts 'File:' or 'Filename:'."""
        content = "# File: test.py\npass"
        token = MagicMock(spec=Token)
        token.type = "fence"
        token.content = content

        assert handler.can_handle(token) is True

    def test_can_handle_rejects_diffs(self, handler):
        """Verify it ignores blocks that look like diffs (handled by DiffHandler)."""
        content = "--- a/foo\n+++ b/foo"
        token = MagicMock(spec=Token)
        token.type = "fence"
        token.content = content
        token.info = "diff"

        assert handler.can_handle(token) is False

    # -------------------------------------------------------------------------
    # Extraction Tests (extract)
    # -------------------------------------------------------------------------

    def test_extract_python_file(self, handler):
        """
        Verify extraction of a Python file.
        Should extract directory 'src/vybz' and filename 'core.py'.
        """
        # Arrange
        raw_content = textwrap.dedent("""
        # filename: src/vybz/core.py
        def main():
            print("Hello")
        """)
        token = MagicMock(spec=Token)
        token.content = raw_content

        # Act
        artifact = handler.extract(token, "")

        # Assert
        assert artifact.filename == "core.py"
        assert artifact.directory == "src/vybz"
        assert artifact.type == "Code"
        # Ensure content is preserved
        assert 'print("Hello")' in artifact.content

    def test_extract_root_file(self, handler):
        """Verify files at root (no directory prefix) map to current directory."""
        # Arrange
        raw_content = textwrap.dedent("""
        # filename: README.md
        # Title
        """)
        token = MagicMock(spec=Token)
        token.content = raw_content

        # Act
        artifact = handler.extract(token, "")

        # Assert
        assert artifact.filename == "README.md"
        assert artifact.directory == "."
        assert artifact.type == "Code"
