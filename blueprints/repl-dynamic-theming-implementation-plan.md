---
status: "Draft"
type: "Blueprint"
author: "Senior Python Architect"
last_updated: "2026-01-16"
references: designs/repl-dynamic-theming-specification.md
---

# REPL Dynamic Theming Implementation Plan

This blueprint details the refactoring of `src/vybz/repl.py` to support dynamic, theme-aware coloring of the input prompt.

## 1. Goal
To eliminate hardcoded color strings (e.g., `'cyan'`) in the REPL and instead derive input styling at runtime from the active `rich` theme defined in `vybz.ui`. This ensures visual consistency when users switch themes (e.g., to "Matrix" or "Dracula").

## 2. Module Specification: `src/vybz/repl.py`

### 2.1 Imports
*   **Add:** `from prompt_toolkit.styles import Style`

### 2.2 Helper Method: `_get_dynamic_style(self) -> Style`
We need a method that bridges `rich` styles to `prompt_toolkit` styles.

*   **Logic:**
    1.  Access the global `ui.console` to get the current theme.
    2.  Retrieve the `rich.style.Style` objects for semantic keys: `info`, `success`, `timestamp`.
    3.  Extract the color name (e.g., "cyan", "#ff00ff") from the rich style.
    4.  Construct and return a `prompt_toolkit.styles.Style` dictionary mapping semantic class names to these colors.

*   **Mapping Table:**
    | PTK Class | Rich Style Source | Fallback |
    | :--- | :--- | :--- |
    | `agent` | `info` | `cyan` |
    | `separator` | `success` | `green` |
    | `meta` | `timestamp` | `gray` |

*   **Implementation Detail:**
    ```python
    def _get_dynamic_style(self) -> Style:
        # Get Rich styles
        s_info = ui.console.get_style("info")
        s_success = ui.console.get_style("success")
        s_time = ui.console.get_style("timestamp")

        # Extract colors safely
        c_agent = s_info.color.name if s_info.color else "cyan"
        c_sep = s_success.color.name if s_success.color else "green"
        c_meta = s_time.color.name if s_time.color else "gray"

        return Style.from_dict({
            "agent": f"bold {c_agent}",
            "separator": f"bold {c_sep}",
            "meta": c_meta,
        })
    ```

### 2.3 Refactor: `start()` Loop
We must update the HTML string construction to use *classes* instead of hardcoded colors, and pass the dynamic style to the prompt method.

*   **Current:**
    ```python
    prompt_text = HTML(f"<b><style fg='cyan'>[{self.active_agent.name}]</style></b> >> ")
    # ...
    user_input = self.session.prompt(prompt_text, ...)
    ```

*   **New:**
    ```python
    # 1. Construct HTML using classes (class:name)
    # Note: We keep the structure simple for now, focusing on color.
    prompt_text = HTML(
        f"<b><style class='agent'>[{self.active_agent.name}]</style></b> "
        f"<style class='separator'>>> </style>"
    )

    # 2. Pass the dynamic style generator
    # We call _get_dynamic_style() inside the loop to catch theme changes
    user_input = self.session.prompt(
        prompt_text,
        style=self._get_dynamic_style(),
        multiline=True
        # ... other args
    )
    ```

## 3. Verification Strategy

### Manual Test Plan
1.  **Launch:** `vybz junior-dev --theme matrix`
    *   *Expect:* The prompt `[Tactical Python Architect] >>` should be **Green** (matching the Matrix `info` style), not Cyan.
2.  **Runtime Switch:**
    *   Type `/theme default`
    *   *Expect:* The prompt immediately turns **Cyan** on the next line.
3.  **Runtime Switch:**
    *   Type `/theme crimson` (if available) or `dracula`.
    *   *Expect:* The prompt adapts to the new palette (Red or Purple).

## 4. Execution Steps
1.  **Modify `src/vybz/repl.py`**: Add the `_get_dynamic_style` method.
2.  **Update `start()`**: Change the HTML string to use `class='agent'` and `class='separator'`.
3.  **Update `prompt()` call**: Inject the `style` argument.
4.  **Verify**: Run the manual test plan.
```

### 3. Senior Dev Peer Review

*   **Separation of Concerns:** The blueprint correctly identifies that `repl.py` shouldn't know about specific colors, only semantic classes (`agent`, `separator`). This delegates the "truth" of color to the `ui` module and `themes.toml`.
*   **Dependencies:** It correctly imports `Style` from `prompt_toolkit.styles`, avoiding confusion with `rich.style.Style`.
*   **Compatibility:** The string interpolation in `_get_dynamic_style` (`f"bold {c_agent}"`) assumes the Rich color name is compatible with PTK. Generally, standard ANSI names (cyan, green, red) and Hex codes are supported by both, so this is safe.

### 4. Verification Script

This script simulates the logic of mapping Rich styles to Prompt Toolkit styles to ensure the API usage is correct.

```python
if __name__ == "__main__":
    from rich.console import Console
    from rich.theme import Theme
    from prompt_toolkit.styles import Style as PtkStyle

    # 1. Setup a Mock Rich Console with a specific theme
    my_theme = Theme({
        "info": "bold #00ff00",  # Matrix Green
        "success": "italic red"
    })
    console = Console(theme=my_theme)

    # 2. Extract Logic (Simulating _get_dynamic_style)
    s_info = console.get_style("info")
    # Note: rich.style.Style.color.name returns the string definition
    c_agent = s_info.color.name if s_info.color else "cyan" 
    
    print(f"Extracted 'info' color: {c_agent}")

    # 3. Create PTK Style
    ptk_style = PtkStyle.from_dict({
        "agent": f"bold {c_agent}"
    })

    print(f"PTK Style Dict: {ptk_style.style_rules}")
    
    # Verification
    if "#00ff00" in str(ptk_style.style_rules):
        print("SUCCESS: Rich color mapped to PTK style.")
    else:
        print("FAILURE: Mapping failed.")
