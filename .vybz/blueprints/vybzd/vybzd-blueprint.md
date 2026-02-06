---
status: "Draft"
type: "Blueprint"
author: "Senior Python Architect"
last_updated: "2026-02-06"
references: designs/vybzd.md, intents/vybzd.md
---

# Vybz Engine Refactor: ADK Client/Server Architecture

This blueprint details the architectural transformation of Vybz from a 
monolithic CLI tool into a distributed Client/Server system powered by the 
**Google Agent Development Kit (ADK)**.

## 1. Architectural Vision

We are decoupling the **Execution Environment** (The Brain) from the 
**User Interface** (The Terminal).

### 1.1. The Separation of Concerns
*   **`vybzd` (Server):** A headless, long-running service responsible for:
    *   Hosting the ADK `ModelRuntime`.
    *   Managing Agent state and Chat History via ADK Sessions.
    *   Loading the Agent Library (TOML/Skills) and hydrating them into ADK 
        objects.
*   **`vybz-cli` (Client):** A lightweight TUI responsible for:
    *   Capturing user input (Prompt Toolkit).
    *   Rendering output (Rich).
    *   Snapshotting the local filesystem (`CodeBase`) and transmitting it to 
        the engine as context.

### 1.2. Communication Protocol
*   **Transport:** HTTP/1.1 (REST) for control messages; WebSockets for 
    real-time chat streaming.
*   **Serialization:** JSON / Pydantic models.

## 2. Phase 1: Shared Domain & ADK Adapter

We must create a translation layer that converts Vybz's proprietary 
configuration formats into ADK-compatible objects.

### 2.1. Module: `src/vybz/shared/`
Move core domain logic here to be accessible by both Client and Server.
*   `vybz.library` (The file readers).
*   `vybz.context_engine` (CodeBase snapshotting).

### 2.2. Module: `src/vybz/server/adapter.py`
*   **Class `AdkHydrator`:**
    *   **Input:** `vybz.agent.Agent` (The TOML data class).
    *   **Output:** `google.adk.Agent`.
    *   **Logic:**
        1.  Construct the `system_prompt` by combining `role_spec`, 
            `operating_context`, and `task_directive` (reusing 
            `Agent.construct_agent_role_profile`).
        2.  *Future:* Map `Skill` scripts to `google.adk.Tool` definitions.

## 3. Phase 2: The Engine (Server Implementation)

### 3.1. Dependencies
*   Add `fastapi`, `uvicorn`, `google-adk` to `pyproject.toml`.

### 3.2. Server Core: `src/vybz/server/main.py`
*   **Initialization:**
    1.  Load `Squad` using `vybz.library`.
    2.  Hydrate all Agents into an `AgentRegistry`.
    3.  Initialize `adk.ModelRuntime`.
*   **Endpoints:**
    *   `GET /agents`: List available personas.
    *   `POST /session/init`:
        *   Body: `{ agent_id: str, context: str }`
        *   Action: Create ADK Session, inject Context (Codebase) as system 
            message.
        *   Return: `{ session_id: str }`
    *   `WS /session/{id}/chat`:
        *   Bidirectional WebSocket.
        *   Client sends: `{ role: "user", content: "..." }`
        *   Server streams: Text chunks from ADK.

## 4. Phase 3: The Client (CLI Refactor)

### 4.1. Network Client: `src/vybz/client/api.py`
A wrapper around `httpx` and `websockets` to abstract the network layer.
*   `connect()`: Handshake with server.
*   `start_session(agent, codebase_snapshot)`: Calls API.
*   `chat_stream(text)`: Yields chunks from WebSocket.

### 4.2. Refactor `ReplSession`
*   **Remove:** `google.genai` imports.
*   **Remove:** `SessionManager` (local logic).
*   **Inject:** `VybzApiClient`.
*   **Logic Change:**
    *   On `/update` or startup: `codebase.render()` -> `client.update_context()`.
    *   On input: `client.chat_stream(input)` -> `ui.stream_chunk()`.

## 5. Phase 4: Server Management (`vybzdctl`)

We introduce a dedicated control utility `vybzdctl` to manage the `vybzd` 
daemon lifecycle, supporting both ad-hoc execution and system service 
integration.

### 5.1. The Control Tool: `src/vybz/tools/ctl.py`
*   **Command:** `vybzdctl`
*   **Actions:**
    *   `start`: Runs `uvicorn` in daemon mode.
    *   `stop`: Sends SIGTERM to the PID.
    *   `status`: Checks health endpoint.
    *   `install`: Generates and installs system service files based on OS detection.

