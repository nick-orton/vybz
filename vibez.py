import os
from dotenv import load_dotenv
from google import genai

def configure_genai_client() -> None:
    """
    Load environment variables and configure the genai client.

    Raises:
        ValueError: If the GEMINI_API_KEY environment variable is not set.
    """
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY not found. Please set it in your .env file or "
            "environment."
        )
    return genai.Client(api_key=api_key)
