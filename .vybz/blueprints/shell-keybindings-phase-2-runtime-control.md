---
status: "Completed"
type: "Blueprint"
author: "Senior Python Architect"
last_updated: "2026-01-14"
references: blueprints/shell-keybindings-architecture--implementation-strategy.md, designs/shell-keybindings-configuration-specification.md
---

# Shell Keybindings Phase 2: Runtime Control

This blueprint details the implementation of **Phase 2**, enabling the user to dynamically toggle the input editing mode (Vi vs Emacs) during an active REPL session via a slash command.

## 1. Goal
To allow users to switch their keyboard interaction model on the fly (e.g., typing `/set vi`) without losing their session context, chat history, or requiring a restart.

## 2. Module Specification: `src/vybz/repl.py`

### 2.1 Method Update: `_handle_command`
We will expand the command parser to handle the `/set` command.

*   **Command Syntax:** `/set <mode>`
*   **Arguments:**
    *   `mode`: Case-insensitive string (`vi` or `emacs`).
*   **Logic:**
    1.  **Validation:** Check if `args` exists. If not, print usage.
    2.  **Normalization:** Lowercase the input argument.
    3.  **Lookup:** Check if the mode exists in `EDITING_MODE_MAP`.
    4.  **Mutation:** Update `self.session.editing_mode` with the resolved Enum value.
        *   *Note:* `prompt_toolkit.PromptSession` allows dynamic updates to this attribute between prompts.
    5.  **Feedback:**
        *   **Success:** Call `ui.print_success(f"Input mode set to {mode.upper()}")`.
        *   **Failure:** Call `ui.print_error` listing valid options.

### 2.2 Implementation Snippet
```python
# Inside _handle_command loop...

if cmd == "/set":
    if not args:
        ui.print_error("Usage: /set <mode> (vi | emacs)")
        return True
    
    target_mode = args[0].lower()
    if target_mode not in EDITING_MODE_MAP:
        ui.print_error(f"Invalid mode '{target_mode}'. Options: {', '.join(EDITING_MODE_MAP.keys())}")
        return True
        
    # Apply the change
    new_mode_enum = EDITING_MODE_MAP[target_mode]
    self.session.editing_mode = new_mode_enum
    ui.print_success(f"Input mode set to {target_mode.upper()}")
    return True
```

## 3. Verification Strategy

### Manual Test Plan
1.  **Launch:** `vybz junior-dev` (Default: Emacs).
2.  **Verify Default:** Type `Esc`. It should likely print `^[`.
3.  **Command:** `/set vi`.
    *   *Expect:* "Input mode set to VI".
4.  **Verify Change:**
    *   Type `def foo():`.
    *   Press `Esc`.
    *   Press `0` (Go to start of line).
    *   *Expect:* Cursor moves to start.
5.  **Command:** `/set invalid`.
    *   *Expect:* Error message with options.
6.  **Command:** `/set emacs`.
    *   *Expect:* "Input mode set to EMACS".

## 4. Execution Steps
1.  **Modify `src/vybz/repl.py`:** Implement the `/set` case in `_handle_command`.
2.  **Verify:** Execute the manual test plan.
