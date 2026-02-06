"""
tests/vybz/test_skill.py

Unit tests for the Skill domain object.
"""
import pytest
from vybz.skill import Skill

def test_skill_render():
    """
    Verify the render method produces the expected Markdown format.
    """
    # Arrange
    skill = Skill(
        id="render-test",
        name="Render Test",
        description="Testing output",
        instructions="## Knowledge\n* Knows Python"
    )

    # Act
    output = skill.render()

    # Assert
    assert "#### Render Test" in output
    assert "_Testing output_" in output
    assert "## Knowledge" in output
    assert "* Knows Python" in output
