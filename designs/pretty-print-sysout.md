---
status: "Completed"
type: "Design"
last_updated: "2026-01-10"
references: intents/pretty-print-sysout.md
---

# CLI Output Styling ("Ricing") Specification

## 1. High-Level Intent
Enhance the `vybz` CLI interaction by implementing a visual styling layer
using the `rich` library. The goal is to replace raw text log headers with
visually distinct `Panel` components and apply a "Cyber/Oceanic" (Blues,
Greens, Cyans) color theme to the output. This improves readability by clearly
separating metadata (Agent/Model/Time) from the generated content stream.

## 2. User Stories
* As a User, I want the session metadata (Agent, Model, Intent) displayed in a
  bordered, colored box so that I can instantly distinguish the start of a new
  response.
* As a User, I want the text output to follow a blue/green color scheme to
  match the specific "Vibe Coding" aesthetic.
* As a User, I want the output to remain compatible with standard terminal
  buffers (vi/Tmux) without breaking the existing streaming functionality.

## 3. Acceptance Criteria
- [ ] The `rich` library is added to `pyproject.toml` dependencies.
- [ ] A new module `src/vybz/ui.py` is created to encapsulate styling logic.
- [ ] The output header (Timestamp, Model, Agent, Intent) is rendered using a
      `rich.panel.Panel` or `Table`.
- [ ] The color palette is strictly limited to shades of Blue (`#0000ff`,
      `cyan`), Green (`#00ff00`, `bright_green`), and Teal.
- [ ] The streaming response body text is colored (e.g., `bright_cyan` or
      `green`) rather than default terminal white/grey.
- [ ] File logging (`interaction_log.txt`) remains plain text (strip ANSI
      codes) or retains readability.

## 4. Implementation Hints (Technical)
* **Library:** Use `rich` (standard Python library for terminal UI).
* **Theme:**
  ```python
  from rich.theme import Theme
  theme = Theme({
      "info": "cyan",
      "warning": "magenta",
      "header": "bold bright_green",
      "content": "#00ffaf" # Spring Green
  })
  ```
* **Architecture:**
  - Create `src/vybz/ui.py`.
  - Expose a function `print_header(agent, model, intent)` that uses a
    `Console` object.
  - Expose a helper for the stream, or simply update `vibez.py` to write to
    `sys.stdout` using ANSI codes derived from the theme if `rich` streaming
    is too heavy/blocking.
* **Streaming Consideration:** `rich.live` can be jumpy. For the *content*, it
  is acceptable to just `console.print(chunk, end="")` with a set style, rather
  than a full Live display.
* **FreeBSD/POSIX:** `rich` auto-detects terminal capabilities. Ensure
  `force_terminal=True` can be set if piping breaks colors, though usually
  auto-detect is sufficient.

## 5. Execution Plan
1. [ ] **Dependencies:** Add `rich>=13.0` to `pyproject.toml`.
2. [ ] **UI Module:** Create `src/vybz/ui.py` with a configured global
       `Console` and the specific Blue/Green `Theme`.
3. [ ] **Header Logic:** Implement the `render_header` function in `ui.py`
       using `rich.panel.Panel` and `rich.table.Table` for layout.
4. [ ] **Integration:** Refactor `src/vybz/vibez.py` to import `ui` and
       replace the f-string header print with `ui.render_header()`.
5. [ ] **Stream Styling:** Update the chunk writing loop in `vibez.py` to use
       the themed color.
