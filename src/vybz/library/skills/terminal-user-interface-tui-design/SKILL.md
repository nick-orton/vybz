---
name: terminal-user-interface-tui-design
description: Expertise in creating delightful, low-friction command-line interfaces
  using modern TUI principles.
---

# Terminal User Interface (TUI) Design
_Expertise in creating delightful, low-friction command-line interfaces using modern TUI principles._

## Knowledge
* #### The Philosophy of CLI UX
      *   **Flow State:** A good CLI never breaks the user's flow. It anticipates intent and offers sensible defaults.
      *   **Discoverability:** Features should be discoverable via `--help`, tab-completion, or intuitive naming conventions (Noun-Verb vs Verb-Noun consistency).
      *   **Glanceability:** Output must be structured (tables, panels) so the most important information jumps out visually. Large walls of text are a failure.
      *   **Feedback:** Every action must have a reaction. Spinners for waiting, checkmarks for success, and clear, actionable error messages.
* #### Visual Hierarchy in Terminals
      *   **Color Theory:** Use color to denote state, not just for decoration.
          *   `Red`: Error/Destructive.
          *   `Yellow`: Warning/Latency.
          *   `Green`: Success/Safe.
          *   `Blue/Cyan`: Metadata/Structure.
          *   `Dim`: Low-priority info (timestamps, IDs).
      *   **Typography:** Use Bold for headers and important values. Use Italic sparingly for descriptions.
* #### The Tooling Stack
      *   **Rich:** The gold standard for output rendering (Panels, Tables, Markdown, Syntax Highlighting).
      *   **Prompt Toolkit:** The engine for interactive REPLs (Keybindings, History, Auto-completion).
      *   **Argparse:** The standard for flag parsing (must be structured logically).

## Abilities
* Refactoring complex, nested command arguments into intuitive, human-readable syntax.
* Designing 'Glanceable' dashboards and status reports using `rich.layout` and `rich.table`.
* Writing error messages that blame the problem, not the user, and suggest immediate fixes.
* Defining standard keybindings (Vi/Emacs) for interactive sessions to match POSIX expectations.
* Creating ASCII/Unicode mockups of interface designs before code is written.
