import os
from dotenv import load_dotenv
from google import genai
from typing import List

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

def get_models(client: genai.Client) -> List[str]:
    """
    Retrieves a list of model names that support the 'generateContent' method.

    Args:
        client (genai.Client): An initialized instance of the Google GenAI client.

    Returns:
        List[str]: A list of strings containing the model identifiers (e.g., 'models/gemini-1.5-pro').

    Raises:
        RuntimeError: If the API call fails or the client is misconfigured.
    """
    try:
        model_list: List[str] = []
        # Iterate through models returned by the SDK
        for model in client.models.list():
            # Filter for models that explicitly support content generation
            if "generateContent" in model.supported_actions:
                model_list.append(model.name)
        return model_list
    except Exception as e:
        raise RuntimeError(f"Failed to fetch models from Gemini API: {str(e)}") from e
