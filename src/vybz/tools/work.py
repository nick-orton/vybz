"""
work.py

The primary entry point for Vybz Kartel. This script configures the
environment, snapshots the codebase, and delegates a task to a specific Agent.
"""

import sys
from pathlib import Path

# Vybz Kartel Core Imports
import vybz.vibez as vibez
from vybz.context_engine import CodeBase
from vybz.squad import Squad

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

# Select the Agent to perform the task.
# Options: 'pm', 'senior-dev', 'junior-dev', 'tech-writer', 'advisor'
TARGET_AGENT = "junior-dev"

# Select the Model.
# Options: 'gemini-3-pro-preview', 'gemini-3-flash-preview'
TARGET_MODEL = "gemini-3-pro-preview"

# Define the Intent.
# Be specific. If using 'junior-dev', provide architectural constraints.
INTENT = """
create a plan of action to carry out the refactoring specified in
`refactor-python-module.md`

Don't re-write all the python code, just indicate what needs to be changed and what is net new
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
