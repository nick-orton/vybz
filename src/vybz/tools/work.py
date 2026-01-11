#!/usr/bin/env python3
"""
work.py

The primary CLI entry point for Vybz Kartel.
Orchestrates the interaction between the User (Intent), the CodeBase (Context),
and the AI Squad (Agents).

Usage:
    vybz <agent> <intent> [-m model] [-c codebase_path] [-l log_path]

Example:
    vybz junior-dev "Refactor main.py" -c .
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

# Vybz Kartel Core Imports
import vybz.vibez as vibez
from vybz.context_engine import CodeBase
from vybz.squad import Squad


def main() -> None:
    """
    Parses command line arguments and orchestrates the Vibe Coding session.
    """
    parser = argparse.ArgumentParser(
        description="Vybz Kartel: AI-Orchestrated Vibe Coding CLI",
        formatter_class=argparse.RawTextHelpFormatter
    )

    # Positional Arguments
    parser.add_argument(
        "agent",
        help="Target Agent Persona \n['junior-dev', 'pm', 'senior-dev', 'advisor', 'tech-writer' ]"
    )
    parser.add_argument(
        "intent",
        help="The task description or intent for the agent."
    )

    # Optional Arguments
    parser.add_argument(
        "-m", "--model",
        default="gemini-3-pro-preview",
        help="Target Gemini Model ID.\nDefault: gemini-3-pro-preview"
    )
    parser.add_argument(
        "-l", "--log-file",
        default="/tmp/vybz.log",
        help="Path to the interaction log file.\nDefault: /tmp/vybz.log"
    )
    parser.add_argument(
        "-c", "--codebase",
        default=None,
        help=(
            "Root path to snapshot for context.\n"
            "If omitted, runs in 'Greenfield' mode (no code context)."
        )
    )

    args = parser.parse_args()

    try:
        # 1. Initialize the Google GenAI Client
        # We do this first to fail fast if API keys are missing.
        client = vibez.configure_genai_client()

        # 2. Load the Agent
        # Validate agent existence before expensive operations.
        try:
            agent = Squad.get_agent(args.agent)
        except ValueError:
            print(f"[!] Error: Agent '{args.agent}' not found.", file=sys.stderr)
            print(f"[-] Available Agents: {', '.join(Squad.list_agents())}", file=sys.stderr)
            sys.exit(1)

        # 3. Snapshot Codebase (Optional)
        codebase: Optional[CodeBase] = None
        if args.codebase:
            cb_path = Path(args.codebase)
            print(f"[-] Snapshotting codebase at: {cb_path.resolve()} ...")
            try:
                codebase = CodeBase(cb_path)
            except (FileNotFoundError, NotADirectoryError) as e:
                print(f"[!] CodeBase Error: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            print("[-] No codebase provided. Running in GREENFIELD mode.")

        # 4. Execution
        print("-" * 60)
        print(f"AGENT: {agent.get_identity()}")
        print(f"MODEL: {args.model}")
        print("-" * 60)

        # 5. Generate and Stream
        vibez.generate_and_continuous_log(
            client=client,
            model_id=args.model,
            agent=agent,
            intent=args.intent,
            codebase=codebase,
            log_file_path=args.log_file
        )

    except KeyboardInterrupt:
        print("\n[!] Session interrupted by user.", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"\n[!] Critical Runtime Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
