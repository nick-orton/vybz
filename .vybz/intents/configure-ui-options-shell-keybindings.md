---
status: "Completed"
type: "Intent"
author: "Lead Technical Writer"
last_updated: "2026-01-14"
references: src/vybz/repl.py, src/vybz/tools/work.py
---

# Configure UI Options (Shell Keybindings)

## Context
Currently, the `vybz` REPL utilizes the default `prompt_toolkit` keybindings
(Emacs-style). In our POSIX/FreeBSD operating context, many users prefer Vi
keybindings (`set -o vi`) for editing complex, multi-line code blocks within
the terminal. There is currently no mechanism to toggle this preference at
startup or during a session.

## High-Level Intent
I want to implement configuration controls for the shell input mode. Users
should be able to select between `vi` and `emacs` editing modes via command-
line arguments at launch or via a slash command during the session.

## User Stories
*   As a User, I want to launch the application with a flag (e.g.,
    `--mode vi`) so that my preferred keybindings are active immediately upon
    session start.
*   As a User, I want to use the `/set` command (e.g., `/set vi`, `/set
    emacs`) within the REPL to toggle input modes dynamically without
    restarting.
*   As a User, I want the system to provide feedback when the mode is changed
    (e.g., "Input mode set to Vi").

## Acceptance Criteria
- [ ] **CLI Argument:** `src/vybz/tools/work.py` accepts a new optional
      argument: `--mode` (choices: `vi`, `emacs`). Default is `emacs`.
- [ ] **REPL Command:** `src/vybz/repl.py` handles the `/set` command in
      `_handle_command`.
- [ ] **Dynamic Switching:** executing `/set vi` updates the running
      `PromptSession` to use `prompt_toolkit.enums.EditingMode.VI`.
- [ ] **Validation:** Invalid modes passed to `/set` result in an error
      message listing valid options.

## Implementation Hints
*   **Library:** `prompt_toolkit` handles this via the `editing_mode`
    parameter on the `PromptSession` or `Application`.
*   **Imports:** You will likely need `from prompt_toolkit.enums import
    EditingMode`.
*   **State:** The `ReplSession` class should initialize with the mode passed
    from CLI args.
