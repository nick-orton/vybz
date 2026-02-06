---
status: "Draft"
type: "Blueprint"
author: "Senior Python Architect"
last_updated: "2026-02-12"
references: blueprints/vybzd/vybzd-top-level-blueprint.md, designs/agentskills/agentskillsio-standard-phase-3-runtime.md, designs/load-file-functionality-specification.md
---

# Distributed Skill & Context Management (Back-to-Front)

This blueprint details the implementation of dynamic session 
mutation—specifically skill management (`/uplevel`, `/downlevel`, `/skills`) 
and surgical context injection (`/load`)—within the Client/Server architecture.

It follows a **Back-to-Front** implementation order: starting with the core 
Server State logic, moving to the FastAPI endpoints, and concluding with the 
Network Client API.

## 1. Goal
To enable session-scoped, ephemeral mutation of an Agent's capabilities and 
context. Changes made via these APIs affect only the active chat session and 
do not persist to the global Agent Library on disk.

## 2. Phase 1: Server State (`src/vybz/server/state.py`)

The server must transition from treating agents as static registry entries to 
session-scoped mutable entities.

### 2.1. Session State Initialization
Update `create_session` to clone the Vybz Agent definition into the session 
memory.
*   **Action:** Load the `VybzAgent` from TOML and store the object in 
    `session.state["vybz_agent"]`.
*   **Action:** Initialize `session.state["manual_context"] = {}` to store 
    files injected via the "load" functionality.

### 2.2. Mutation Logic
Implement the following methods in `ServerState`:

*   **`get_session_skills(session_id)`**: Returns the list of `Skill` objects 
    from the session-scoped agent.
*   **`uplevel_session_skill(session_id, skill_data)`**: 
    1. Instantiates a `VybzSkill` from the provided data.
    2. Calls `session.state["vybz_agent"].add_skill(skill)`.
    3. Triggers instruction refresh.
*   **`downlevel_session_skill(session_id, skill_id)`**:
    1. Calls `session.state["vybz_agent"].remove_skill(skill_id)`.
    2. Triggers instruction refresh.
*   **`load_session_context(session_id, filename, content)`**:
    1. Updates the `session.state["manual_context"]` dictionary.
    2. Triggers instruction refresh.

### 2.3. Instruction Refresh (`_refresh_session_instructions`)
A private helper to re-synchronize the ADK Agent with the mutated Vybz state.
*   **Logic:** Re-runs `ContextAssembler.build_system_instruction` using the 
    mutated agent and manual context, then updates `session.agent.instruction`.

## 3. Phase 2: Server API (`src/vybz/server/main.py`)

Expose the state mutations via REST endpoints.

### 3.1. DTO Definitions (Pydantic Models)
*   **`SkillDTO`**: `id`, `name`, `description`, `instructions`.
*   **`FileLoadDTO`**: `filename`, `content`.

### 3.2. Endpoints
*   **`GET /session/{id}/skills`**: Returns a list of active skills for the 
    session.
*   **`POST /session/{id}/skills/uplevel`**: Accepts `SkillDTO`.
*   **`POST /session/{id}/skills/downlevel`**: Accepts `{ "skill_id": str }`.
*   **`POST /session/{id}/load`**: Accepts `FileLoadDTO`.

## 4. Phase 3: Client API (`src/vybz/client/api.py`)

Extend the `VybzApiClient` to provide a clean interface for the future 
command layer.

### 4.1. New Client Methods
*   **`list_session_skills(session_id)`**: Returns a list of skill metadata.
*   **`uplevel_skill(session_id, skill_data)`**: Serializes and uploads a skill.
*   **`downlevel_skill(session_id, skill_id)`**: Requests removal of a skill.
*   **`load_file_content(session_id, filename, content)`**: Uploads raw file 
    content to the session context.

## 5. Senior Dev Peer Review

*   **Entropy Management:** This plan explicitly avoids modifying the global 
    registry. By "cloning" the agent into the session state, we ensure that 
    parallel sessions remain isolated.
*   **Context Persistence:** The "Load" functionality is correctly integrated 
    into the session state, ensuring it survives across multiple turns.
*   **Performance:** Sending full `instructions` strings for skills and 
    `content` for files is necessary for a headless server that cannot 
    see the client's local disk.

## 6. Verification Strategy

### 6.1. Server-Side Unit Tests
1. Initialize a session.
2. Call `uplevel_session_skill` with mock data.
3. Verify that the session's ADK agent instruction now contains the new skill.
4. Call `load_session_context` and verify the instruction contains the file.

### 6.2. API Integration Tests
1. Start `vybzd`.
2. Use `curl` or a test script to POST a skill to `/session/{id}/skills/uplevel`.
3. Verify a 200 OK response.
4. GET `/session/{id}/skills` and verify the new skill is present in the list.
