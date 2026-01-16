---
status: "Draft"
type: "Blueprint"
last_updated: "2026-01-16"
references: designs/repl-prompt-conciseness-refactor.md
---

# REPL Prompt Conciseness Refactor Implementation Plan

This blueprint details the refactoring of the Vybz REPL interface to address UX
friction regarding horizontal sprawl and invisible state. We will transition
from verbose, static prompts to concise, dynamic prompts with a dedicated status
bar on the right side of the terminal.

## 1. Goal
Maximize usable screen real estate and provide immediate visual feedback on
system state (Input Mode, Context Availability) without cluttering the input
line.

## 2. Module Specification: `src/vybz/repl.py`

### 2.1 Imports
*   Add `from prompt_toolkit.styles import Style` to handle custom styling classes.

### 2.2 Class `ReplSession` Updates

We will introduce three new helper methods to encapsulate the TUI logic and
clean up the `start()` loop.

#### Method: `_get_prompt_tokens(self) -> List[Tuple[str, str]]`
*   **Purpose:** Generates the left-side prompt.
*   **Logic:**
    1.  Determine Label: Use `self.active_agent.id` (filename stem) instead of
        `.name`. Fallback to "vybz" if None.
    2.  Return Tokens:
        *   `("class:agent", f"{label} ")`
        *   `("class:separator", "❯ ")`

#### Method: `_get_rprompt_tokens(self) -> List[Tuple[str, str]]`
*   **Purpose:** Generates the right-side status prompt.
*   **Logic:**
    1.  **Input Mode:** Check `self.session.editing_mode`.
        *   `EditingMode.VI` -> "VI"
        *   `EditingMode.EMACS` -> "EMACS"
    2.  **Context:** Check `self.codebase`.
        *   Not None -> "CTX"
        *   None -> "NO-CTX"
    3.  Return Tokens:
        *   `("class:meta", f"{mode_str} | {ctx_str}")`

#### Method: `_get_style(self) -> Style`
*   **Purpose:** Defines the color mapping for the custom classes used above.
*   **Definition:**
    ```python
    return Style.from_dict({
        "agent": "bold cyan",       # Matches default theme 'info'
        "separator": "bold green",  # Matches default theme 'success'
        "meta": "dim white",        # Matches default theme 'timestamp'
    })
    ```

### 2.3 Refactor: `start()`
*   **Remove:** The `prompt_text = HTML(...)` construction inside the loop.
*   **Update:** The `self.session.prompt()` call.
    ```python
    user_input = self.session.prompt(
        self._get_prompt_tokens,      # Pass method reference (Dynamic)
        rprompt=self._get_rprompt_tokens, # Pass method reference (Dynamic)
        style=self._get_style(),
        multiline=True
    )
    ```

## 3. Verification Strategy

### Manual Test Plan
1.  **Launch:** `vybz junior-dev --mode vi`
2.  **Visual Check (Left):** Prompt should read `junior-dev ❯ `.
3.  **Visual Check (Right):** Right prompt should read `VI | CTX` (if in a codebase) or `VI | NO-CTX`.
4.  **State Change:**
    *   Type `/set emacs`.
    *   *Expect:* Right prompt updates instantly to `EMACS | ...`.
5.  **Agent Switch:**
    *   Type `/agent pm`.
    *   *Expect:* Left prompt updates instantly to `pm ❯ `.

## 4. Execution Steps
1.  **Modify `src/vybz/repl.py`:** Implement the 3 helper methods.
2.  **Update `start()`:** Wire up the dynamic prompt generation.
3.  **Verify:** Run the manual test plan.
