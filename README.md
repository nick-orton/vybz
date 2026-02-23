# Vybz Kartel: AI-Orchestrated Coding Workbench

**Vybz** is a high-velocity coding workbench designed for POSIX
environments. It transforms your local terminal into a sophisticated
development studio where specialized AI Agents collaborate on your source
tree.

Built on a **Client-Server Architecture**, Vybz separates heavy-duty
LLM orchestration (`vybzd`) from the interactive user experience (`vybz`),
providing a stateful, low-latency "Vibe Coding" workflow.

## Core Architecture

Vybz operates on a client-server model to ensure stability and state
persistence:

- **`vybzd` (The Server):** A persistent background process that manages
  agent sessions, context snapshots, and the `google-genai` SDK
  connections. It maintains the "Source of Truth" for your project's
  state.
- **`vybz` (The Client):** A lightweight, interactive REPL powered by
  `prompt_toolkit`. It communicates with the server via an internal API
  to provide real-time feedback and high-fidelity TUI rendering.

## Key Features

- **The Squad:** Specialized AI agents defined in TOML (e.g., `senior-dev`,
  `pm`, `tech-writer`). Each agent possesses unique system instructions
  and personality.
- **Composable Skills:** Agents inherit capabilities from modular,
  directory-based "Skills" (adhering to the AgentSkills.io standard).
- **Context Engine:** Automatic codebase snapshotting that respects
  `.gitignore`, enabling agents to "see" your files and directory structure.
- **Artifact Management:** Slash commands like `/save` automatically
  extract, name, and route code blocks, designs, and blueprints to the
  correct directories based on metadata.
- **Advanced REPL:** Supports Vi/Emacs keybindings, multi-line input, and
  custom themes (Dracula, Matrix, etc.).

## Prerequisites

- **Python:** 3.11 or higher.
- **API Key:** Google Gemini API key (`GEMINI_API_KEY`).
- **OS:** POSIX-compliant (FreeBSD/Linux/macOS).

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/nick-orton/vybz.git
    cd vybz
    ```

2.  **Set up the environment:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -e .
    ```

3.  **Configure API Key:**
    ```bash
    export GEMINI_API_KEY="your-google-api-key-here"
    ```

## Quick Start

### 1. Start the Server
In a dedicated terminal (or tmux pane), launch the Vybz daemon:
```bash
vybzd
```

### 2. Launch the Client
In another terminal, start an interactive session with an agent:
```bash
# Start a session with the senior developer
vybz senior-dev --codebase .
```

## Interactive Commands

Inside the REPL, use slash commands to manage the session:

- **Alt+Enter** (or `Esc` then `Enter`): Submit input to the agent.
- **`/agent <name>`**: Switch the active agent in the current session.
- **`/clear`**: Clear the terminal screen (preserves chat history).
- **`/set <mode>`**: Set input mode (`vi` or `emacs`).
- **`/save`**: Extract and save code/docs from the agent's last response.
- **`/update`**: Refresh the codebase context (e.g., after manual file edits).
- **`/load <path>`**: Manually inject a specific file's content into context.
- **`/skills`**: Display the active agent's current capabilities.
- **`/uplevel <path>`**: Inject a local skill directory at runtime.
- **`/downlevel <id>`**: Remove a skill from the active session.
- **`/theme <name>`**: Switch the UI theme (e.g., `matrix`, `dracula`).
- **`/help`**: List all available commands and keybindings.
- **`/exit`**: End the session.

## The Squad: Specialized Agents

Agents are defined in `src/vybz/agents/*.toml`. Use the right agent for the
right task:

*   **`advisor`:** The meta-agent. Designs prompts for new agents.
*   **`pm` (Product Manager):** Translates vague intent into strict technical
    specifications. Use this first for new features.
*   **`senior-dev`:** Focuses on architecture, safety, and PEP standards.
    Refuses to write code without impact analysis.
*   **`junior-dev`:** High-speed code generator. Assumes architecture is
    decided.
*   **`tech-writer`:** Generates documentation and commit messages.
*   **`librarian`:** Organizes documentation and ensures doc metadata is 
    up-to-date.
*   **`qa`:** Principal QA Engineer. Specializes in exploratory testing and 
    root cause analysis.
*   **`test-dev`:** QA Automation Lead. Specializes in hermetic `pytest` 
    suites and mocking.
*   **`sysadmin`:** Unix Greybeard. Writes robust, idempotent shell scripts 
    for POSIX systems.
*   **`ux-designer`:** Principal TUI Designer. Designs low-friction terminal 
    interfaces using `rich`.

### Composable Skills

