"""
tests/vybz/test_repl_save_bug.py

Reproduction of the truncation bug in /save when dealing with nested code blocks.
"""
import pytest
from unittest.mock import MagicMock
from vybz.repl import ReplSession
from vybz.agent import Agent

def test_parse_artifact_truncates_nested_blocks(mock_genai_client):
    """
    Bug Confirmation:
    When the LLM generates a markdown block (e.g. Design) that contains
    internal code blocks (e.g. Python snippet), and uses the same number
    of backticks (3) for both, standard markdown parsers close the outer
    block at the end of the inner block.

    This test asserts that the 'Section 3' (text following the inner block)
    is preserved. Currently, this fails because markdown-it-py respects
    strict CommonMark rules which interpret the inner closing ticks as
    the end of the outer block.
    """
    # Arrange
    # Mock dependencies required for ReplSession init
    mock_agent = MagicMock(spec=Agent)
    mock_agent.name = "Test Agent"
    mock_agent.id = "test-agent"

    repl = ReplSession(
        client=mock_genai_client,
        agent=mock_agent,
        model_id="gemini-3-test"
    )

    # A simulated LLM response where the outer block uses 3 ticks
    # and the inner block also uses 3 ticks (common LLM behavior).
    llm_output = """
Here is the design doc you asked for:

```markdown
---
type: Design
---
# Nested Block Test

## Section 1
This is the start.

## Section 2
Here is some code:
```python
def hello():
    print("world")
```

## Section 3
This text is part of the design but gets cut off because the parser
thinks the previous ``` closed the file.
```

Hope that helps!
"""

    # Act
    content, directory, filename = repl._parse_artifact(llm_output)

    # Assert
    print(f"DEBUG: Parsed Content Length: {len(content)}")
    print(f"DEBUG: Parsed Content Tail: {content[-50:]}")

    # Verification 1: The inner code block should exist
    assert "def hello():" in content, "Inner code block missing"

    # Verification 2: The text AFTER the inner code block should exist
    # THIS ASSERTION WILL FAIL given the current implementation.
    assert "## Section 3" in content, "Artifact truncated after inner code block"
    assert "This text is part of the design" in content, "Trailing content lost"
