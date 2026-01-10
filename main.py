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

intent = f""" create a module that gets a google genai client and prints out the models available for the current API Key.  It should filter for the generative models.  I want to use these strings in the client.models.generate_content method.  It should return a list of strings
"""

final_prompt = f"""
{role}

{intent}
"""
response = client.models.generate_content(
    model=MODEL_ID,
    contents=final_prompt
)

print(response.text)
