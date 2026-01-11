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
    pip install -r requirements.txt
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
*   Conventional Commit messages (via `bin/autocommit_gen.py`).
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

The core interaction model is the `workbench.py` script. It initializes the
environment, loads a specific agent, creates a snapshot of the code, and submits
an intent.

### Example Workbench

Save the following as `workbench.py` in the root directory to start coding.

```python
"""
workbench.py

The primary entry point for Vybz Kartel. This script configures the
environment, snapshots the codebase, and delegates a task to a specific Agent.
"""

import sys
from pathlib import Path

# Vybz Kartel Core Imports
import vibez
from context_engine import CodeBase
from squad import Squad

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

# Select the Agent to perform the task.
# Options: 'pm', 'senior-dev', 'junior-dev', 'tech-writer', 'advisor'
TARGET_AGENT = "junior-dev"

# Select the Model.
# Options: 'gemini-3-pro-preview', 'gemini-3-flash-preview'
TARGET_MODEL = "gemini-3-flash-preview"

# Define the Intent.
# Be specific. If using 'junior-dev', provide architectural constraints.
INTENT = """
Create a new utility module in 'bin/cleanup.py'.
It should recursively delete all '__pycache__' directories and '.DS_Store'
files in the current directory.
Ensure it uses pathlib and handles PermissionErrors gracefully.
"""

# Output log file
LOG_FILE = "out.log"

# -----------------------------------------------------------------------------
# Execution
# -----------------------------------------------------------------------------

def main():
    try:
        # 1. Initialize the Google GenAI Client
        client = vibez.configure_genai_client()

        # 2. Snapshot the current Codebase
        # This reads the filesystem, respecting .gitignore
        print("[-] Snapshotting codebase...")
        codebase = CodeBase(Path("."))

        # 3. Load the Agent from the Squad
        print(f"[-] Activating Agent: {TARGET_AGENT}...")
        agent = Squad.get_agent(TARGET_AGENT)

        print(f"[-] Starting Vibe Session with {TARGET_MODEL}...")
        print("-" * 60)

        # 4. Generate and Stream
        # This functions sends the prompt + codebase to Gemini and logs output
        vibez.generate_and_continuous_log(
            client=client,
            model_id=TARGET_MODEL,
            agent=agent,
            intent=INTENT,
            codebase=codebase,
            log_file_path=LOG_FILE
        )

    except Exception as e:
        print(f"\n[!] Critical Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### Running the Workbench

```bash
python workbench.py
```

The output will stream to your terminal and be logged to out.log. Code blocks 
will be formatted in Markdown, ready to be piped into files or copied into your
editor.

## CLI Utilities (`bin/`)

Vybz Kartel includes standalone Python scripts in the `bin/` directory to
automate routine tasks and enforce style constraints. These tools are designed
to be chainable and POSIX-compliant.

### 1. Auto-Commit Generator (`bin/autocommit_gen.py`)
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
bin/autocommit_gen.py

# 3. Generate with context from a previous coding session
bin/autocommit_gen.py --log-file out.log
```

### 2. Markdown Formatter (`bin/mdformat`)
A utility to enforce hard line wrapping on Markdown files. This ensures that
documentation and git commit messages remain readable in terminal buffers and
`git log` outputs without horizontal scrolling.

*   **Default Width:** 80 characters (configurable).
*   **Logic:** It respects Markdown syntax, preserving headers, code blocks,
    and list indentation while reflowing paragraph text.

**Usage:**
```bash
# Format a file and output to stdout
bin/mdformat docs/architecture.md

# Set a custom width
bin/mdformat README.md -w 100
```

### Recommended Workflow: The `gc` Alias
For the optimal "Vibe Coding" experience, combine these tools to automate your
commit workflow. Add the following alias to your shell configuration (as seen
in `env.sh`):

```bash
alias gc="./bin/autocommit_gen.py > /tmp/commit; ./bin/mdformat /tmp/commit | git commit -F - -e"
```

**Workflow:**
1.  `git add .`
2.  `gc`
3.  The script generates a message, formats it to 80 chars, and opens your
    editor (`-e`) for final review before committing.
