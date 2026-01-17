---
status: "Draft"
type: "Design"
author: "PM Lead"
last_updated: "2026-01-16"
references: intents/ux-critique.md, designs/theming-the-repl-specification.md
---

# REPL Dynamic Theming Specification

## 1. High-Level Intent
Address the "Hardcoded Styling" friction point identified in the UX Critique.
Currently, the REPL prompt in `src/vybz/repl.py` uses hardcoded HTML colors
(e.g., `<style fg='cyan'>`), which completely ignores the active application
theme. This results in visual inconsistency—for example, a user running the
Green/Black "Matrix" theme still sees a Cyan prompt. We will refactor the REPL
to dynamically derive its input styles from the active `rich` theme configuration.

## 2. User Stories
* As a User, when I launch Vybz with `--theme matrix`, I want the prompt's agent
  label to be Green (matching the theme's `info` color), not Cyan.
* As a User, when I switch themes dynamically via `/theme dracula`, I want the
  prompt colors to update immediately to match the new palette.
* As a User, I want a consistent visual experience where the Input line feels
  like it belongs to the same application as the Output stream.

## 3. Acceptance Criteria
- [ ] **Removal of Hardcoding:** All string literals defining colors (e.g.,
      `'cyan'`, `'green'`, `'#00ff00'`) are removed from `src/vybz/repl.py`.
- [ ] **Dynamic Mapping:** The `prompt_toolkit` Style object is constructed at
      runtime by querying the global `vybz.ui.console` styles.
- [ ] **Semantic Mapping:**
    - The Agent Name (`class:agent`) inherits the color of the theme's `info`
      style.
    - The Separator (`class:separator`) inherits the color of the theme's
      `success` style.
    - The Metadata (`class:meta`) inherits the color of the theme's `timestamp`
      style.
- [ ] **Hot-Swap Support:** The `/theme` command triggers a regeneration of the
      style mapping, ensuring the prompt updates instantly.

## 4. Implementation Hints (Technical)

### 4.1. The Bridge (Rich -> Prompt Toolkit)
`rich` and `prompt_toolkit` both have classes named `Style`, but they are
incompatible. We must map them manually.

**Logic:**
1.  Access the global console's theme: `ui.console.get_style("style_name")`.
2.  Extract the color definition (Hex or ANSI name).
3.  Build a dictionary for `prompt_toolkit.styles.Style.from_dict`.

```python
# src/vybz/repl.py

from prompt_toolkit.styles import Style as PtkStyle
from vybz import ui

def _get_dynamic_style(self) -> PtkStyle:
    # 1. Retrieve Rich styles from the active console
    # Note: We use the semantic keys defined in themes.toml
    s_info = ui.console.get_style("info")
    s_success = ui.console.get_style("success")
    s_time = ui.console.get_style("timestamp")

    # 2. Extract color strings (e.g., "#00ff00" or "cyan")
    # Rich Style objects have a 'color' attribute which has a 'name'
    c_agent = s_info.color.name if s_info.color else "cyan"
    c_sep = s_success.color.name if s_success.color else "green"
    c_meta = s_time.color.name if s_time.color else "gray"

    # 3. Construct PTK Style
    return PtkStyle.from_dict({
        "agent": f"bold {c_agent}",
        "separator": f"bold {c_sep}",
        "meta": c_meta,
    })
```

### 4.2. Loop Integration
In `ReplSession.start()`, ensure `_get_dynamic_style` is called (or passed as a
callable if PTK supports it, otherwise re-evaluated) on every loop iteration or
at least after a `/theme` command is executed.

## 5. Execution Plan
1. [ ] **Implement Mapper:** Add the `_get_dynamic_style` helper method to
       `ReplSession` in `src/vybz/repl.py`.
2. [ ] **Update Prompt Call:** Modify the `self.session.prompt(...)` call to use
       the dynamic style object.
3. [ ] **Verify:**
       1. Launch `vybz junior-dev --theme matrix`.
       2. Confirm prompt is Green.
       3. Type `/theme default`.
       4. Confirm prompt turns Cyan.
