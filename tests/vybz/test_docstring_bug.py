"""
tests/vybz/test_docstring_bug.py

QA Regression Suite: Docstring Path Parsing
-------------------------------------------
This module characterizes a known defect in the ArtifactProcessor where
Python files using the project's own docstring convention are not correctly
routed to their destination.
"""
import pytest
import textwrap
from vybz.artifact import ArtifactProcessor

def test_docstring_convention_is_recognized_by_parser():
    """
    VERIFICATION OF FIX:
    Demonstrates that a Python code block using the Vybz Docstring convention

    is correctly identified as a 'Code' artifact and routed based on the path.
    """
    # Arrange
    processor = ArtifactProcessor()

    # Simulate an Agent outputting code that mimics src/vybz/commands/core.py style
    llm_output = textwrap.dedent("""
    Here is the implementation:

    ```python
    \"\"\"
    src/vybz/services/ghost.py

    This file uses the docstring convention for naming.
    \"\"\"
    def boo():
        return "ghost"
    ```
    """)

    # Act
    artifacts = processor.parse(llm_output)
    artifact = artifacts[0]

    # Assert: The Fix
    # 1. The CodeFileHandler should recognize the docstring pattern
    assert artifact.type == "Code", \
        "Parser failed to identify type as 'Code' (Bug still present?)"

    # 2. The directory should be 'src/vybz/services'
    assert artifact.directory == "src/vybz/services", \
        f"Parser incorrectly routed file to {artifact.directory}"

    # 3. The filename should be extracted correctly
    assert artifact.filename == "ghost.py"

def test_docstring_convention_should_extract_path():
    """
    TARGET BEHAVIOR:
    This test asserts how the system *should* behave.
    It is marked as xfail (Expected Failure) until the bug is fixed.
    """
    # Arrange
    processor = ArtifactProcessor()
    llm_output = textwrap.dedent("""
    ```python
    \"\"\"
    src/vybz/logic.py
    \"\"\"
    x = 1
    ```
    """)

    # Act
    artifacts = processor.parse(llm_output)
    artifact = artifacts[0]

    # Assert
    assert artifact.filename == "logic.py"
    assert artifact.directory == "src/vybz"
    assert artifact.type == "Code"
