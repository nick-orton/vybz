import os
import vibez
from google import genai
from pathlib import Path
from agent import Agent

# Initialize the client.
client = vibez.configure_genai_client()

def read_file(filepath: str):
    filetext = Path(filepath)
    if not filetext.exists():
        print(f"Error: file '{filepath}' not found.")
        return
    return filetext.read_text(encoding="utf-8")

SENIOR_DEV = Agent.from_toml(Path("agents/senior-dev.toml"))
print(f"    Loaded: {SENIOR_DEV.get_identity()}")

JUNIOR_DEV = Agent.from_toml(Path("agents/junior-dev.toml"))
print(f"    Loaded: {JUNIOR_DEV.get_identity()}")

ADVISOR = Agent.from_toml(Path("agents/advisor.toml"))
print(f"    Loaded: {ADVISOR.get_identity()}")

role = SENIOR_DEV

design = read_file("designs/git-commit-helper.txt")
intent = f"""
{design}
"""

#MODEL_ID = "gemini-3-flash-preview"
MODEL_ID = "gemini-3-pro-preview"
LOG_FILE="out.log"

vibez.generate_and_continuous_log(
    client=client,
    model_id=MODEL_ID,
    agent=role,
    intent=intent,
    log_file_path=LOG_FILE
)
