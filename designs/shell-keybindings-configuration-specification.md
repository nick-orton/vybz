---
status: "Completed"
type: "Design"
last_updated: "2026-01-14"
references: intents/configure-ui-options-shell-keybindings.md
---

# [Shell Keybindings Configuration] Specification

## 1. High-Level Intent
Implement configuration controls for the REPL's input editing mode. Currently,
`vybz` defaults to Emacs-style keybindings (standard for `prompt_toolkit`).
Given our strong POSIX/FreeBSD operating context, many users prefer `vi`
bindings for editing complex multi-line inputs. This feature adds a CLI flag
(`--mode`) for startup configuration and a REPL command (`/set`) for runtime
toggling.

## 2. User Stories
* As a User, I want to launch `vybz` with `vybz junior-dev --mode vi`, so that
  I can use familiar Vim motions (h, j, k, l) immediately.
* As a User, I want to switch modes dynamically using `/set vi` or `/set emacs`
  inside the session, in case I change my mind or hand the keyboard to a
  colleague.
* As a User, I want clear feedback ("Input mode set to VI") when the change
  occurs.

## 3. Acceptance Criteria
- [ ] **CLI Argument:** `src/vybz/tools/work.py` accepts `--mode` with choices
      `['vi', 'emacs']`. Default is `emacs`.
- [ ] **Initialization:** `ReplSession` initializes with the requested mode.
- [ ] **Runtime Command:** The REPL recognizes `/set <mode>` (case-insensitive).
- [ ] **State Change:** Executing `/set vi` updates the active `PromptSession`
      to use `EditingMode.VI`.
- [ ] **Validation:** Invalid modes result in an error message listing valid
      options.

## 4. Implementation Hints (Technical)
*   **Library:** `prompt_toolkit` controls this via the `editing_mode`
    attribute.
*   **Imports:**
    ```python
    from prompt_toolkit.enums import EditingMode
    ```
*   **Mapping:**
    ```python
    MODE_MAP = {
        "vi": EditingMode.VI,
        "emacs": EditingMode.EMACS
    }
    ```
*   **Update Logic:**
    The `PromptSession` object is stateful. You can update
    `self.session.editing_mode` at any time between prompts.

## 5. Execution Plan
1.  [ ] **Update CLI:** Modify `src/vybz/tools/work.py` to add the `--mode`
        argument and pass it to the `ReplSession` constructor.
2.  [ ] **Update REPL Init:** Modify `src/vybz/repl.py` `__init__` to accept
        `mode: str` and set the initial `editing_mode`.
3.  [ ] **Implement Command:** Add `/set` logic to `_handle_command` in
        `src/vybz/repl.py`.