### 5.2. Service Integration (OS Mastery)
*   **FreeBSD/OpenBSD:** Generate `/etc/rc.d/vybzd`.
    *   Uses `rc.subr`.
    *   Config via `/etc/rc.conf`.
*   **Debian/Linux:** Generate `/etc/systemd/system/vybzd.service`.
    *   Type=simple.

### 5.3. Client Orchestration
The `vybz` client will instruct the user to spawn a user-level instance via 
`vybzdctl start --user` if no system daemon is detected.
 
## 6. Execution Plan

1.  **Structure:** Create `src/vybz/server` and `src/vybz/client`.
2.  **Shared:** Move `CodeBase` and `Library` to `src/vybz/shared`.
3.  **Server:** Implement `AdkHydrator` and basic FastAPI shell.
4.  **Client:** Implement `VybzApiClient`.
5.  **Integration:** Refactor `ReplSession` to use the API client.
6.  **Management:** Implement `vybzdctl` and service generation templates.

## 7. Senior Dev Critique (Pre-Build)
*   **Latency:** Sending the full codebase snapshot (which can be MBs) over 
    local HTTP is fast, but we should ensure we only send it on startup or 
    explicit `/update`.
*   **State Drift:** If the server persists but the user changes the 
    `agents/*.toml` files locally, the server is stale. The server needs a 
    `/reload` endpoint or a file watcher. *Decision: For V1, restart server on 
    CLI exit.*
*   **Authentication:** Localhost implies trust, but future remote versions 
    will need auth. Keep this in mind.

## 8. Verification Strategy
1.  **Manual:** Run `uvicorn` in Tab 1. Run `vybz` in Tab 2. Verify chat works.
2.  **Auto:** Run `vybz` (no server running). Verify it spawns server and 
    connects.
3.  **Context:** Modify a file. Run `/update`. Verify agent sees change.

```

### 3. Senior Dev Peer Review

*   **Architecture:** The specific split between `vybz-engine` (ADK/State) and 
    `vybz-cli` (UI/IO) is the correct pattern. It allows the "Brain" to 
    eventually move to a remote GPU server or cloud instance while the "Body" 
    remains local to the files being edited.
*   **Dependencies:** Moving `CodeBase` to `shared` is critical. The Client 
    needs to *read* the files, but the Server needs to *understand* the 
    structure (if we ever move to server-side file access). For now, 
    Client-Side Read -> Server-Side Context Injection is the safest path for a 
    tool that edits local files.
*   **ADK Fit:** Using the ADK's `Agent` and `Session` abstractions replaces 
    our custom `SessionManager` and `ContextAssembler` logic, which is a net 
    reduction in technical debt (outsourcing complexity to the library).

### 4. Verification Script

This script verifies that the Python environment is ready for the refactor 
(imports) and simulates the Server/Client handshake logic.

```python
if __name__ == "__main__":
    import asyncio
    import sys
    
    print("--- Simulating ADK Client/Server Architecture ---")
    
    # 1. Mock Server Logic (The Engine)
    class MockAdkRuntime:
        def __init__(self):
            self.sessions = {}
            
        def create_session(self, agent_id, context):
            sid = f"session-{agent_id}-123"
            self.sessions[sid] = {"context_len": len(context)}
            return sid
            
        async def chat(self, sid, text):
            # Simulate ADK processing
            yield f"Echo: {text}"

    # 2. Mock Client Logic (The CLI)
    async def run_client_simulation():
        runtime = MockAdkRuntime()
        
        # Snapshot (Client Side)
        codebase_snapshot = "# CodeBase\n..." 
        print(f"[Client] Snapshot size: {len(codebase_snapshot)} bytes")
        
        # Init Session (Network Call)
        sid = runtime.create_session("junior-dev", codebase_snapshot)
        print(f"[Client] Connected to Session: {sid}")
        
        # Chat Loop
        user_input = "Hello World"
        print(f"[Client] Sending: {user_input}")
        
        async for chunk in runtime.chat(sid, user_input):
            print(f"[Client] Received: {chunk}")

    # Run
    try:
        asyncio.run(run_client_simulation())
        print("[SUCCESS] Architecture concept valid.")
    except ImportError:
        print("[SKIP] Asyncio/Runtime missing.")
```
