---
status: "Draft"
type: "Design"
author: "PM Lead"
last_updated: "2026-01-29"
references: intents/load-file-functionality.md, designs/codebase-context-hot-reload-specification.md
---

# Load File Functionality Specification

## 1. High-Level Intent
Implement a `/load <filename>` command within the REPL. This feature allows
users to manually inject specific file contents into the active Agent's context
window. Unlike the broad `CodeBase` snapshot (which scans a root directory),
this provides surgical precision, enabling the inclusion of files that might be
outside the project root, ignored by `.gitignore`, or simply relevant for a
specific one-off task. Crucially, these manually loaded files must persist
across context refreshes (`/update`).

## 2. User Stories
* As a User, I want to type `/load scripts/deploy.sh` to immediately add that
  file's content to the Agent's knowledge, so I can ask questions about it
  without restarting the session.
* As a User, I want manually loaded files to remain in context even after I run
  `/update` to refresh the main codebase, so I don't have to re-load them.
* As a User, I want clear feedback if the file cannot be found or read, so I
  can correct the path.

## 3. Acceptance Criteria
- [ ] **Command:** The REPL accepts `/load <path>`.
- [ ] **Path Resolution:** The path is resolved relative to the Current Working
      Directory (CWD).
- [ ] **State Persistence:** The `SessionManager` maintains a registry of
      manually loaded files (separate from the `CodeBase` object).
- [ ] **Context Injection:** When `/load` is executed, the file content is read
      and the Agent's system instruction is rebuilt to include it.
- [ ] **Hot Swap:** The active chat session is immediately refreshed (re-
      created with history preserved) to apply the new context.
- [ ] **Durability:** Executing `/update` (which refreshes the CodeBase) does
      *not* clear the manually loaded files.
- [ ] **Feedback:**
    - Success: "Loaded [filename] (Size: X bytes)."
    - Failure: "Error loading [filename]: [Reason]."

## 4. Implementation Hints (Technical)

### 4.1 Architecture Updates
*   **`src/vybz/services/session.py` (SessionManager):**
    *   Add attribute `self.manual_context: Dict[str, str]` (Filename -> Content).
    *   Update `refresh_context()` to pass this dictionary to the assembler.
    *   Add method `load_file(path: str) -> bool`: Handles reading and updating state.

*   **`src/vybz/services/context.py` (ContextAssembler):**
    *   Update `build_system_instruction` signature to accept `manual_context`.
    *   Render logic: Append a new section `### MANUAL CONTEXT` containing the
        loaded files formatted as markdown code blocks.

*   **`src/vybz/commands/core.py`:**
    *   Implement `LoadCommand`. Calls `session.session_manager.load_file()`,
        then triggers `session.session_manager.refresh_context()`.

## 5. Execution Plan
1. [ ] **Update Context Assembler:** Modify `src/vybz/services/context.py` to
       render the `manual_context` dictionary.
2. [ ] **Update Session Manager:** Modify `src/vybz/services/session.py` to
       store manual files and pass them during prompt construction.
3. [ ] **Implement Logic:** Add `load_file` method to `SessionManager` handling
       I/O and error catching.
4. [ ] **Create Command:** Implement `LoadCommand` in
       `src/vybz/commands/core.py` and register it.
5. [ ] **Verify:** Test loading a file, then asking the agent about its
       contents. Run `/update` and verify memory persists.
