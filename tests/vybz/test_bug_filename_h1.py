"""
tests/vybz/test_bug_filename_h1.py

Reproduction Suite for Bug:
filename-generation-failure-for-artifacts-missing-h1-headers.md

Root Cause:
The DocumentHandler in src/vybz/commands/artifact.py uses a strict regex that
only matches Level 1 Markdown headers (`# Title`) for filename generation.
Agents like the QA Lead often output Level 2 headers (`## Title`), causing
the system to fallback to generic timestamped filenames.
"""
import pytest
import textwrap
from vybz.commands.artifact import ArtifactProcessor

def test_filename_extraction_should_support_h2_headers():
    """
    Prove that the current extraction logic fails to handle Level 2 headers,
    resulting in generic filenames (e.g., 'artifact-123456.md') instead of
    semantic ones.

    Target Behavior:
    Input: "## Login UI Crash"
    Expected Filename: "login-ui-crash.md"
    """
    # Arrange
    processor = ArtifactProcessor()

    # Simulate typical QA Agent output (using ## for the title)
    llm_output = textwrap.dedent("""
    Here is the bug report found during exploratory testing:

    ```markdown
    ---
    type: Bug
    status: Draft
    author: Principal QA Engineer
    ---
    ## Login UI Crash on invalid input

    ### Symptom
    The application throws a 500 error when...
    ```
    """)

    # Act
    artifacts = processor.parse(llm_output)

    # Verify we extracted an artifact
    assert len(artifacts) == 1
    artifact = artifacts[0]

    # Assert
    # This assertion will FAIL if the bug is present.
    # The current code returns 'artifact-{timestamp}.md'.
    # The desired code should return 'login-ui-crash-on-invalid-input.md'.
    expected_filename = "login-ui-crash-on-invalid-input.md"

    assert artifact.filename == expected_filename, (
        f"BUG PROVEN: Expected semantic filename '{expected_filename}', "
        f"but got generic fallback '{artifact.filename}'."
    )
