"""
tests/conftest.py

Global pytest configuration and fixtures.
"""
import sys
import os
from pathlib import Path
import pytest

# 1. Path Manipulation
# Ensure 'src' is in python path so we can import 'vybz'
# This allows running tests without `pip install -e .`
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

@pytest.fixture
def mock_genai_client(mocker):
    """
    Mocks the Google GenAI Client to prevent actual API calls.
    """
    mock_client = mocker.Mock()
    # Mock the chat session creation
    mock_chat = mocker.Mock()
    mock_client.chats.create.return_value = mock_chat
    
    return mock_client

@pytest.fixture
def temp_skills_dir(tmp_path):
    """
    Creates a temporary directory structure for testing skill loading.
    Returns the Path object to the 'skills' directory.
    """
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    return skills_dir
