"""
tests/vybz/test_diff_handler.py

Unit tests for the DiffHandler strategy class.
Verifies identification of diff blocks and filename extraction logic.
"""
import pytest
from unittest.mock import MagicMock, patch
from markdown_it.token import Token
from vybz.artifact import DiffHandler

class TestDiffHandler:
    """
    Tests for the DiffHandler class in src/vybz/artifact.py
    """

    @pytest.fixture
    def handler(self):
        return DiffHandler()

    @pytest.mark.parametrize("info_string", ["diff", "patch", "DIFF", "PATCH "])
    def test_can_handle_valid_tokens(self, handler, info_string):
        """Verify it accepts standard diff/patch tags, case-insensitive."""
        token = MagicMock(spec=Token)
        token.type = "fence"
        token.info = info_string
        assert handler.can_handle(token) is True

    @pytest.mark.parametrize("info_string", ["python", "", "markdown", "text"])
    def test_can_handle_invalid_info(self, handler, info_string):
        """Verify it rejects non-diff code blocks."""
        token = MagicMock(spec=Token)
        token.type = "fence"
        token.info = info_string
        assert handler.can_handle(token) is False

    def test_can_handle_wrong_type(self, handler):
        """Verify it rejects non-fence tokens."""
        token = MagicMock(spec=Token)
        token.type = "inline"
        token.info = "diff"
        assert handler.can_handle(token) is False

    @patch("vybz.diff_utils.DiffSanitizer")
    def test_extract_valid_diff(self, MockSanitizer, handler):
        """
        Happy Path: Verify extraction logic.
        1. Calls sanitizer.
        2. Extracts filename from '+++ b/' header.
        3. Flattens path structure in filename.
        """
        # Arrange
        raw_content = "--- a/src/vybz/agent.py\n+++ b/src/vybz/agent.py\n@@ -1,1 +1,1 @@"
        token = MagicMock(spec=Token)
        token.content = raw_content

        MockSanitizer.sanitize.return_value = "Sanitized Content"

        # Act
        artifact = handler.extract(token, "ignored_full_text")

        # Assert
        assert artifact.type == "Diff"
        assert artifact.directory == "output"
        # Verify path flattening: / -> -
        assert artifact.filename == "src-vybz-agent.py.diff"
        assert artifact.content == "Sanitized Content"

        # Verify Sanitizer was invoked
        MockSanitizer.sanitize.assert_called_with(raw_content)

    @patch("vybz.artifact.datetime")
    @patch("vybz.diff_utils.DiffSanitizer")
    def test_extract_fallback_filename(self, MockSanitizer, mock_dt, handler):
        """
        Edge Case: Verify fallback filename generation when diff header is missing.
        """
        # Arrange
        content = "@@ -1,1 +1,1 @@\n-old\n+new" # No '+++ b/' header
        token = MagicMock(spec=Token)
        token.content = content

        MockSanitizer.sanitize.return_value = content
        # Mock time for deterministic filename
        mock_dt.datetime.now.return_value.strftime.return_value = "123456"

        # Act
        artifact = handler.extract(token, "")

        # Assert
        assert artifact.filename == "patch-123456.diff"
        assert artifact.type == "Diff"
