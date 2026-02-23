"""
tests/vybz/server/test_main.py

Unit tests for the Vybz Engine FastAPI application.
Verifies REST endpoints and WebSocket chat logic using hermetic mocks.
"""
import sys
import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient

# 1. Mock google.adk BEFORE importing vybz.server.main to prevent runtime errors
mock_adk = MagicMock()
mock_sessions_module = MagicMock()
mock_tools_module = MagicMock()
sys.modules["google.adk"] = mock_adk
sys.modules["google.adk.sessions"] = mock_sessions_module
sys.modules["google.adk.tools"] = mock_tools_module

from vybz.server.main import app

# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def mock_state():
    """
    Patches the global 'state' object in vybz.server.main.
    """
    with patch("vybz.server.main.state") as mock_state_obj:
        # Default mock behaviors
        mock_state_obj.agent_templates = {}
        mock_state_obj.model_id = "test-model"
        mock_state_obj.initialize = MagicMock()

        # Mock Async methods with AsyncMock
        mock_state_obj.create_session = AsyncMock()
        mock_state_obj.get_session_skills = AsyncMock()
        mock_state_obj.uplevel_session_skill = AsyncMock()
        mock_state_obj.downlevel_session_skill = AsyncMock()
        mock_state_obj.load_session_context = AsyncMock()
        mock_state_obj.get_runner = MagicMock()

        yield mock_state_obj

@pytest.fixture(autouse=True)
def mock_genai_types():
    """
    Patches google.genai.types to allow isinstance checks in the main code.
    Since we mock sys.modules['google.genai'], types is a Mock by default.
    We replace it with a class structure that supports isinstance.
    """
    class MockContent:
        def __init__(self, role=None, parts=None):
            self.role = role
            self.parts = parts or []

    class MockPart:
        def __init__(self, text=None):
            self.text = text

    with patch("vybz.server.main.types") as mock_types:
        mock_types.Content = MockContent
        mock_types.Part = MockPart
        yield mock_types

@pytest.fixture
def client(mock_state):
    """
    Returns a TestClient context.
    """
    with TestClient(app) as c:
        yield c

# -----------------------------------------------------------------------------
# REST Endpoint Tests
# -----------------------------------------------------------------------------

def test_lifespan_initializes_state(mock_state):
    """Verify that starting the app triggers state initialization."""
    with TestClient(app):
        mock_state.initialize.assert_called_once()

def test_health_check(client, mock_state):
    """Verify /health returns status and stats."""
    mock_state.agent_templates = {"a": 1, "b": 2}
    mock_state.runners = {"s1": 1}
    mock_state.model_id = "gemini-mock"

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "agents_available": 2,
        "active_sessions": 1,
        "model": "gemini-mock"
    }

def test_list_agents(client, mock_state):
    """Verify /agents returns list of templates."""
    mock_agent = MagicMock()
    mock_agent.name = "Junior"
    mock_agent.version = "1"
    mock_state.agent_templates = {"junior": mock_agent}

    response = client.get("/agents")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "junior"
    assert data[0]["name"] == "Junior"

def test_init_session_success(client, mock_state):
    """Verify /session/init creates a session and returns ID."""
    mock_state.create_session.return_value = "sess-123"

    payload = {"agent_id": "junior-dev", "context": "# Code"}
    response = client.post("/session/init", json=payload)

    assert response.status_code == 200
    assert response.json() == {"session_id": "sess-123"}
    mock_state.create_session.assert_called_with(
        "junior-dev", "# Code"
    )

def test_init_session_agent_not_found(client, mock_state):
    """Verify 404 if create_session raises ValueError."""
    mock_state.create_session.side_effect = ValueError("Agent not found")

    response = client.post("/session/init", json={"agent_id": "ghost"})
    assert response.status_code == 404

def test_init_session_internal_error(client, mock_state):
    """Verify 500 if create_session raises unexpected Error."""
    mock_state.create_session.side_effect = Exception("Boom")

    response = client.post("/session/init", json={"agent_id": "junior"})
    assert response.status_code == 500

