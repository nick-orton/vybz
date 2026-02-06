---
status: "Draft"
type: "Design"
author: "Senior Python Architect"
last_updated: "2026-02-06"
references: intents/vybzd.md
---
```

# Vybz Engine Refactor: ADK Client/Server Architecture

## 1. High-Level Intent
Refactor Vybz from a monolithic CLI application into a distributed 
**Client/Server Architecture** leveraging the Google Agent Development Kit (ADK).

The core logic (Agent orchestration, Context management, Tool execution) will 
move to a headless **Vybz Server** (`vybz-engine`). The existing Terminal UI 
will become a lightweight **Vybz Client** (`vybz-cli`).

This separation decouples the "Brain" from the "Interface," enabling future 
clients (e.g., WhatsApp, VS Code, Web UI) to interact with the same persistent 
agent squad. It leverages the ADK's native `GenAIServer` capabilities to 
handle state, history, and tool routing, replacing our custom `SessionManager`.

## 2. User Stories
*   **As a Developer**, I want to run `vybz server start` to spin up a 
    persistent agent runtime that listens for connections.
*   **As a User**, I want to connect via the terminal CLI (`vybz junior-dev`) 
    to chat with an agent, then disconnect, and later reconnect from a 
    different interface (e.g., a Web UI) and see the same conversation history.
*   **As an Architect**, I want the Server to handle the complexity of 
    "Hydrating" Vybz TOML agents into ADK objects, so that clients can be dumb 
    rendering engines.
*   **As a User**, I want the Client to automatically upload my local 
    `CodeBase` context to the Server upon connection, so the remote agent 
    knows about my local files without needing direct filesystem access.

## 3. Acceptance Criteria
- [ ] **Dependency:** `google-adk` (and likely `fastapi`/`uvicorn` if not 
      bundled) added to `pyproject.toml`.
- [ ] **Architecture Split:** Codebase separated into `src/vybz/server` and 
      `src/vybz/client`.
- [ ] **The Server (`vybz-engine`):**
    - [ ] Implements an ADK-based runtime.
    - [ ] Exposes a WebSocket endpoint for real-time chat streaming.
    - [ ] Exposes REST endpoints for Agent switching and Skill management.
    - [ ] Implements `AdkHydrator` to load `library/agents/*.toml` at startup.
- [ ] **The Client (`vybz-cli`):**
    - [ ] Refactored `ReplSession` to use an `ApiClient` instead of local SDK 
      calls.
    - [ ] Serializes the local `CodeBase` (Markdown string) and transmits it 
      to the server during session initialization/update.
- [ ] **Tooling:**
    - [ ] `vybz` command updated to detect if server is running; if not, 
      prompt to start or auto-spawn (Localhost mode).

## 4. Implementation Hints (Technical)

### 4.1. Architecture Diagram
```text
[ File System ] <--- (Reads) --- [ Vybz CLI (Client) ]
                                        |
                                   (WebSockets)
                                   (JSON / REST)
                                        |
                                        v
[ ADK Runtime ] <--- (Hosts) --- [ Vybz Server ]
                                        ^
                                        |
                                 [ Agent Library (TOML) ]
```

### 4.2. The Server (`src/vybz/server/`)
We will likely wrap the ADK's `ModelRuntime` in a FastAPI app.

*   **`main.py`**: Entry point. Loads `Squad` via `AdkHydrator`.
*   **`hydrator.py`**:
    *   Reads `Agent` (TOML).
    *   Constructs `adk.Agent`.
    *   Maps `Skill` instructions to `adk.Agent.system_prompt`.
    *   *Crucial:* Maps `Skill/scripts/*.py` to `adk.Tool` definitions.
*   **`router.py`**:
    *   `POST /session/init`: Accepts `{ agent_id, codebase_context }`. Returns `session_id`.
    *   `WS /session/{id}/stream`: Bidirectional stream.

### 4.3. The Client (`src/vybz/client/`)
The `ReplSession` changes significantly. It becomes a View Controller.

```python
class NetworkSessionManager:
    def __init__(self, server_url):
        self.ws = connect(server_url)
        
    def send_prompt(self, text):
        self.ws.send({"role": "user", "content": text})
        
    def listen(self):
        for msg in self.ws:
            yield msg # Stream chunks to UI
