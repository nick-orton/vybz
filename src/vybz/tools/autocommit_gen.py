#!/usr/bin/env python3
"""
Auto-Commit Generator utilizing Google Gemini 3.0.

Analyzes staged git changes and optional context logs to generate
professional, Conventional Commit messages.

Usage:
    export GEMINI_API_KEY="your_key"
    # Generates message and opens git commit editor
    vybz-commit
    
    # Just prints message to stdout
    vybz-commit --dry-run
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# -----------------------------------------------------------------------------
# Path Setup (Allow imports from project root)
# -----------------------------------------------------------------------------
# Ensure we can import vybz modules even if running as a script
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from google import genai
from google.genai import types
from vybz.squad import Squad
from vybz.agent import Agent

# -----------------------------------------------------------------------------
# Configuration & Constants
# -----------------------------------------------------------------------------

TARGET_MODEL = "gemini-3-flash-preview"
TARGET_AGENT = "tech-writer"


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

    @staticmethod
    def commit(message: str) -> None:
        """
        Starts the git commit process with the given message.
        Uses -e to force the editor to open for user review.

        Args:
            message: The AI-generated commit message.
        """
        try:
            # We use subprocess.run without capture_output so it inherits
            # stdin/stdout/stderr, allowing the interactive editor (vim/nano) to work.
            subprocess.run(
                ["git", "commit", "-e", "-m", message],
                check=True
            )
        except subprocess.CalledProcessError:
            # User aborted the commit (e.g., via empty message or :cq in vim)
            print("\nCommit operation aborted by user.", file=sys.stderr)


class GeminiCommitAgent:
    """Wrapper for the Google Gen AI SDK (v1.57+)."""

    def __init__(self, agent: Agent, api_key: Optional[str] = None) -> None:
        """
        Initialize the GenAI client with a specific persona.

        Args:
            agent: The Agent instance defining the persona (Tech Writer).
            api_key: The Google API Key.
        """
        self.agent = agent
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
        # Construct the raw intent from diff and context
        parts = [f"### GIT DIFF (Staged Changes)\n{diff}"]

        if context:
            parts.append(f"\n### AGENT LOGS (Context)\n{context}")
            parts.append(
                "\nNote: The logs describe intent. The Diff shows result. "
                "Synthesize the message based on Diff, using logs for "
                "motivation."
            )

        raw_intent = "\n".join(parts)


        try:
            sys_instructions = self.agent.construct_agent_role_profile()
            config = types.GenerateContentConfig(
                temperature=0.2,
                system_instruction=sys_instructions
            )
            response = self.client.models.generate_content(
                model=TARGET_MODEL,
                contents=raw_intent,
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
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the message to stdout instead of opening git commit."
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

        # Initialize Squad and load the Tech Writer agent
        try:
            tech_writer = Squad.get_agent(TARGET_AGENT)
        except Exception as e:
            print(f"Error loading agent '{TARGET_AGENT}': {e}", file=sys.stderr)
            sys.exit(1)

        agent = GeminiCommitAgent(agent=tech_writer)

        print("Analyzing changes...", file=sys.stderr)
        commit_message = agent.generate_message(diff_text, context_content)

        if args.dry_run:
            print(commit_message)
        else:
            GitService.commit(commit_message)

    except (GitOperationError, GenAIConfigurationError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
