---
status: "Completed"
type: "Blueprint"
last_updated: "2026-01-12"
references: designs/codebase-context-hot-reload-specification.md
---

# Context Hot-Reload Implementation Plan

This blueprint details the implementation of the `/update` command in the 
`vybz` REPL. This feature allows the user to refresh the `CodeBase` snapshot 
and the "Current Date" metadata without restarting the application or losing 
conversation history.

## 1. Goal
Enable a development loop where the user can:
1. Discuss a plan with an Agent.
2. Modify files (or apply Agent code) externally.
3. Run `/update` to make the Agent aware of the changes.
4. Continue the conversation verifying the new state.

## 2. Module Specification: `src/vybz/repl.py`

### 2.1 Class `ReplSession` Updates

#### Method: `_refresh_context(self) -> None`
*   **Purpose:** Orchestrates the reload of the CodeBase and the reconstruction 
    of Chat sessions.
*   **Logic:**
    1.  **UI Feedback:** Print "Refreshing CodeBase snapshot..."
    2.  **CodeBase Reload:**
        *   If `self.codebase` is not None:
            *   Re-instantiate `self.codebase = CodeBase(self.codebase.root_path)`.
        *   If `self.codebase` is None:
            *   Print warning (Greenfield mode), but still proceed to update Date.
    3.  **Session Hot-Swap:**
        *   Iterate through all items in `self.sessions` (Dict[agent_name, chat_object]).
        *   For each agent, call `self._rebuild_chat_session(agent_name, old_chat)`.
        *   Update `self.sessions` with the new chat objects.
    4.  **Active Session Update:**
        *   Update `self.active_chat` to point to the new chat object for `self.active_agent`.
    5.  **UI Feedback:** Print success message "Context refreshed. Date: YYYY-MM-DD."

#### Method: `_rebuild_chat_session(self, agent_name: str, old_chat: Any) -> Any`
*   **Purpose:** Creates a new `Chat` object with fresh system instructions but 
    preserves conversation history.
*   **Logic:**
    1.  **Retrieve Agent:** `Squad.get_agent(agent_name)`.
    2.  **Construct System Instruction:**
        *   `agent.construct_agent_role_profile()`
        *   `Current Date` (Fresh `datetime.now()`)
        *   `self.codebase.render()` (The newly refreshed snapshot).
    3.  **Extract History:**
        *   `history = old_chat.get_history()`
        *   *Note:* The SDK `get_history()` returns the list of messages 
            exchanged so far.
    4.  **Create New Chat:**
        ```python
        new_chat = self.client.chats.create(
            model=self.model_id,
            history=history, # Inject preserved history
            config=types.GenerateContentConfig(
                system_instruction=new_sys_instruction,
                temperature=0.7
            )
        )
        ```
    5.  Return `new_chat`.

### 2.2 Command Handling (`_handle_command`)
*   **New Case:** `/update`
*   **Action:** Call `self._refresh_context()`.
*   **Return:** `True`.

## 3. Verification Strategy

### Manual Test Script
1.  **Launch:** `vybz junior-dev -c .` (Interactive Mode).
2.  **Turn 1:** "What is in `README.md`?" -> Agent quotes current README.
3.  **External Action:** Modify `README.md` (e.g., add "Updated via Vybz").
4.  **Command:** `/update`.
    *   *Expect:* "Refreshing CodeBase..." -> "Context refreshed."
5.  **Turn 2:** "What does the README say now?"
    *   *Expect:* Agent quotes the **new** text.
    *   *Expect:* Agent remembers Turn 1 (History preserved).

## 4. Execution Steps
1.  **Implement `_rebuild_chat_session` helper.**
2.  **Implement `_refresh_context` logic.**
3.  **Register `/update` command.**
