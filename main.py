import os
import vibez
from google import genai
from pathlib import Path

# Initialize the client. If you leave api_key blank, the SDK
# actually checks the GEMINI_API_KEY env var automatically.
client = vibez.configure_genai_client()
#MODEL_ID = "gemini-3-flash-preview"
MODEL_ID = "gemini-3-pro-preview"


def read_role(role_path: str):
    role_text = Path(role_path)
    if not role_text.exists():
        print(f"Error: Prompt file '{role_text}' not found.")
        return
    return role_text.read_text(encoding="utf-8")

SENIOR_DEV = read_role("prompts/senior-dev.md")
JUNIOR_DEV = read_role("prompts/junior-dev.md")
ADVISOR = read_role("prompts/advisor.md")

role = JUNIOR_DEV

#template = read_role("prompts/epi.md")

intent = f""" Create a code snippet such that it takes the response from the generate_content command to genai.client and continuosly appends it to a log file.
- Make the log file configurable and ensure that it's there creating it if it doesn't.
- Put a dividor into the log file such that when we re-run it you can easily see the different outputs.  Append them with a timestamp.
- It isn't necessary to configure the client.  Create this whole thing as a function that takes the client as a parameter
- Also send the response to standard out
"""

prompt = f"""
{role}

{intent}
"""
LOG_FILE="out.log"
vibez.generate_and_continuous_log(client,MODEL_ID,prompt,LOG_FILE)

