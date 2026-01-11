# Vybz Kartel: The Vibe Coding Workbench

**Vybz Kartel** is a terminal-centric, AI-orchestrated coding workbench designed
for POSIX environments (FreeBSD/Debian). It leverages the **Google Gemini 3.0**
models via the unified `google-genai` SDK (v1.57+) to facilitate "Vibe
Coding"—a workflow that prioritizes flow state, low-friction CLI interactions,
and high-velocity software evolution.

This system is not an autocomplete plugin; it is a **Context Engine** that
snapshots your entire codebase, injects it into specialized AI Personas
(Agents), and streams architectural plans, code, or documentation directly to
standard output and logs.

## Core Features

*   **The Squad (Agent System):** A collection of specialized AI personas 
    defined in TOML configuration files.  These agents design features, write
    code or even create new agents.
*   **Context Engine:** A robust filesystem snapshot tool (`CodeBase`) that
    respects `.gitignore`, excludes binary files, and serializes your source
    tree into Markdown for accurate LLM context.
*   **Continuous Logging:** All interactions are streamed to `stdout` for real-
    time feedback and simultaneously appended to log files for history
    tracking.
*   **Design-First Architecture:** Prompts are treated as source code, stored
    in `designs/`, and managed via version control.

## Prerequisites

*   **Python:** 3.11 or higher.
*   **API Key:** Google Gemini API key (`GEMINI_API_KEY`).
*   **OS:** Code is POSIX compliant tailored for FreeBSD and Debian
*   **Terminal:** Tmux and your preferred text editor recommended for optimal 
    rendering.

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
    Create a `.env` file in the root directory:
    ```bash
    GEMINI_API_KEY="your-google-api-key-here"
    ```

## The Squad: Specialized Agents

The logic of Vybz Kartel is driven by **Agents**. These are not generic
chatbots; they are strict personas defined in `agents/*.toml`.

### 1. Advisor (`agents/advisor.toml`)
**The Meta-Architect.** The Advisor does not write application code. Its sole
purpose is to design *other* agents. It understands prompt engineering, context
windows, and the specific strengths of Gemini models. Use the Advisor when you
need to create a new role (e.g., a "QA Engineer" or "Security Auditor").

### 2. PM Lead (`agents/pm.toml`)
**The Ambiguity Filter.** The PM transforms vague user intent into concrete,
atomic technical specifications. It produces User Stories, Acceptance Criteria,
and Implementation Hints. It bridges the gap between "I want a blog" and strictly
defined Python tasks.

### 3. Senior Python Architect (`agents/senior-dev.toml`)
**The Brain.** This agent focuses on system design, PEP standards, and
maintainability. It refuses to write code without first analyzing architectural
impact. It enforces the use of the `google-genai` v1.57 SDK and modern Python
3.11+ syntax.

### 4. Tactical Python Architect (`agents/junior-dev.toml`)
**The Hands.** A "code engine" designed for speed. It assumes the architecture
decisions are already made. It produces high-volume, compliant code blocks with
minimal chatter.

### 5. Lead Technical Writer (`agents/tech-writer.toml`)
**The Translator.** Analyzes diffs and code logic to produce human-centric
documentation. It generates:
*   `README.md` files (it wrote this one).
*   Conventional Commit messages (via `vybz-commit`).
*   Docstrings adhering to Google Style.

## Design Artifacts

The `designs/` directory contains the "Source of Truth" for the project's
intelligence. In Vybz Kartel, **Prompt Engineering is Code**.

*   **`designs/codebase.md`**: Defines how the system sees itself (the
    specification for the Context Engine).
*   **`designs/pm-agent.md`**: The blueprint used to generate the PM agent.
*   **`designs/agent-plans.md`**: The meta-structure for how agents are stored
    and loaded.

Modifying these files allows you to fundamentally alter the behavior of the
system using the system itself.

## Usage: The Workbench

The core interaction model is the `vybz` CLI. It initializes the environment,
loads a specific agent, creates a snapshot of the code, and submits an intent
directly from your shell.

### CLI Example

To execute a task, pass the agent name and your intent string as positional
arguments. You can optionally attach the current codebase context, specify a
model, and define a log output.

```bash
vybz junior-dev \
    "Create a new utility module in 'bin/cleanup.py'. \
    It should recursively delete all '__pycache__' directories and \
    '.DS_Store' files in the current directory. \
    Ensure it uses pathlib and handles PermissionErrors gracefully." \
    --codebase . \
    --model gemini-3-flash-preview \
    --log-file out.log
```

The output will stream to your terminal and be logged to `out.log`. Code blocks
will be formatted in Markdown, ready to be piped into files or copied into your
editor.


## CLI Utilities 

Vybz Kartel includes standalone Python executables to automate routine tasks 
and enforce style constraints. These tools are designed to be chainable and
POSIX-compliant.

### 1. Auto-Commit Generator (`vybz-commit`)
This script utilizes the **Lead Technical Writer** agent to analyze your
currently staged git changes and generate a Conventional Commit message.

*   **Logic:** It reads `git diff --cached`, loads the `tech-writer` agent via
    `squad.py`, and outputs a formatted message to `stdout`.
*   **Context Injection:** You can optionally pass an agent interaction log.
    The script will use the log to understand the *intent* (Why) while using
    the diff to verify the *implementation* (What).

**Usage:**
```bash
# 1. Stage your changes
git add .

# 2. Generate message (requires GEMINI_API_KEY in env)
vybz-commit

# 3. Generate with context from a previous coding session
vybz-commit --log-file out.log
```

### 2. Markdown Formatter (`vybz-fmt`)
A utility to enforce hard line wrapping on Markdown files. This ensures that
documentation and git commit messages remain readable in terminal buffers and
`git log` outputs without horizontal scrolling.

*   **Default Width:** 80 characters (configurable).
*   **Logic:** It respects Markdown syntax, preserving headers, code blocks,
    and list indentation while reflowing paragraph text.

**Usage:**
```bash
# Format a file and output to stdout
vybz-fmt docs/architecture.md

# Set a custom width
vybz-fmt README.md -w 100
```

### Recommended Workflow: The `gc` Alias
For the optimal "Vibe Coding" experience, combine these tools to automate your
commit workflow. Add the following alias to your shell configuration (as seen
in `env.sh`):

```bash
alias gc="vybz-commit > /tmp/commit; vybz-fmt /tmp/commit | git commit -F - -e"
```

**Workflow:**
1.  `git add .`
2.  `gc`
3.  The script generates a message, formats it to 80 chars, and opens your
    editor (`-e`) for final review before committing.
