---
status: "Completed"
type: "Blueprint"
author: "Senior Python Architect"
last_updated: "2026-02-15"
references: src/vybz/client/api.py, src/vybz/repl.py
---

# Vybz Engine Refactor - Step 4: Client Integration

This blueprint details the specific code changes required to wire the existing 
`VybzApiClient` (`src/vybz/client/api.py`) into the CLI application.

## 1. Goal
Replace the local `SessionManager` and synchronous execution loop in the CLI 
with an asynchronous architecture that delegates logic to the `vybzd` server 
via the API Client.

## 2. New Module: `src/vybz/client/session.py`

We need a client-side controller to manage the `VybzApiClient` lifecycle and 
hold UI-specific state (like the local `CodeBase` snapshot for the status bar).

### Class: `ClientSessionManager`
*   **Responsibilities:**
    *   Initialize the API client.
    *   Manage the active `session_id`.
    *   Maintain a local `active_agent` metadata object (for the prompt label).
    *   Maintain a local `codebase` object (for the context indicator).
*   **Methods:**
    *   `connect()`: Checks health.
    *   `initialize(agent_id, codebase_root)`: 
        *   Snapshots `CodeBase`.
        *   Calls `await client.start_session(agent_id, context_str)`.
    *   `chat(text)`: Yields from `client.chat_stream(text)`.
    *   `refresh_context()`: 
        *   Re-snapshots `CodeBase`.
        *   Calls `await client.update_context(...)`.
    *   `switch_agent(agent_id)`: 
        *   Calls `await client.start_session(...)` (New session).
        *   Updates local `active_agent` metadata.

## 3. Refactor: The Command Layer (`src/vybz/commands/`)

The command interface must become asynchronous to await API calls.

### 3.1. Abstract Base Class (`src/vybz/commands/base.py`)
*   **Change:** `def execute(...)` -> `async def execute(...)`.

### 3.2. Concrete Commands (`src/vybz/commands/core.py`)
*   **Update:** All commands must be updated to `async def`.
*   **Logic Updates:**
    *   `AgentCommand`: `await session.manager.switch_agent(...)`
    *   `UpdateCommand`: `await session.manager.refresh_context()`
    *   `UplevelCommand`: Read file locally -> `await session.manager.client.uplevel_skill(...)`
    *   `DownlevelCommand`: `await session.manager.client.downlevel_skill(...)`
    *   `LoadCommand`: Read file locally -> `await session.manager.client.load_file_content(...)`
    *   `SkillsCommand`: `await session.manager.client.list_session_skills(...)`

## 4. Refactor: The REPL (`src/vybz/repl.py`)

### 4.1. Class `ReplSession`
*   **Constructor:** Accepts `ClientSessionManager` instead of the old `SessionManager`.
*   **Method `start`:** Becomes `async def start(self)`.
*   **Loop Changes:**
    *   **Input:** `user_input = await self.session.prompt_async(...)` (Prompt Toolkit async method).
    *   **Commands:** `await self._handle_command(user_input)`.
    *   **Chat:** `await self._handle_input(user_input)`.
        *   Iterate: `async for chunk in self.session_manager.chat(text): ...`

## 5. Refactor: Entry Point (`src/vybz/tools/work.py`)

### 5.1. Async Bootstrap
*   Introduce `async def async_main():`.
*   **Interactive Branch:**
    1.  Instantiate `VybzApiClient`.
    2.  Instantiate `ClientSessionManager`.
    3.  `await manager.initialize(...)`.
    4.  Instantiate `ReplSession`.
    5.  `await session.start()`.
*   **Main Block:**
    *   `asyncio.run(async_main())`.

## 6. Execution Steps

1.  **Create:** `src/vybz/client/session.py`.
2.  **Refactor:** `src/vybz/commands/base.py` (Async Interface).
3.  **Refactor:** `src/vybz/commands/core.py` (Async Implementation).
4.  **Refactor:** `src/vybz/repl.py` (Async Loop).
5.  **Refactor:** `src/vybz/tools/work.py` (Async Entry).

## 7. Verification Strategy

### 7.1. Unit Tests
*   **Test:** `tests/vybz/client/test_client_session.py`
    *   Mock `VybzApiClient`.
    *   Verify `initialize` calls `client.start_session`.
*   **Test:** `tests/vybz/commands/test_async_core.py`
    *   Update existing command tests to be `pytest.mark.asyncio`.

### 7.2. Integration Check
*   **Pre-req:** `vybzd` must be running (`vybzd --reload`).
*   **Action:** `vybz junior-dev`.
*   **Verify:** 
    *   Connection successful.
    *   Prompt shows `junior-dev`.
    *   Chat works.
    *   `/agent pm` switches agent on server.
