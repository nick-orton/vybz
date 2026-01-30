---
status: "Draft"
type: "Blueprint"
author: "Senior Python Architect"
last_updated: "2026-01-29"
references: designs/load-file-functionality-specification.md
---

# Load File Functionality Implementation Plan

This blueprint details the implementation of the `/load` command, enabling users to surgically inject specific files into the Agent's context window.

## 1. Goal
To allow users to manually load files (e.g., config files, scripts outside the source tree) into the active session context and ensure these files persist across `CodeBase` refreshes.

## 2. Module Specification: `src/vybz/services/context.py`

### 2.1 Update `ContextAssembler`
We need to expand the `build_system_instruction` signature to accept manual context data.

*   **Signature Update:**
    ```python
    @staticmethod
    def build_system_instruction(
        agent: Agent, 
        codebase: CodeBase | None, 
        manual_context: Dict[str, str] | None = None
    ) -> str
    ```
*   **Render Logic:**
    *   Append a new section `### MANUAL CONTEXT` after the CodeBase section.
    *   Iterate through `manual_context` (Filename -> Content).
    *   Format each entry as a labelled Markdown code block.

## 3. Module Specification: `src/vybz/services/session.py`

### 3.1 Class `SessionManager` Updates

#### Attributes
*   Add `self.manual_context: Dict[str, str] = {}` to `__init__`.

#### Method: `load_file(self, path_str: str) -> str`
*   **Purpose:** Reads a file and stores it in memory.
*   **Logic:**
    1.  Resolve `Path(path_str).resolve()`.
    2.  **Validation:** Check exists, is_file.
    3.  **Read:** Read content (UTF-8).
    4.  **Store:** `self.manual_context[str(resolved_path)] = content`.
    5.  **Return:** The resolved path string (for UI feedback).
    6.  **Error Handling:** Raise `FileNotFoundError` or `IOError` to be caught by the Command layer.

#### Update: `_create_chat`
*   Pass `self.manual_context` to `ContextAssembler.build_system_instruction`.

#### Update: `refresh_context`
*   No logic change required regarding `manual_context` persistence (since it's an instance attribute), but ensure the call to `_create_chat` inside the loop picks up the current state.

## 4. Module Specification: `src/vybz/commands/core.py`

### 4.1 New Class: `LoadCommand`
*   **Name:** `/load`
*   **Logic:**
    1.  Validate args (require 1 arg).
    2.  Call `session.session_manager.load_file(args[0])`.
    3.  Call `session.session_manager.refresh_context()` to hot-swap the session with the new data.
    4.  **UI Feedback:**
        *   Success: `ui.print_success(f"Loaded {path} into context.")`
        *   Failure: `ui.print_error(...)` inside the try/except block.

## 5. Execution Steps

1.  **Update Service (Context):** Modify `src/vybz/services/context.py`.
2.  **Update Service (Session):** Modify `src/vybz/services/session.py`.
3.  **Implement Command:** Add `LoadCommand` to `src/vybz/commands/core.py` and register it in `registry.py`.
4.  **Verify:** Run verification script.

## 6. Verification Strategy

### 6.1 Automated Test
*   Create `tests/vybz/commands/test_load_command.py`.
*   Mock `SessionManager`.
*   Verify `load_file` updates the dict.
*   Verify `refresh_context` is called.

### 6.2 Manual Verification
1.  Launch `vybz junior-dev`.
2.  Create a dummy file `secret_plans.txt`.
3.  Run `/load secret_plans.txt`.
4.  Ask "What is in the secret plans?".
5.  Run `/update`.
6.  Ask "Do you still know the plans?".
```

### 3. Senior Dev Peer Review
*   **Persistence:** The plan correctly identifies that `manual_context` stored in `SessionManager` will survive a `refresh_context` call (which only re-instantiates `CodeBase`).
*   **Separation:** The `ContextAssembler` remains stateless, receiving the data it needs.
*   **UX:** Triggering `refresh_context` immediately after load is the correct move; otherwise, the user would load a file and the agent wouldn't know about it until the *next* manual refresh, which is confusing.

### 4. Verification Script
This script verifies the new method signatures can be implemented without breaking existing calls (using default args).

```python
if __name__ == "__main__":
    from typing import Dict, Optional
    
    # Mocking the ContextAssembler update
    def build_system_instruction(
        agent: str, 
        codebase: str | None, 
        manual_context: Dict[str, str] | None = None
    ) -> str:
        out = f"Agent: {agent}\n"
        if codebase:
            out += f"CodeBase: {codebase}\n"
        
        if manual_context:
            out += "### MANUAL CONTEXT\n"
            for name, content in manual_context.items():
                out += f"File: {name}\n{content}\n"
        return out

    # Test Backward Compatibility
    print("--- Test 1: Legacy Call ---")
    print(build_system_instruction("Junior", "root/"))
    
    # Test New Functionality
    print("\n--- Test 2: With Manual Context ---")
    files = {"/tmp/notes.txt": "Secret Info"}
    print(build_system_instruction("Junior", "root/", files))