Agents are constructed from modular **Skills** defined in
`src/vybz/skills/`. Vybz adheres to the [AgentSkills.io](https://agentskills.io)
standard, which promotes portable, directory-based capabilities. Each skill is
a self-contained unit comprising a `SKILL.md` file with YAML Frontmatter and
Markdown instructions.

This architecture ensures that critical constraints—such as Python coding
standards, OS-specific shell rules, or SDK versions—are defined once and
shared across the entire Squad.

A standard skill includes:

*   **Metadata:** Defined in YAML Frontmatter, specifying the `name` and
    `description` used for [Resource Discovery](https://agentskills.io/specification).
*   **Instructions:** The Markdown body providing the facts and rules the agent
    applies that knowledge. These are behavioral rules and specific directives 
    (e.g., "Always implement PEP 484 type hints" or "Prefer piping `grep` into 
    `awk`").

Example skills include:
*   **`modern-python-standards`**: PEP 8, Type Hinting, and Docstring rules.
*   **`unix-systems-mastery`**: OS-specific constraints (FreeBSD 15.0, `sh` vs `bash`).
*   **`google-genai-v1-57`**: Strict syntax rules for the unified Gemini SDK.

## Design Philosophy: Instructions as Code

In Vybz Kartel, **Prompt Engineering is Source Code**. We do not rely on 
ephemeral chat history to build complex software. Instead, we treat natural 
language instructions as persistent artifacts that evolve through a strict 
lifecycle.

The agents are **opinionated** about the location and structure of these files.
They expect specific artifacts to exist in specific directories to function 
correctly.

### The Workflow

1.  **Intents (`intents/`)**
    *   **Author:** Human User.
    *   **Purpose:** Raw, high-level desires. These can be vague or 
        stream-of-consciousness (e.g., "I want a dark mode feature").
    *   **Consumer:** The **PM Agent** reads these to understand the "Why."

2.  **Designs (`designs/`)**
    *   **Author:** PM Agent.
    *   **Purpose:** Translation of Intents into concrete specifications. These
        files contain User Stories, Acceptance Criteria, and Technical 
        Constraints.
    *   **Consumer:** The **Senior Developer** uses these as the "Source of 
        Truth" for functionality.

3.  **Blueprints (`blueprints/`)**
    *   **Author:** Senior Developer Agent.
    *   **Purpose:** Architectural implementation plans. These define *how* the
        code changes will occur, mapping out module structures, refactoring 
        strategies, and dependency management.
    *   **Consumer:** The **Junior Developer** follows these blueprints to 
        generate code without needing to make architectural decisions.

By formalizing this pipeline, Vybz Kartel ensures that code generation is not a
"guess" by an LLM, but the result of a structured engineering process.

#### Metadata & Lifecycle Tracking

To bridge the gap between human prose and machine logic, every artifact in the
`designs/` and `blueprints/` directories should begin with **YAML Frontmatter**.
This metadata transforms static Markdown into a queryable knowledge graph,
enabling the **Librarian** agent to track document lineage and lifecycle states.

**Schema:**

```yaml
---
status: "Draft"        # Options: [Draft, Proposed, In Progress, Completed]
type: "Design"         # Options: [Design, Intent, Blueprint]
last_updated: "2026-01-11"
references: designs/feature-spec.md  # Comma-separated list of upstream docs
---
```

## User Configuration

To persist your preferred workflow settings (like Vi keybindings or UI themes),
you can create a configuration file. Vybz looks for this file at startup.

**File Locations:**
1. `~/.vybzrc`
2. `~/.config/vybz.config`

**Format:** TOML

**Example:**
```toml
# ~/.vybzrc
mode = "vi"               # Options: vi, emacs
theme = "matrix"          # Options: default, matrix, dracula
model = "gemini-3-flash-preview"
```

See `vybzrc.example` for more details.

**Precedence:**
CLI Arguments (e.g., `--mode emacs`) override Config File settings, which
override System Defaults.

## CLI Utilities

Vybz Kartel includes standalone tools to automate routine maintenance tasks.

### Auto-Commit Generator (`vybz-commit`)
Uses the **Lead Technical Writer** agent to analyze staged git changes and
generate a Conventional Commit message.

**Usage:**
```bash
# 1. Stage changes
git add .

# 2. Generate commit message based on diff
vybz-commit

# 3. (Optional) Provide context from an interaction log
vybz-commit --log-file /tmp/vybz.log
```

### Markdown Formatter (`vybz-fmt`)
Enforces a hard wrap limit (default: 80 chars) on Markdown files. This ensures
readability in terminal buffers and git logs.

**Usage:**
```bash
# Format a file and output to stdout
vybz-fmt README.md > README.md.tmp && mv README.md.tmp README.md

# Custom width
vybz-fmt docs/spec.md -w 100
```

## Development

Vybz uses `pytest` for testing. The suite is hermetic and does not call
the live API.

```bash
# Run all tests
pytest

# Run tests for the server specifically
pytest tests/vybz/server/
```

## License

MIT License. See `LICENSE` for details.
```
