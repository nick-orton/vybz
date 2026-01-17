---
status: "Completed"
type: "Design"
author: "PM Lead"
last_updated: "2026-01-15"
references: intents/theming-the-repl.md
---

# Theming the REPL Specification

## 1. High-Level Intent
Externalize the visual styling of the Vybz REPL from hardcoded Python constants
into a user-editable TOML configuration file. This project transforms the UI
from a static "Cyber/Oceanic" aesthetic into a dynamic system that supports
custom color palettes (Themes). Users will be able to define themes in
`themes.toml`, select them at launch via CLI arguments, and switch them on the
fly during interactive sessions.

## 2. User Stories
* As a User, I want to edit a `themes.toml` file to customize the colors of
  `info`, `warning`, and `error` messages to match my terminal's palette.
* As a User, I want to launch Vybz with `vybz ... --theme high-contrast` to
  ensure accessibility immediately upon startup.
* As a User, I want to type `/theme matrix` inside the REPL to switch the visual
  context without restarting my session.
* As a User, I want the system to fall back to the standard "Cyber" theme if my
  configuration file is missing or contains errors.

## 3. Acceptance Criteria
- [ ] **Configuration:** A `themes.toml` file is loaded from the current working
      directory (or package defaults).
- [ ] **Schema:** The TOML file supports named sections (e.g., `[matrix]`)
      containing key-value pairs for Rich styles.
- [ ] **Phase 1 (Extraction):** The hardcoded `VYBZ_THEME` in `src/vybz/ui.py`
      is replaced by a loader that reads "default" from TOML, falling back only
      if the file is missing.
- [ ] **Phase 2 (CLI):** `src/vybz/tools/work.py` accepts `--theme <name>`.
- [ ] **Phase 3 (Runtime):** The REPL accepts `/theme <name>`, updates the
      global Console object, and provides immediate visual feedback.
- [ ] **Validation:** Invalid theme names trigger a styled error message listing
      available options.

## 4. Implementation Hints (Technical)
*   **Module:** `src/vybz/ui.py`
    *   Introduce a `ThemeManager` class or a `load_theme(name)` function.
    *   Use `tomllib` (Python 3.11+) for parsing.
    *   **Hot-Swapping:** Since `rich.console.Console` copies the theme on init,
        you cannot simply mutate `console.theme`. You must re-instantiate the
        global `console` and `error_console` objects.
        *   *Note:* Ensure dependent modules access console via `ui.console`
            (namespace lookup) rather than importing `console` directly, or the
            swap won't propagate.
*   **Config Location:** Check `Path.cwd() / "themes.toml"`.
*   **Default Theme:** Keep the existing "Cyber/Oceanic" definitions in code as
    the `FALLBACK_THEME` constant to ensure the app is never broken.

## 5. Execution Plan

### Phase 1: Configuration Extraction
1.  [ ] **Create Config:** Create `themes.toml` in the project root with the
        current "default" (Cyber) and a new "matrix" (Green/Black) theme.
2.  [ ] **Refactor UI:** Modify `src/vybz/ui.py` to load this file.
3.  [ ] **Init Logic:** Ensure `ui` initializes with the "default" theme defined
        in the TOML.

### Phase 2: CLI Integration
1.  [ ] **Update CLI:** Modify `src/vybz/tools/work.py` to add
        `--theme <str>`.
2.  [ ] **Wire Up:** Pass the argument to a new `ui.set_theme(name)` function
        before the agent or REPL starts.

### Phase 3: Dynamic Switching
1.  [ ] **Update REPL:** Add `/theme` command to `src/vybz/repl.py`.
2.  [ ] **Implement Swap:** Ensure `ui.set_theme` correctly replaces the global
        console instances.
3.  [ ] **Verify:** Test switching themes mid-session and verify the colors
        change immediately.
