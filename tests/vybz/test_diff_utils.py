"""
tests/vybz/test_diff_utils.py

Unit tests for the DiffSanitizer utility.
Validates heuristic repair of malformed diffs (missing context spaces)
and header recalculation using the unidiff library.
"""
import pytest
import textwrap
from vybz.tools.diff_utils import DiffSanitizer

class TestDiffSanitizer:
    """
    Validates the DiffSanitizer logic pipeline:
    1. Heuristic text repair (injecting missing spaces).
    2. Object model parsing & header recalculation.
    """

    def test_sanitize_recalculates_header(self):
        """
        Verify that incorrect hunk headers (bad arithmetic) are recalculated
        based on the actual content provided.
        """
        # Arrange: Header claims length 5 for both chunks, but actual content
        # is only 3 lines long (1 context + 1 change + 1 context).
        raw_diff = textwrap.dedent("""\
        --- a/file.py
        +++ b/file.py
        @@ -1,5 +1,5 @@
         def foo():
        -    print("old")
        +    print("new")
             return True""")

        # Act
        cleaned = DiffSanitizer.sanitize(raw_diff)

        # Assert
        # The sanitizer should parse the hunks and output the mathematically correct header.
        # -1,3 +1,3 matches the 3 lines of content.
        assert "@@ -1,3 +1,3 @@" in cleaned

    def test_sanitize_combined_repair(self):
        """
        Verify that the pipeline handles both missing spaces AND wrong headers
        in a single pass.
        """
        # Arrange: Missing spaces AND wrong header (claims 10 lines, has 3)
        raw_diff = textwrap.dedent("""\
        --- a/test.py
        +++ b/test.py
        @@ -10,10 +10,10 @@
        def bar():
        +    pass
        return None""")

        # Act
        cleaned = DiffSanitizer.sanitize(raw_diff)

        # Assert
        # 1. Spaces restored?
        assert " def bar():" in cleaned
        assert " return None" in cleaned
        # 2. Header fixed? (3 lines total)
        assert "@@ -10,2 +10,3 @@" in cleaned

    def test_sanitize_fail_open_on_garbage(self):
        """
        Verify that non-diff content (garbage) is returned raw without crashing.
        The sanitizer should log a warning but preserve the user's content.
        """
        # Arrange
        garbage = "This is just a random sentence.\nIt is not a diff.\n"

        # Act
        result = DiffSanitizer.sanitize(garbage)

        # Assert
        assert result == garbage

    def test_sanitize_multi_hunk_tracking(self):
        """
        Verify that the state machine correctly tracks 'inside hunk' status
        across multiple hunks in the same file.
        """
        raw_diff = textwrap.dedent("""\
        --- a/multi.py
        +++ b/multi.py
        @@ -1,3 +1,3 @@
        import os
        -import sys
        +import pathlib
        import re
        @@ -10,3 +10,3 @@
        def main():
        -    pass
        +    return 0
        if __name__ == "__main__":""")

        # Act
        cleaned = DiffSanitizer.sanitize(raw_diff)

        # Assert
        # Check context repair in the first hunk
        assert " import re" in cleaned
        # Check context repair in the second hunk
        assert " def main():" in cleaned
        assert " if __name__ == \"__main__\":" in cleaned

    def test_sanitize_respects_no_newline_marker(self):
        """
        Verify that the 'No newline at end of file' marker is NOT treated
        as a context line (i.e., it should NOT get a leading space).
        """
        raw_diff = textwrap.dedent("""\
        --- a/eof.py
        +++ b/eof.py
        @@ -1,1 +1,1 @@
        -print("Hi")
        +print("Bye")
        \\ No newline at end of file""")

        # Act
        cleaned = DiffSanitizer.sanitize(raw_diff)

        # Assert
        # Should remain starting with backslash
        assert "\\ No newline at end of file" in cleaned
        # Should NOT become " \ No newline..."
        assert " \\ No newline" not in cleaned

    def test_sanitize_ensures_final_newline(self):
        """
        Verify that the output always ends with a newline character,
        as required by POSIX patch utilities.
        """
        # Arrange: Diff without trailing newline
        raw_diff = textwrap.dedent("""\
        --- a/file.py
        +++ b/file.py
        @@ -1,1 +1,1 @@
         context""") # No \n at end

        # Act
        cleaned = DiffSanitizer.sanitize(raw_diff)

        # Assert
        assert cleaned.endswith("\n")
