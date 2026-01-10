import os
from google import genai
from pathlib import Path
from vibez import configure_genai_client

# Initialize the client. If you leave api_key blank, the SDK
# actually checks the GEMINI_API_KEY env var automatically.
client = configure_genai_client()
#MODEL_ID = "gemini-3-flash-preview"
MODEL_ID = "gemini-3-pro-preview"


def read_role(role_path: str):
    role_text = Path(role_path)
    if not role_text.exists():
        print(f"Error: Prompt file '{role_text}' not found.")
        return
    print(role_text)
    return role_text.read_text(encoding="utf-8")

SENIOR_DEV = read_role("prompts/senior-dev-role.md")

role = SENIOR_DEV

intent = f"""write a simple python hello-world"""

final_prompt = f"""
{rolebase_instructions}

{intent}
"""
response = client.models.generate_content(
    model=MODEL_ID,
    contents=final_prompt
)

print(response.text)
