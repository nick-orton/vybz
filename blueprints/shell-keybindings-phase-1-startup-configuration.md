---
status: "Completed"
type: "Blueprint"
last_updated: "2026-01-14"
references: blueprints/shell-keybindings-architecture.md
---

# Shell Keybindings Phase 1: Startup Configuration

This blueprint details the implementation of **Phase 1**, enabling the user to select the input editing mode (Vi vs Emacs) via Command Line Interface arguments at application launch.

## 1. Goal
To allow users to launch Vybz with `vybz junior-dev --mode vi` and immediately use Vi-style keybindings (e.g., `Esc` to enter navigation mode, `k`/`j` for history navigation) in the REPL.

## 2. Module Specification: `src/vybz/repl.py`

### 2.1 Imports
*   Add: `from prompt_toolkit.enums import EditingMode`

### 2.2 Constants
*   Define a module-level constant (or class attribute) for mapping:
    ```python
    EDITING_MODE_MAP = {
        "vi": EditingMode.VI,
        "emacs": EditingMode.EMACS
    }
    ```

### 2.3 Class `ReplSession` Updates

#### Constructor (`__init__`)
*   **New Argument:** `mode: str = "emacs"`
*   **Logic:**
    1.  Look up the enum in `EDITING_MODE_MAP`.
    2.  Pass this enum to the `PromptSession` constructor.
    ```python
    # Inside __init__
    self.editing_mode = EDITING_MODE_MAP.get(mode.lower(), EditingMode.EMACS)
    
    self.session = PromptSession(
        key_bindings=self.kb,
        editing_mode=self.editing_mode # <--- NEW
    )
    ```

## 3. CLI Integration: `src/vybz/tools/work.py`

### 3.1 Argument Parsing
*   **Update:** `argparse` definition in `main()`.
*   **Add Argument:**
    ```python
    parser.add_argument(
        "--mode",
        choices=["vi", "emacs"],
        default="emacs",
        help="Input editing mode (default: emacs)"
    )
    ```

### 3.2 Session Initialization
*   **Update:** The `ReplSession` instantiation block.
    ```python
    session = repl.ReplSession(
        # ... existing args ...
        mode=args.mode
    )
    ```

## 4. Verification Strategy

### Manual Verification
1.  **Launch:** `vybz junior-dev --mode vi`
2.  **Test:**
    *   Type some text.
    *   Press `Esc`.
    *   Press `h` (left), `l` (right) to move cursor.
    *   *Expectation:* Cursor moves without typing characters.
3.  **Launch:** `vybz junior-dev --mode emacs` (or default).
    *   Test: Press `Esc` then `h`.
    *   *Expectation:* `h` is likely typed or interpreted as a Meta sequence, but *not* as a navigation command in the same way.

## 5. Execution Steps
1.  **Refactor `repl.py`:** Add imports, map, and update `__init__`.
2.  **Refactor `work.py`:** Add CLI argument and pass to constructor.
3.  **Verify:** Run manual test.
