---
status: "Draft"
type: "Blueprint"
last_updated: "2026-01-15"
references: designs/rc-config-file.md
---

# RC Config File Implementation Plan

This blueprint details the implementation of a persistent user configuration 
system for Vybz. It enables the CLI to load default settings (Theme, Mode, 
Model) from a user's dotfiles (`~/.vybzrc` or XDG config), reducing friction 
for power users.

## 1. Goal
Establish a configuration hierarchy: **CLI Arguments > User Config File > 
System Defaults**. This allows users to define their "Flow" environment once 
via a TOML file while retaining the ability to override settings for specific 
tasks.

## 2. New Module: `src/vybz/config.py`

### 2.1 Service: `ConfigLoader`
A stateless service responsible for discovering, parsing, and sanitizing user 
configuration.

*   **Imports:** `os`, `tomllib`, `pathlib.Path`, `typing`.
*   **Constants:**
    *   `ALLOWED_KEYS`: Set of strings defining valid config options (`theme`, 
        `mode`, `model`, `log_file`, `agent`, `codebase`).
*   **Method: `_get_search_paths() -> List[Path]`**
    *   Returns ordered list of paths to check:
        1.  `$HOME/.vybzrc`
        2.  `$XDG_CONFIG_HOME/vybz.config` (defaults to `~/.config/vybz.config`)
*   **Method: `load() -> Dict[str, Any]`**
    *   **Logic:**
        1.  Iterate search paths.
        2.  Stop at the first file that exists.
        3.  Parse content using `tomllib`.
        4.  **Sanitization:** Filter the dictionary to include *only* keys in 
            `ALLOWED_KEYS`. This prevents polluting the `argparse` namespace 
            with invalid data.
        5.  Return the sanitized dict (or empty dict if no file found).
    *   **Error Handling:** If TOML parsing fails, print a styled warning via 
        `ui.print_warning` and return an empty dict (Fail Open).

## 3. Refactor: `src/vybz/tools/work.py`

### 3.1 Integration in `main()`
We need to inject the loaded config into the `argparse` lifecycle **after** 
arguments are defined but **before** they are parsed.

*   **Import:** `from vybz import config`
*   **Logic Change:**
    ```python
    # ... after parser definition ...
    
    # 1. Load User Config
    user_defaults = config.ConfigLoader.load()
    
    # 2. Inject Defaults
    # This overrides the 'default=...' values set in add_argument(), 
    # but is overridden by actual CLI flags provided by the user.
    if user_defaults:
        parser.set_defaults(**user_defaults)
        
    # 3. Parse Args
    args = parser.parse_args()
    ```

## 4. Verification Strategy

### 4.1 Manual Test Plan
1.  **Baseline:** Run `vybz --help`. Note the default value for `--mode` 
    (should be `emacs`).
2.  **Configuration:** Create `~/.vybzrc`:
    ```toml
    mode = "vi"
    theme = "matrix"
    ```
3.  **Verification (Defaults):** Run `vybz --help`.
    *   *Expect:* The help text for `--mode` now says `(default: vi)`.
4.  **Verification (Runtime):** Run `vybz junior-dev`.
    *   *Expect:* UI loads with "matrix" theme (Green).
    *   *Expect:* Keybindings are Vi-mode.
5.  **Verification (Override):** Run `vybz junior-dev --theme default`.
    *   *Expect:* UI loads with "default" theme (Blue/Cyan), overriding the 
        config file.

## 5. Execution Steps
1.  **Create Module:** Implement `src/vybz/config.py`.
2.  **Refactor CLI:** Update `src/vybz/tools/work.py`.
3.  **Verify:** Perform the manual test plan.

```

### 3. Senior Dev Peer Review

*   **Safety:** The `ALLOWED_KEYS` filter in `ConfigLoader` is crucial. Without it, a malicious or typo-ridden config file could inject unexpected attributes into the `args` namespace, potentially causing runtime errors in `repl.py` or `vibez.py`.
*   **UX:** Using `parser.set_defaults()` is the correct "Pythonic" way to handle this. It ensures that the `--help` output accurately reflects the *effective* defaults for that specific user, which is a nice touch for usability.
*   **Robustness:** The "Fail Open" strategy (returning empty dict on error) ensures that a syntax error in a config file doesn't prevent the user from using the tool to fix it.

### 4. Verification Script

Since this blueprint involves filesystem interactions and CLI parsing, a standalone script to verify the `argparse` behavior is valuable.

```python
if __name__ == "__main__":
    import argparse
    
    # Simulate the logic
    print("--- Simulating Config Injection ---")
    
    # 1. Define Parser with System Defaults
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="emacs", help="Input mode")
    parser.add_argument("--theme", default="default", help="UI Theme")
    
    print(f"1. System Defaults: {parser.parse_args([])}")
    
    # 2. Load User Config (Simulated)
    user_config = {"mode": "vi", "theme": "matrix"}
    print(f"2. Loaded Config:   {user_config}")
    
    # 3. Inject Defaults
    parser.set_defaults(**user_config)
    
    # 4. Parse Empty Args (Should use Config)
    args_default = parser.parse_args([])
    print(f"3. Effective Args:  {args_default}")
    
    # 5. Parse Explicit Args (Should override Config)
    args_override = parser.parse_args(["--theme", "dracula"])
    print(f"4. Override Args:   {args_override}")
    
    assert args_default.mode == "vi"
    assert args_override.theme == "dracula"
    print("\n[SUCCESS] Logic holds.")
