---
status: "Completed"
type: "Design"
last_updated: "2026-01-12"
references: intents/refresh-codebase-context-via-update.md
---

# CodeBase Context Hot-Reload Specification

## 1. High-Level Intent
Implement a `/update` command within the REPL that forces a refresh of the
`CodeBase` snapshot and injects it into the active (and cached) chat sessions.
Currently, the file system state is captured only once at startup. This feature
enables "Hot Reloading" of context, allowing users to modify files externally
or apply agent-generated code, then immediately ask the agent to verify those
changes without losing the conversation history.

## 2. User Stories
* As a User, I want to type `/update` to re-scan my project directory, so that
  the agent becomes aware of file changes made since the session started.
* As a User, I want the agent to retain our conversation history after an
  update, so I don't have to re-explain the task.
* As a User, I want the system to confirm when the update is complete, so I
  know I can proceed with the new context.

## 3. Acceptance Criteria
- [ ] **Command:** The `/update` command is recognized by the REPL.
- [ ] **Re-Snapshot:** Executing the command re-initializes the `CodeBase`
      object, capturing the current state of the filesystem.
- [ ] **Time Sync:** The "Current Date" in the system instruction is updated to
      the immediate present.
- [ ] **Active Session Hot-Swap:** The currently active `ChatSession` is
      replaced by a new instance containing:
      1. The *new* System Instruction (New Date + New CodeBase).
      2. The *old* Chat History (preserved).
- [ ] **Cached Session Handling:** Inactive sessions in `self.sessions` are
      either similarly hot-swapped so they reload
      context upon next switch.
- [ ] **Feedback:** UI displays "Context and CodeBase refreshed" upon success.

## 4. Implementation Hints (Technical)
*   **SDK Constraints:** The `system_instruction` of an existing `ChatSession`
    cannot be mutated. You must instantiate a *new* chat object.
*   **Swap Logic:**
    ```python
    # 1. Capture History
    history = self.active_chat.get_history()
    
    # 2. Re-Initialize CodeBase
    self.codebase = CodeBase(self.codebase.root_path)
    
    # 3. Construct New System Prompt
    new_instr = self.active_agent.construct_agent_role_profile() + ... 
    
    # 4. Create New Chat
    self.active_chat = self.client.chats.create(
        model=self.model_id,
        history=history, # <--- Critical
        config=types.GenerateContentConfig(system_instruction=new_instr)
    )
    ```
*   **Inactive Sessions:** To ensure consistency, it is safer to iterate
    through `self.sessions` and apply this logic to *all* of them.

## 5. Execution Plan
1.  [ ] **Method Definition:** Add `_refresh_context(self)` to `ReplSession` in
        `src/vybz/repl.py`.
2.  [ ] **Snapshot Logic:** Implement the `CodeBase` re-instantiation and logic
        to clear/invalidate inactive sessions in `self.sessions`.
3.  [ ] **Chat Swap:** Implement the history extraction and new chat creation
        pattern for the `active_chat`.
4.  [ ] **Command Binding:** Wire `/update` in `_handle_command` to call
        `_refresh_context`.
