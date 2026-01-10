#!/usr/bin/env python3
"""
Auto-Commit Generator utilizing Google Gemini 3.0.

Analyzes staged git changes and optional context logs to generate
professional, Conventional Commit messages.

Usage:
    export GEMINI_API_KEY="your_key"
    python autocommit_gen.py [--log-file path/to/log.txt]
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

from google import genai
from google.genai import types

# -----------------------------------------------------------------------------
# Configuration & Constants
# -----------------------------------------------------------------------------

TARGET_MODEL = "gemini-3-flash-preview"

# Text content formatted to stay within 79-character width.
SYSTEM_INSTRUCTION = (
    "You are a Senior Release Engineer and Technical Writer.\n"
    "Your task is to generate a git commit message based on:\n"
    "1. The `git diff --cached` output (The Truth).\n"
    "2. An optional vibe-coding log file (The Context/Why).\n\n"
    "**Rules:**\n"
    "1. Use the **Conventional Commits** specification.\n"
    "   Format: <type>(<scope>): <subject> followed by a blank line and\n"
    "   a <body>.\n"
    "   Types: feat, fix, docs, style, refactor, perf, test, build, ci,\n"
    "   chore, revert.\n"
    "2. The <subject> must be imperative, lower-case, no period at end.\n"
    "3. The <body> should explain *what* and *why*, not just *how*.\n"
    "4. Context: If logs are provided, prioritize the user's intent to\n"
    "   explain the 'Why'.\n"
    "5. Human Changes: Acknowledge that humans may have modified the code.\n"
    "6. Output: Return ONLY the commit message. No markdown or preamble."
)


# -----------------------------------------------------------------------------
# Exceptions
# -----------------------------------------------------------------------------

class GitOperationError(Exception):
    """Raised when a git command fails or environment is invalid."""
    pass


class GenAIConfigurationError(Exception):
    """Raised when API keys or client configuration is invalid."""
    pass


# -----------------------------------------------------------------------------
# Services
# -----------------------------------------------------------------------------

class GitService:
    """Handles interactions with the local git binary via subprocess."""

    @staticmethod
    def assert_git_repo() -> None:
        """
        Verifies the current directory is within a git repository.

        Raises:
            GitOperationError: If not in a git repo.
        """
        try:
            subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except subprocess.CalledProcessError:
            raise GitOperationError("Directory is not a git repository.")
        except FileNotFoundError:
            raise GitOperationError("Git binary not found. Install git.")

    @staticmethod
    def get_staged_diff() -> str:
        """
        Retrieves the diff of currently staged files.

        Returns:
            str: The raw diff output.

        Raises:
            GitOperationError: If fetching the diff fails or none staged.
        """
        try:
            result = subprocess.run(
                ["git", "diff", "--cached"],
                capture_output=True,
                text=True,
                check=True
            )
            diff = result.stdout.strip()

            if not diff:
                raise GitOperationError(
                    "No staged changes. Run 'git add <file>' first."
                )
            return diff
        except subprocess.CalledProcessError as e:
            raise GitOperationError(f"Failed to get git diff: {e.stderr}")


class GeminiCommitAgent:
    """Wrapper for the Google Gen AI SDK (v1.57+)."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        """
        Initialize the GenAI client.

        Args:
            api_key: The Google API Key.
        """
        _key = api_key or os.getenv("GEMINI_API_KEY")
        if not _key:
            raise GenAIConfigurationError(
                "GEMINI_API_KEY not found in environment."
            )

        self.client = genai.Client(api_key=_key)

    def generate_message(self, diff: str, context: Optional[str]) -> str:
        """
        Generates a commit message using the LLM.

        Args:
            diff: The raw git diff.
            context: Optional string content of agent logs.

        Returns:
            str: The generated commit message.
        """
        parts = [f"### GIT DIFF (Staged Changes)\n{diff}"]

        if context:
            parts.append(f"\n### AGENT LOGS (Context)\n{context}")
            parts.append(
                "\nNote: The logs describe intent. The Diff shows result. "
                "Synthesize the message based on Diff, using logs for "
                "motivation."
            )

        prompt = "\n".join(parts)

        try:
            config = types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.2,
            )
            response = self.client.models.generate_content(
                model=TARGET_MODEL,
                contents=prompt,
                config=config
            )

            if not response.text:
                return "Error: Empty response from model."

            return response.text.strip()

        except Exception as e:
            return f"Error generating commit message: {str(e)}"


# -----------------------------------------------------------------------------
# Main Execution
# -----------------------------------------------------------------------------

def main() -> None:
    """Main entry point for the script."""
    desc = "Generate Conventional Commit messages from staged changes."
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument(
        "--log-file",
        type=Path,
        help="Path to an agent interaction log file for context."
    )

    args = parser.parse_args()

    try:
        GitService.assert_git_repo()
        diff_text = GitService.get_staged_diff()

        context_content: Optional[str] = None
        if args.log_file:
            if not args.log_file.exists():
                msg = f"Warning: Log '{args.log_file}' not found. Ignoring."
                print(msg, file=sys.stderr)
            else:
                try:
                    context_content = args.log_file.read_text(encoding='utf-8')
                except Exception as e:
                    msg = f"Warning: Could not read log: {e}. Ignoring."
                    print(msg, file=sys.stderr)

        load_dotenv()
        agent = GeminiCommitAgent()

        print("Analyzing changes...", file=sys.stderr)
        commit_message = agent.generate_message(diff_text, context_content)

        print(commit_message)

    except (GitOperationError, GenAIConfigurationError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
