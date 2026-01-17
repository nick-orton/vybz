---
status: "Completed"
type: "Intent"
author: "Lead Technical Writer"
last_updated: "2026-01-15"
references: src/vybz/tools/work.py, src/vybz/theme.py, src/vybz/repl.py
---

# Persist User Settings via RC Config File

## Context
Currently, user preferences for the Vybz environment—specifically the Input Mode
(`--mode vi/emacs`) and the UI Theme (`--theme`)—are ephemeral. A user must
specify them via command-line arguments every time they launch the application
or rely on external shell aliases. This creates friction and breaks the "Flow"
state required for Vibe Coding.

## High-Level Intent
I want to implement an optional, user-level configuration file (a "dotfile")
living in the user's home directory. Vybz should read this file at startup to
populate default settings for the session.

## User Stories
*   As a User, I want to create a `~/.vybz.toml` file containing `mode = "vi"`,
    so that I default to Vi keybindings without typing `--mode vi` every time.
*   As a User, I want to define my preferred theme permanently in this config
    file.
*   As a User, I want Command Line Arguments to take precedence over the config
    file, so I can temporarily override my defaults (e.g., `vybz --theme
    matrix` overrides a config set to `dracula`).

## Technical Requirements

### 1. Configuration Discovery
The system should look for the configuration file in the following order of
precedence:
1.  `$HOME/.vybzrc`
2.  (Optional Future) `$XDG_CONFIG_HOME/vybz.config`

### 2. File Format
Use **TOML** to maintain consistency with the existing `agents/*.toml` and
`themes.toml` architecture.  Don't use the .toml extention, though.  Use the 
naming format above

**Example Schema:**
```toml
theme = "dracula"
mode = "vi"
model = "gemini-3-pro-preview"
```

The contents of the file should be optional.  If a specific config such as 
`theme` is missing, the system will go with defaults.

### 3. Integration Logic
*   **Module:** `src/vybz/tools/work.py` (The CLI Entry Point).
*   **Precedence Hierarchy:**
    1.  **CLI Flag:** (e.g., `--mode emacs` explicit flag).
    2.  **User Config:** (Value found in `~/.vybzrc`).
    3.  **System Default:** (Hardcoded fallback, e.g., `emacs`, `default`).

## Implementation Hints
*   Use `pathlib.Path.home()` to resolve the user directory.
*   Use `tomllib` (Python 3.11+) to parse the file.
*   This logic should likely execute *before* `argparse` finalizes, or be used
    to set the `default` values of the `argparse` arguments dynamically.

