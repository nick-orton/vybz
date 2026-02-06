---
status: "Draft"
type: "Blueprint"
author: "Senior Python Architect"
last_updated: "2026-02-06"
references: blueprints/vybzd/vybzd-top-level-blueprint.md, blueprints/vybzd/vybzd-step-2-adk-adapter.md
---

# Vybz Engine Refactor - Step 3: The Engine (Server Implementation)

This blueprint details the implementation of `vybzd`, the headless FastAPI 
server that hosts the Google ADK runtime. This server acts as the "Brain," 
managing agent state and executing prompts, while exposing a REST/WebSocket 
interface for clients.

## 1. Dependencies
*   **Target:** `pyproject.toml`
*   **Action:** Add `fastapi>=0.109.0` and `uvicorn[standard]>=0.27.0`.

## 2. Module Specification: `src/vybz/server/state.py`

We need a singleton-style container to hold the server's runtime state, as 
FastAPI re-initializes dependencies per request.

### Class: `ServerState`
*   **Attributes:**
    *   `agent_registry: Dict[str, adk.Agent]`: The hydrated squad (Read-only 
        after startup).
    *   `sessions: Dict[str, adk.Session]`: Active chat sessions (Mutable).
    *   `library: Library`: The Vybz library service.
*   **Methods:**
    *   `initialize()`: Uses `AdkHydrator` to populate `agent_registry`.
    *   `get_agent(agent_id: str) -> adk.Agent`: Lookup.
    *   `create_session(agent_id: str, context: str) -> str`: Initializes an 
        ADK session and returns a UUID.

## 3. Module Specification: `src/vybz/server/main.py`

The entry point for the `uvicorn` process.

### 3.1 Lifespan Manager
We use FastAPI's `lifespan` context manager to load the Squad *once* at startup.
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load Library and Hydrate Agents
    state.initialize()
    yield
    # Clean up (if necessary)
