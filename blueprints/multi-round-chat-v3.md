---
status: "Completed"
type: "Blueprint"
author: "Senior Python Architect"
last_updated: "2026-01-11"
references: blueprints/multi-round-chat.md, designs/multi-round-chat.md
---

# Phase 3: UI Polish & Interaction Refinement

This blueprint defines the final polish steps for the Interactive Chat feature. While the core CLI refactor was accelerated into Phases 1 & 2, this phase focuses on differentiating the "Session" UX from the "Task" UX and adding robust command handling.

## 1. Goal
Elevate the REPL from a functional loop to a polished, professional terminal interface with distinct visual identity and user controls.

## 2. Review: CLI Integration (`src/vybz/tools/work.py`)
*   **Status:** **Completed** (Accelerated).
*   **Verification:** The `intent` argument is successfully optional (`nargs='?'`), and the branching logic correctly initializes `ReplSession` when no intent is provided. No further changes required in this file.

## 3. Module Specification: `src/vybz/ui.py`
The current UI reuses the generic "Task" header. Interactive sessions require a distinct visual anchor.

### New Function: `render_session_header`
*   **Signature:**
    ```python
    def render_session_header(
        agent_name: str, 
        model_id: str, 
        codebase_root: str | None = None
    ) -> None:
    ```
*   **Visual Specs:**
    *   **Title:** "VYBZ KARTEL // INTERACTIVE SESSION"
    *   **Color Theme:** Use `spring_green1` or `bright_cyan` to distinguish from standard logs.
    *   **Metadata:** Display `Agent`, `Model`, and `Context` (if loaded).
    *   **Footer:** "Commands: /exit, /clear, /help | Submit: Alt+Enter"

## 4. Module Specification: `src/vybz/repl.py`
Enhance the input loop to support "Slash Commands" for session management.

### Method: `_handle_command(self, input_text: str) -> bool`
*   **Purpose:** Intercepts inputs starting with `/` before they are sent to the LLM.
*   **Returns:** `True` if a command was handled (skip LLM), `False` otherwise.
*   **Commands:**
    *   `/help`: Prints available keybindings and commands using `ui.print_system`.
    *   `/clear`: Clears the screen (visual reset) using `console.clear()`.
    *   `/exit`, `/quit`: Raises `EOFError` to close the session.

### Update: `start()`
*   Replace `ui.render_header` with `ui.render_session_header`.
*   Integrate `_handle_command` check inside the main loop.

## 5. Verification Strategy
1.  **Launch:** `vybz junior-dev`.
2.  **Visual Check:** Confirm the header explicitly says "INTERACTIVE SESSION" and lists the Context path (if `vybz junior-dev -c .`).
3.  **Command Check:**
    *   Type `/help` -> Expect system message with instructions.
    *   Type `/clear` -> Expect terminal to wipe (preserving history in memory, just clearing view).
    *   Type `/exit` -> Expect graceful shutdown.

