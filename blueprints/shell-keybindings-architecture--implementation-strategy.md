---
status: "Draft"
type: "Blueprint"
last_updated: "2026-01-14"
references: designs/shell-keybindings-configuration-specification.md
---

# Shell Keybindings Architecture & Implementation Strategy

This blueprint outlines the phased implementation strategy for configuring
Shell Keybindings (Vi vs Emacs) in the Vybz REPL. To ensure stability and
clean separation of concerns, the implementation is split into **Startup
Configuration** (CLI) and **Runtime Control** (Slash Commands).

## 1. Architectural Overview

The feature relies on `prompt_toolkit`'s native support for input modes. We
need to bridge the gap between user intent (string flags like "vi") and the
internal library enums (`EditingMode.VI`).

### 1.1 Data Flow
1.  **User:** Runs `vybz ... --mode vi`.
2.  **CLI (`work.py`):** Parses string.
3.  **REPL (`repl.py`):** Maps string to `prompt_toolkit.enums.EditingMode`.
4.  **Session:** `PromptSession` initialized with specific mode.
5.  **Runtime:** User types `/set emacs` -> `ReplSession` updates state.

## 2. Phased Implementation Plan

### Phase 1: Startup Configuration
**Goal:** Enable the user to select the editing mode at launch time via CLI arguments.

*   **Scope:**
    *   Update `src/vybz/tools/work.py` to accept `--mode`.
    *   Update `src/vybz/repl.py` to accept `mode` in `__init__`.
    *   Implement the mapping logic (String -> Enum).
*   **Deliverable:** `vybz junior-dev --mode vi` launches with Vi bindings active.

### Phase 2: Runtime Control
**Goal:** Enable the user to toggle the editing mode dynamically during an active session.

*   **Scope:**
    *   Implement `/set <mode>` command in `ReplSession._handle_command`.
    *   Implement logic to mutate the active `PromptSession` state.
    *   Add UI feedback ("Input mode set to ...").
*   **Deliverable:** Typing `/set emacs` instantly switches keybindings without restarting.

## 3. Technical Standards

### 3.1 Mapping Strategy
We will use a centralized mapping dictionary in `repl.py` to ensure consistency between CLI args and the `/set` command.

```python
from prompt_toolkit.enums import EditingMode

EDITING_MODES = {
    "vi": EditingMode.VI,
    "emacs": EditingMode.EMACS
}
```

### 3.2 Validation
Both the CLI entry point and the runtime command must validate input against the keys of `EDITING_MODES`.
*   **CLI:** Use `argparse` `choices=['vi', 'emacs']` for free validation.
*   **Runtime:** Check dictionary keys and return a friendly error message if invalid.

### 3.3 Default State
The system must default to `emacs` (Standard behavior) to preserve backward compatibility for existing users.
