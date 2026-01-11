import vibez
import sys
from pathlib import Path
from agent import Agent
from context_engine import CodeBase
from squad import Squad

# Initialize the client.
client = vibez.configure_genai_client()

def read_file(filepath: str):
    filetext = Path(filepath)
    if not filetext.exists():
        print(f"Error: file '{filepath}' not found.")
        return
    return filetext.read_text(encoding="utf-8")

cb = CodeBase(Path("."))

intent = f"""
Create a README.md for this code base.

Name the project Vybz Kartel.

Give an overview of what it does and how to use it.
Pay special attention to the design artifacts and the various agents.  Explain
all the agents and what they're for.

Give a complete example workbench.py that copies the essential code from main.py and
calls vibez.generate_and_continuous_log.
"""

#MODEL_ID = "gemini-3-flash-preview"
MODEL_ID = "gemini-3-pro-preview"
LOG_FILE = "out.log"
AGENT = "tech-writer"

try:
    # Listing agents triggers lazy initialization/logging
    available_agents = Squad.list_agents()

    # Select role (defaults to junior-dev, could be arg-parsed)
    if AGENT not in available_agents:
        print(f"Error: Default agent '{AGENT}' not found in {available_agents}")
        sys.exit(1)

    role = Squad.get_agent(AGENT)
except Exception as e:
    print(f"Squad Error: {e}", file=sys.stderr)
    sys.exit(1)


vibez.generate_and_continuous_log(
    client=client,
    model_id=MODEL_ID,
    agent=role,
    intent=intent,
    codebase=cb,
    log_file_path=LOG_FILE
)
