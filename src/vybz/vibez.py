import os
import sys
import datetime
from vybz.agent import Agent
from vybz.context_engine import CodeBase
import vybz.ui as ui
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
from typing import List, Optional

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

def generate_and_continuous_log(
    client: genai.Client,
    model_id: str,
    agent: Agent,
    intent: str,
    codebase: Optional[CodeBase] = None,
    log_file_path: str = "interaction_log.txt"
) -> str:
    """
    Generates content via Google Gen AI SDK (v1.57), streams response to stdout,
    and continuously appends output to a specific log file with timestamps.

    Args:
        client: Configured google.genai.Client instance.
        model_id: Target model (e.g., 'gemini-2.0-flash-exp').
        agent: The Agent instance defining the persona.
        intent: User input prompt/intent.
        codebase: Optional CodeBase snapshot to inject into the LLM context.
        log_file_path: Path to the log file. Created if non-existent.

    Returns:
        The complete generated text response.

    Raises:
        IOError: If file operations fail.
        Exception: If the API call fails.
    """
    log_path = Path(log_file_path)
    timestamp_iso = datetime.datetime.now().isoformat()
    timestamp_display = datetime.datetime.now().strftime("%H:%M:%S")
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")

    # Construct the full system prompt internally
    sys_instructions = agent.construct_agent_role_profile()

    # Inject Date Knowledge
    sys_instructions += f"\n\n### SYSTEM METADATA\nCurrent Date: {current_date}\n"

    # Inject codebase if provided. Do NOT include in log header.
    if codebase:
        sys_instructions += "\n\n" + codebase.render()

    # Render UI Header (Visual Only)
    ui.render_header(
        agent_name=agent.get_identity(),
        model_id=model_id,
        intent=intent,
        timestamp=timestamp_display
    )
    ui.print_system("Stream initialized...")


    # Header emphasizes Agent Identity and Intent, not the boilerplate system prompt
    raw_header = (
        f"\n\n{'='*60}\n"
        f"TIMESTAMP: {timestamp_iso}\n"
        f"MODEL:     {model_id}\n"
        f"AGENT:     {agent.get_identity()}\n"
        f"INTENT:    {intent}\n"
        f"{'='*60}\n"
        f"RESPONSE:\n"
    )

    full_response = []

    try:
        # Ensure parent directory exists
        if not log_path.parent.exists():
            log_path.parent.mkdir(parents=True, exist_ok=True)

        # Open file in append mode. We keep it open during the stream to ensure
        # "continuous" appending as chunks arrive.
        with open(log_path, "a", encoding="utf-8") as f:
            # Write metadata header to log
            f.write(raw_header)

            # Execute generation with streaming
            response_stream = client.models.generate_content_stream(
                model=model_id,
                contents=intent,
                config=types.GenerateContentConfig(
                   response_mime_type="text/plain",
                   system_instruction=sys_instructions
                )
            )


            for chunk in response_stream:
                if chunk.text:
                    # Echo to Standard Out via UI (Styled)
                    ui.stream_chunk(chunk.text)

                    # Append to Log File immediately
                    f.write(chunk.text)

                    # Accumulate for return
                    full_response.append(chunk.text)

            # Trailing newline for log file readability
            f.write("\n")
            print() # Trailing newline for stdout

    except Exception as e:
        error_msg = f"Failed during generation/logging: {str(e)}"
        ui.print_error(error_msg)

        # Attempt to log the error if file system is accessible
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(error_msg)
        except IOError:
            pass
        raise e

    return "".join(full_response)
