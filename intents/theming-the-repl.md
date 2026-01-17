---
status: "Draft"
type: "Intent"
author: "Lead Technical Writer"
last_updated: "2026-01-15"
references: src/vybz/ui.py, src/vybz/repl.py, src/vybz/tools/work.py
---

# Theming the REPL

## Context
Currently, the visual style of the Vybz REPL is hardcoded in `src/vybz/ui.py` 
as the `VYBZ_THEME` constant (a "Cyber/Oceanic" palette). While this fits the 
default aesthetic, users have different preferences for accessibility (High 
Contrast) or personal taste (Dark/Light modes).

## High-Level Intent
I want to externalize the UI color configuration into a TOML file. This allows 
users to define multiple named themes and switch between them via CLI arguments 
at startup or dynamically during a session.

## User Stories
*   As a User, I want to define color mappings in a `themes.toml` file using 
    standard TOML syntax, so I can customize the look of `info`, `warning`, 
    `error`, and `success` messages.
*   As a User, I want to launch Vybz with `vybz ... --theme matrix`, so that 
    the application starts immediately with my preferred aesthetic.
*   As a User, I want to type `/theme dracula` inside the REPL to instantly 
    swap the color palette without restarting the session.
*   As a User, I want the system to fall back to a sensible "default" theme if 
    my configuration is missing or invalid.

## Acceptance Criteria
- [ ] **Configuration File:** The system looks for a `themes.toml` file (likely 
      in the project root or a standard config path).
- [ ] **TOML Structure:** The file supports sections `[theme_name]` containing 
      key-value pairs for Rich styles (e.g., `info = "blue"`, `warning = "red"`).
- [ ] **CLI Argument:** `src/vybz/tools/work.py` accepts an optional `--theme` 
      argument.
- [ ] **REPL Command:** `src/vybz/repl.py` supports the `/theme <name>` command.
- [ ] **Dynamic Updates:** `src/vybz/ui.py` exposes a method to reload the 
      global `Console` object with a new `rich.theme.Theme` at runtime.
- [ ] **Validation:** If a requested theme does not exist in the TOML file, the 
      system prints an error listing available themes and retains the current 
      theme.

## Implementation Hints
*   **Library:** Use `tomllib` (Python 3.11+) to parse the config.
*   **Rich Integration:**
    *   The `Console` object in `ui.py` is global. You may need to create a 
        function `ui.set_theme(theme_name: str)` that constructs a new `Theme` 
        object and updates the console instance.
*   **Default Behavior:**
    *   If `themes.toml` is missing, the hardcoded "Cyber/Oceanic" theme should 
        remain the fallback to ensure the app works out-of-the-box.

