# Vybz Kartel: AI-Orchestrated Vibe Coding Workbench

**Vybz Kartel** is a terminal-centric, AI-orchestrated coding workbench designed
for POSIX environments (FreeBSD/Debian). It leverages the **Google Gemini 3.0**
models via the unified `google-genai` SDK (v1.57+) to facilitate "Vibe
Coding"—a workflow that prioritizes flow state, low-friction CLI interactions,
and high-velocity software evolution.

This system is not a simple autocomplete plugin. It is a **Context Engine**
that snapshots your local filesystem, injects it into specialized AI Personas
(Agents), and enables stateful, multi-turn architectural discussions directly
in your terminal.

## Core Features

*   **Interactive REPL:** A robust Read-Eval-Print Loop powered by
    `prompt_toolkit`. Supports multi-line input, slash commands, and persistent
    chat history for iterative development.
*   **The Squad:** A modular system of specialized AI agents defined in TOML.
    Agents range from "Junior Developers" (code generation) to "Product
    Managers" (specification) and "Technical Writers" (documentation).
*   **Context Engine:** A read-only filesystem snapshot tool (`CodeBase`) that
    respects `.gitignore`, excludes binary files, and serializes your source
    tree into Markdown for accurate LLM context.
*   **TUI Experience:** Styled output using `rich` with a "Cyber/Oceanic"
    theme, ensuring clear visual separation between user input, system logs,
    and agent responses.

## Prerequisites

*   **Python:** 3.11 or higher.
*   **API Key:** Google Gemini API key (`GEMINI_API_KEY`).
*   **OS:** POSIX-compliant (FreeBSD/Linux/macOS).
*   **Terminal:** A modern terminal emulator. Neovim and Tmux are recommended
    for optimal rendering.

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

## Usage

The primary interface is the `vybz` command. It supports two modes:
**Interactive (Recommended)** and **One-Shot**.

### 1. Interactive Mode (REPL)
Launch a stateful chat session with a specific agent. This mode allows you to
refine requirements, ask follow-up questions, and paste large blocks of code
for refactoring.

**Command:**
```bash
# Syntax: vybz <agent> [-c path/to/codebase]
vybz junior-dev --codebase .
```

**Keybindings & Commands:**
*   **Alt+Enter** (or `Esc` then `Enter`): Submit input to the agent.
*   **Enter**: Insert a newline (allows for multi-line code pasting).
*   **`/agent [name]`**: Switch active agent (e.g., `/agent pm`). Type without
    arguments to list available agents.
*   **`/clear`**: Clear the terminal screen (preserves chat history).
*   **`/save`**: Auto-save the last generated artifact to the appropriate
    directory based on its metadata.
*   **`/help`**: Show available commands and keybindings.
*   **`/exit`**: End the session.

### 2. One-Shot Mode (Legacy)
Execute a single, fire-and-forget task. Useful for quick questions or scripting.

**Command:**
```bash
# Syntax: vybz <agent> "Your instruction here"
vybz senior-dev "Explain the factory pattern in Python"
```

### Context Injection (`--codebase`)
The `--codebase` (or `-c`) snapshots the target directory
and injects it into the Agent's system instructions.

*   **Without `-c`:** The agent runs in "Greenfield" mode.
*   **With `-c .`:** The agent "sees" your current project structure and file
    contents (respecting `.gitignore`).

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
    up-to-date

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

### Recommended Workflow Alias
Add this alias to your shell configuration (e.g., `.bashrc` or `.zshrc`) to
streamline your commit workflow:

```bash
alias gc="vybz-commit > /tmp/commit; vybz-fmt /tmp/commit | git commit -F - -e"
```

**Workflow:**
1.  `git add .`
2.  `gc` -> Generates message, formats it, and opens your editor for review.

## Project Structure

*   `src/vybz/`: Core source code.
*   `src/vybz/agents/`: TOML definitions for AI personas.
*   `designs/`: High-level specifications and designs.
*   `blueprints/`: Architectural implementation plans.
*   `intents/`: Raw user intents (historical).

## License

MIT License. See `LICENSE` for details.
----------------------------------------
