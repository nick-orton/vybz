---
status: "Draft"
type: "Blueprint"
last_updated: "2026-01-15"
references: designs/theming-the-repl-specification.md
---

# Theming the REPL Implementation Plan (v3)

This blueprint details the execution steps to externalize the Vybz UI styling 
into a TOML configuration file. This iteration simplifies the architecture by 
leveraging the native `rich.theme.Theme` object instead of a custom domain 
wrapper.

## 1. Goal
Decouple visual aesthetics from source code. Enable users to define custom 
color palettes in `themes.toml` and switch between them via CLI arguments or 
REPL commands.

## 2. Artifact Specification: `themes.toml`
A new configuration file to be created in the project root.

*   **Structure:**
    ```toml
    [default] # The "Cyber/Oceanic" fallback
    info = "cyan"
    warning = "bold yellow"
    error = "bold red"
    success = "bold spring_green1"
    "header.label" = "bold cyan"
    "header.value" = "spring_green1"
    content = "white"
    "panel.border" = "blue"
    "session.border" = "spring_green1"
    timestamp = "dim white"

    [matrix] # High-contrast Green/Black
    info = "bold green"
    warning = "bold yellow"
    # ... etc
    ```

## 3. New Module: `src/vybz/theme.py`

### 3.1 Service: `ThemeLoader`
A stateless service responsible for parsing configuration and returning Rich objects.

*   **Imports:**
    *   `from rich.theme import Theme`
    *   `import tomllib`
*   **Constants:**
    *   `DEFAULT_STYLES`: The hardcoded dictionary currently in `ui.py` (Cyber/Oceanic).
*   **Methods:**
    *   `load(name: str) -> Theme`:
        1.  **Discovery:** Check `Path.cwd() / "themes.toml"`.
        2.  **Parsing:** Use `tomllib.load()`.
        3.  **Lookup:** Find the section matching `name`.
        4.  **Fallback:**
            *   If file missing OR name not found:
            *   If `name == "default"`, return `Theme(DEFAULT_STYLES)`.
            *   Else, raise `ValueError`.
        5.  **Construction:** Return `Theme(styles_dict)`.
    *   `list_available() -> List[str]`: Returns list of keys in `themes.toml` + "default".

## 4. Refactor: `src/vybz/ui.py`

### 4.1 Cleanup
*   **Remove:** The hardcoded `VYBZ_THEME` constant.

### 4.2 Integration
*   **Import:** `from vybz.theme import ThemeLoader`.
*   **Function:** `set_theme(theme_name: str) -> bool`:
    *   **Logic:**
        1.  Try `rich_theme = ThemeLoader.load(theme_name)`.
        2.  If successful:
            *   **Hot Swap:** Re-instantiate global `console = Console(theme=rich_theme)` and `error_console`.
            *   Return `True`.
        3.  Catch `ValueError`:
            *   Print error listing `ThemeLoader.list_available()`.
            *   Return `False`.

## 5. CLI Integration: `src/vybz/tools/work.py`

### 5.1 Argument Parsing
*   **Update:** `argparse` definition.
*   **Add:** `--theme` (default: "default").

### 5.2 Initialization
*   **Logic:** Call `ui.set_theme(args.theme)` immediately after imports.

## 6. REPL Integration: `src/vybz/repl.py`

### 6.1 Command Handling (`_handle_command`)
*   **New Command:** `/theme <name>`
*   **Logic:**
    1.  Call `ui.set_theme(name)`.
    2.  Provide feedback based on boolean return.

## 7. Execution Steps

1.  **Create Module:** Implement `src/vybz/theme.py` containing `ThemeLoader`.
2.  **Create Config:** Create `themes.toml` in project root.
3.  **Refactor UI:** Update `src/vybz/ui.py` to delegate to `ThemeLoader`.
4.  **Update CLI:** Add `--theme` flag.
5.  **Update REPL:** Add `/theme` command.
6.  **Verification:** Run manual test script.

## 8. Verification Strategy

### Manual Test
```bash
# 1. Start with Matrix theme
vybz junior-dev --theme matrix

# 2. Check Visuals
# Expect: Green borders, Green text.

# 3. Switch Runtime
# Input: /theme default
# Expect: Success message in Cyan/Green. Borders change to Blue.
```
