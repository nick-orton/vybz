import os
from google import genai

# Retrieve the API key from the environment
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found. Did you run 'source env.sh'?")

# Initialize the client. If you leave api_key blank, the SDK
# actually checks the GEMINI_API_KEY env var automatically.
client = genai.Client(api_key=api_key)

response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents="Explain the concept of 'vibe coding' in three sentences."
)

print(response.text)
