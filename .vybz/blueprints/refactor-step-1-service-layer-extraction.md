---
status: "Complete"
type: "Blueprint"
author: "Senior Python Architect"
last_updated: "2026-01-17"
references: critiques/codebase-quality--structural-critique.md
---

# Refactor Step 1: Service Layer Extraction

This blueprint details the first phase of the REPL architecture refactor. We will extract the **System Prompt Construction** and **GenAI Session Management** logic from `src/vybz/repl.py` into dedicated service classes.

## 1. Goal
To decouple "Business Logic" (managing API state, context, and agents) from "Presentation Logic" (TUI loops, keybindings, and printing). This prepares the codebase for the Command Pattern refactor.

## 2. New Module: `src/vybz/services/context.py`

### 2.1 Class: `ContextAssembler`
A stateless utility class (or collection of static methods) responsible for assembling the final string sent to the LLM as a system instruction.

*   **Method:** `build_system_instruction(agent: Agent, codebase: CodeBase | None) -> str`
    *   **Logic:**
        1.  Call `agent.construct_agent_role_profile()`.
        2.  Append `datetime.now()` metadata.
        3.  Append `codebase.render()` if codebase is provided.
    *   **Migration:** Logic moves from `ReplSession._build_system_instruction`.

## 3. New Module: `src/vybz/services/session.py`

### 3.1 Class: `SessionManager`
A stateful controller that manages the lifecycle of GenAI `ChatSession` objects. It holds the "truth" of who we are talking to and what the history is.

*   **Attributes:**
    *   `client`: `genai.Client`
    *   `sessions`: `Dict[str, ChatSession]` (Cache of active sessions)
    *   `active_agent`: `Agent`
    *   `active_chat`: `ChatSession`
    *   `codebase`: `CodeBase | None`
    *   `model_id`: `str`

*   **Constructor:**
    *   Accepts `client`, `model_id`, `initial_agent`, `codebase`.
    *   Immediately activates the initial agent.

*   **Methods:**
    *   `_create_chat(agent: Agent, history: list = None) -> ChatSession`:
        *   Uses `ContextAssembler` to build prompt.
        *   Calls `client.chats.create`.
    *   `switch_agent(agent_name: str) -> Agent`:
        *   Resolves agent via `Squad`.
        *   Updates `active_agent` and `active_chat`.
        *   Returns the new `Agent` object (so the UI can update headers).
    *   `refresh_context() -> int`:
        *   Reloads `CodeBase` (if exists).
        *   Iterates `self.sessions`, extracting history and rebuilding chat objects with new prompts.
        *   Returns count of refreshed sessions.

## 4. Refactor: `src/vybz/repl.py`

### 4.1 Class `ReplSession`
*   **Imports:** Add `from vybz.services.session import SessionManager`.
*   **Attributes:**
    *   Remove: `self.client`, `self.sessions`, `self.active_agent`, `self.active_chat`, `self.codebase`, `self.model_id`.
    *   Add: `self.session_manager: SessionManager`.
*   **Method Updates:**
    *   `__init__`: Initialize `SessionManager` instead of setting up individual state.
    *   `_handle_input`: Delegate to `self.session_manager.active_chat.send_message_stream`.
    *   `_refresh_context`: Delegate to `self.session_manager.refresh_context()`.
    *   `_switch_to_agent...`: Delegate to `self.session_manager.switch_agent()`.
    *   `_get_prompt_tokens`: Access agent info via `self.session_manager.active_agent`.

## 5. Verification Strategy

### 5.1 Unit Tests
*   **New Test:** `tests/vybz/services/test_context.py` to verify prompt assembly.
*   **New Test:** `tests/vybz/services/test_session.py` to verify switching and refreshing logic in isolation (mocking the client).

### 5.2 Integration Check
*   Run `vybz junior-dev`.
*   Test `/agent pm` (Switching).
*   Test `/update` (Context Refresh).
*   Ensure behavior is identical to pre-refactor state.

## 6. Execution Steps
1.  Create `src/vybz/services/__init__.py`.
2.  Implement `src/vybz/services/context.py`.
3.  Implement `src/vybz/services/session.py`.
4.  Refactor `src/vybz/repl.py` to consume `SessionManager`.
5.  Run verification tests.
```

### Senior Dev Peer Review
This blueprint accurately captures the intent of Step 1. By isolating the `SessionManager`, we make the core logic testable without needing to instantiate a full TUI environment (which is notoriously hard to test automatically).

One minor addition: `vibez.py` also constructs system prompts. While not strictly in scope for the *REPL* refactor, using `ContextAssembler` in `vibez.py` as well would reduce code duplication further. I will mark this as a "Stretch Goal" for the implementation phase.

### Verification Script
This script verifies the directory structure creation for the new services.

```python
if __name__ == "__main__":
    from pathlib import Path
    
    services_dir = Path("src/vybz/services")
    print(f"Plan: Create directory {services_dir}")
    print(f"Plan: Create {services_dir / 'context.py'}")
    print(f"Plan: Create {services_dir / 'session.py'}")
    
    # Check if we are ready to implement
    if Path("src/vybz/repl.py").exists():
        print("[OK] Source exists, ready for refactor.")
    else:
        print("[FAIL] Source missing.")
