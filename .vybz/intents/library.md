# filename: .vybz/intents/restructure-agents-and-skills.md
---
status: "Completed"
type: "Intent"
author: "Lead Technical Writer"
last_updated: "2026-02-06"
references: 
---

# Agents and Skills Library

## Context
Currently, `agents` and `skills` are nested deep within `src/vybz/`, treating 
them as source code rather than user-configurable data. This makes it difficult
for users to locate, modify, or extend these definitions without diving into 
the package structure.

## High-Level Intent
I want to restructure the project to treat agents and skills as "Libraries" 
that live at the top level of the project during development, and are 
installed to a standard user configuration directory 
(`$HOME/.config/vybz/library/`) for runtime usage.

I would like the vybz codebase to treat these config files in a programatic
way with a Library object that can be used to to discover agents and skills.

## Requirements

### 1. Project Structure Refactor
*   Move the `agents/` directory from `src/vybz/agents/` to the project root.
*   Move the `skills/` directory from `src/vybz/skills/` to the project root.

### 2. Installation Behavior
*   When the package is installed (via `pip`), these configuration files 
    should not just be buried in `site-packages`.
*   The installation process (or the application's first-run logic) should 
    ensure these files are provisioned into `$HOME/.config/vybz/library/`.
*   The system should treat this location as the default "Library" for loading 
    agents and skills.

### 3. Refactoring
*   There should be a Library object which is initialized with a reference to
    all agents and skills
*   Fetching Agents or Skills should come from the library
*   The library should have methods for listing available agents, skills, and
    descriptions so that in the future skills and agents can be searched for.
    

### 4. Configuration & Overrides
*   **Terminology:** Refer to the collection of agents and skills as the 
    "Library".
*   **Config Option:** Add a configuration setting (in `vybzrc` or CLI args) 
    to specify an alternate `library_root`.
    *   Example CLI: `vybz --library /path/to/custom/library ...`
    *   Example Config: `library = "/opt/shared/vybz"`
*   **Precedence:**
    1.  CLI Argument (`--library`)
    2.  Config File Entry
    3.  Environment Variable (`VYBZ_LIBRARY`)
    4.  Default: `$HOME/.config/vybz/library/`
