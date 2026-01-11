---
status: "Draft" 
type: "Design" 
last_updated: "2026-01-11" 
references: intents/switch-agents.md, designs/multi-round-chat.md 
---

# Agent Switching & Session Management Specification

## 1. High-Level Intent
Enable the Vybz REPL to manage multiple concurrent, isolated agent sessions.
Currently, the REPL is bound to a single agent at initialization. This feature
allows the user to switch active personas (e.g., from `pm` to `senior-dev`)
without restarting the CLI. Each agent maintains its own independent
conversation history ("Parallel Universes"), allowing the user to context-switch
between architectural planning and code implementation seamlessly.

## 2. User Stories
* As a User, I want to use the `/agent` command to switch the active persona.
* As a User, I want to see a list of available agents if I type `/agent` without
  arguments (or with partial matches), so that I don't have to memorize
  filenames.
* As a User, I want the system to preserve the chat history of Agent A when I
  switch to Agent B, so that when I return to Agent A, our conversation resumes
  exactly where we left off.
* As a User, I want the UI Header to immediately update to reflect the new
  active Agent and their specific context.

## 3. Acceptance Criteria
- [ ] **Command Implementation:** `/agent <name>` command added to
  `ReplSession`.
- [ ] **Lazy Loading:** Switching to a new agent initializes a new `ChatSession`
  (with current Date/Codebase context) only upon request.
- [ ] **State Persistence:** Switching away from an agent caches its
  `ChatSession` object in memory.
- [ ] **State Restoration:** Switching back to a previously used agent restores
  its history and context window.
- [ ] **Autocomplete/Menu:**
    - If `/agent` is typed with no args, display available agents.
    - `prompt_toolkit` auto-completion for agent names.
- [ ] **UI Feedback:**
    - The Session Header (Top of screen) updates the "AGENT" field.
    - The Prompt (Bottom of screen) updates to the new agent name (e.g., `[PM
      Lead] >>`).
    - A system message confirms the switch: "Switched to PM Lead (New Session)"
      or "(Resumed Session)".

## 4. Implementation Hints (Technical)
*   **Architecture Refactor (`src/vybz/repl.py`):**
    *   Current: `self.chat` holds one session.
    *   New: `self.sessions: Dict[str, ChatSession]` and `self.active_agent_key:
        str`.
*   **Session Management:**
    *   Create a helper method `_get_or_create_session(agent_key: str)`.
    *   Reuse `_init_chat` logic but scope it to the requested agent.
    *   **CRITICAL:** `CodeBase` snapshot is shared/immutable across sessions
        (for now), or re-injected if we want to capture file changes between
        switches. *Decision: Share the initial snapshot object to save
        memory/time, unless `_init_chat` is called new.*
*   **Prompt Toolkit:**
    *   Use `Completer` for the `/agent` command if possible, or simple string
        matching logic in `_handle_command`.
*   **UI:**
    *   Call `ui.render_session_header` immediately after a switch to visually
        reset the context for the user.

## 5. Execution Plan
1.  [ ] **Refactor ReplSession:** Change `__init__` to initialize a `sessions`
    dictionary rather than a single `chat` object.
2.  [ ] **Implement Session Switcher:** Create `switch_agent(name)` method that
    handles the lazy loading and pointer update.
3.  [ ] **Update Command Handler:** Expand `_handle_command` to parse `/agent`.
    Implement fuzzy matching or listing of `Squad.list_agents()`.
4.  [ ] **UI & Verification:** Ensure the prompt string and header update
    dynamically.