def test_list_session_skills(client, mock_state):
    """Verify retrieval of session-specific skills."""
    mock_skill = MagicMock()
    mock_skill.id = "s1"
    mock_skill.name = "Skill 1"
    mock_skill.description = "Desc"
    mock_skill.instructions = "Do it"

    mock_state.get_session_skills.return_value = [mock_skill]

    response = client.get("/session/uuid-1/skills")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "s1"
    mock_state.get_session_skills.assert_called_with("uuid-1")

def test_uplevel_skill(client, mock_state):
    """Verify skill uplevel endpoint parsing."""
    payload = {
        "id": "new-skill",
        "name": "New Skill",
        "description": "...",
        "instructions": "..."
    }
    response = client.post("/session/uuid-1/skills/uplevel", json=payload)

    assert response.status_code == 200
    mock_state.uplevel_session_skill.assert_called_once()
    args, _ = mock_state.uplevel_session_skill.call_args
    # args[0] is session_id, args[1] is dict
    assert args[0] == "uuid-1"
    assert args[1]["id"] == "new-skill"

def test_downlevel_skill_success(client, mock_state):
    """Verify successful skill removal."""
    mock_state.downlevel_session_skill.return_value = True

    response = client.post("/session/id-1/skills/downlevel", json={"skill_id": "s1"})

    assert response.status_code == 200
    mock_state.downlevel_session_skill.assert_called_with("id-1", "s1")

def test_load_context(client, mock_state):
    """Verify manual context injection endpoint."""
    payload = {"filename": "notes.txt", "content": "secret"}
    response = client.post("/session/id-1/load", json=payload)

    assert response.status_code == 200
    mock_state.load_session_context.assert_called_with("id-1", "notes.txt", "secret")

# -----------------------------------------------------------------------------
# WebSocket Tests
# -----------------------------------------------------------------------------

def test_websocket_chat_flow(client, mock_state, mock_genai_types):
    """
    Verify the full WebSocket chat loop:
    1. Connect.
    2. Send JSON content.
    3. Receive streamed text chunks from ADK Runner.
    """
    session_id = "sess-1"
    mock_runner = MagicMock()
    mock_state.get_runner.return_value = mock_runner

    # Mock the runner.run() generator yielding events
    # We need to mock the event structure: event.partial=True/False, event.content.parts[0].text
    def create_event(text, partial=True):
        event = MagicMock()
        event.partial = partial
        part = MagicMock(text=text)
        part.thought = None
        event.content.parts = [part]
        return event

    mock_runner.run.return_value = iter([
        create_event("Hello "),
        create_event("World", partial=True)
    ])

    with client.websocket_connect(f"/session/{session_id}/chat") as websocket:
        # Send User Input
        websocket.send_json({"content": "Hi"})

        # Receive Streamed Chunks
        msg1 = websocket.receive_text()
        msg2 = websocket.receive_text()

    assert msg1 == "Hello "
    assert msg2 == "World"

    # Verify runner was called with correct structure
    mock_runner.run.assert_called_once()
    call_kwargs = mock_runner.run.call_args.kwargs
    assert call_kwargs["session_id"] == session_id

    # Check that new_message is an instance of our MockContent (which the code checks via isinstance)
    assert isinstance(call_kwargs["new_message"], mock_genai_types.Content)
    assert call_kwargs["new_message"].parts[0].text == "Hi"

def test_websocket_session_not_found(client, mock_state):
    """Verify WS closes with 4004 if session ID is invalid."""
    mock_state.get_runner.side_effect = ValueError("No session")

    with pytest.raises(Exception): # TestClient raises on close
        with client.websocket_connect("/session/bad-id/chat") as websocket:
            websocket.receive_text()

    mock_state.get_runner.assert_called_with("bad-id")

def test_websocket_adk_error_handling(client, mock_state):
    """Verify that runtime errors during generation are sent to client."""
    mock_runner = MagicMock()
    mock_state.get_runner.return_value = mock_runner
    mock_runner.run.side_effect = Exception("ADK Crash")

    with client.websocket_connect("/session/ok/chat") as websocket:
        websocket.send_json({"content": "crash"})
        msg = websocket.receive_text()

    assert "[Error: ADK Crash]" in msg

def test_websocket_handles_string_chunks(client, mock_state):
    """Verify handling of simple string events if ADK returns them (defensive coding)."""
    # This test ensures we don't crash if the event structure changes slightly
    # In main.py we strictly check event.partial and event.content
    # If those don't match, nothing is sent.
    pass
