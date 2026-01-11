---
status: "Draft"
type: "Blueprint"
last_updated: "2026-01-11"
references: designs/switch-agents.md
---

# Agent Switching Implementation Plan

This blueprint details the refactoring of `src/vybz/repl.py` to support multi-agent sessions within a single REPL instance.

## 1. Architectural Changes

### Current State
`ReplSession` is 1:1 with an `Agent` and a `ChatSession`.

### Target State
`ReplSession` acts as a session manager (1:N).
*   It maintains a registry of active chat sessions (`self.sessions`).
*   It lazily loads new agents via `Squad` when requested.
*   It preserves conversation history when switching between agents (Parallel Universes).

## 2. Module Specification: `src/vybz/repl.py`

### 2.1. Imports
*   Add `from vybz.squad import Squad` to enable dynamic agent loading.

### 2.2. Class `ReplSession` Refactor

#### Data Structures
*   **Remove:** `self.agent`, `self.chat` (as single instance attributes).
*   **Add:**
    *   `self.active_agent: Agent` (The currently selected persona).
    *   `self.active_chat: ChatSession` (The currently active GenAI chat object).
    *   `self.sessions: Dict[str, ChatSession]` (Map of `agent_name` -> `ChatSession` object).

#### Constructor (`__init__`)
*   Initialize `self.sessions = {}`.
*   Call `self._switch_to_agent(initial_agent)` immediately to set up the starting state.

#### New Method: `_get_or_create_chat(agent: Agent) -> ChatSession`
*   **Logic:**
    1.  Check `self.sessions` for `agent.name`. If exists, return it.
    2.  If not, construct System Instructions:
        *   `agent.construct_agent_role_profile()`
        *   `Date Knowledge`
        *   `CodeBase` (Shared snapshot).
    3.  Create new `client.chats.create(...)`.
    4.  Store in `self.sessions[agent.name]`.
    5.  Return it.

#### New Method: `_switch_to_agent(agent_name: str)`
*   **Logic:**
    1.  Resolve Agent object using `Squad.get_agent(agent_name)`.
    2.  Set `self.active_agent`.
    3.  Set `self.active_chat = self._get_or_create_chat(self.active_agent)`.
    4.  Update UI Header (`ui.render_session_header`).
    5.  Log the switch event to the file (`=== SWITCHED TO AGENT: ... ===`).

### 2.3. Command Handling (`_handle_command`)
*   **New Command:** `/agent [name]`
    *   **No Args:** Print list of available agents (`Squad.list_agents()`).
    *   **With Arg:** Call `self._switch_to_agent(name)`.
        *   Handle `ValueError` if agent doesn't exist and print error to `ui.print_error`.
    *   **Action:** If switch successful, return `True` (refresh loop).

### 2.4. The Loop (`start`)
*   **Prompt Update:** The prompt text `HTML(...)` must be re-generated inside the `while` loop (or updated upon switch) to reflect `self.active_agent.name`.

## 3. UI Implications
*   **Header:** `ui.render_session_header` is already robust enough, just needs to be called with the new agent name.
*   **Prompt:** Needs dynamic update to show `[NewAgent] >>`.

## 4. Verification Strategy
1.  **Launch:** `vybz pm`.
2.  **Chat:** "Plan a feature."
3.  **Switch:** `/agent senior-dev`.
    *   *Expect:* Header updates. Prompt changes to `[Senior Python Architect]`.
4.  **Chat:** "Review this plan." 
    *   *Note:* Senior Dev will NOT see PM's chat history (Sessions are isolated).
5.  **Switch Back:** `/agent pm`.
    *   *Expect:* History with PM is preserved.

## 5. Execution Steps
1.  **Refactor `__init__`**: Change single chat to dict.
2.  **Implement `_switch_to_agent`**: Core logic for lazy loading.
3.  **Update `_handle_command`**: Add `/agent` parser.
4.  **Update `start` loop**: Dynamic prompt rendering.
