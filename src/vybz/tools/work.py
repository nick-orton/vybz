#!/usr/bin/env python3
"""
work.py

The primary CLI entry point for Vybz Kartel.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

import vybz.vibez as vibez
import vybz.ui as ui
import vybz.repl as repl
import vybz.config as config
from vybz.context_engine import CodeBase
from vybz.squad import Squad
from vybz.services.session import SessionManager


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
        nargs='?',
        default=None,
        help="The task description. If omitted, enters Interactive Mode."
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
    parser.add_argument(
        "--mode",
        choices=["vi", "emacs"],
        default="emacs",
        help="Input editing mode (default: emacs)"
    )
    parser.add_argument(
        "--theme",
        default="default",
        help="UI Color Theme (default: default)"
    )

    # Load User Config
    user_defaults = config.ConfigLoader.load()
    if user_defaults:
        parser.set_defaults(**user_defaults)

    args = parser.parse_args()

    try:
        # 0. Configure UI Theme
        ui.set_theme(args.theme)

        # 1. Initialize the Google GenAI Client
        client = vibez.configure_genai_client()

        # 2. Load the Agent
        try:
            agent = Squad.get_agent(args.agent)
        except ValueError:
            ui.print_error(f"Agent '{args.agent}' not found.")
            ui.print_system(f"Available Agents: {', '.join(Squad.list_agents())}")
            sys.exit(1)

        # 3. Snapshot Codebase (Optional)
        codebase: Optional[CodeBase] = None
        if args.codebase:
            cb_path = Path(args.codebase)
            ui.print_system(f"Snapshotting codebase at: {cb_path.resolve()} ...")
            try:
                codebase = CodeBase(cb_path)
            except (FileNotFoundError, NotADirectoryError) as e:
                ui.print_error(f"CodeBase Error: {e}")
                sys.exit(1)
        else:
            ui.print_system("No codebase provided. Running in GREENFIELD mode.")

        # 4. Execution Branching
        if args.intent:
            # ---> ONE-SHOT MODE (Legacy)
            vibez.generate_and_continuous_log(
                client=client,
                model_id=args.model,
                agent=agent,
                intent=args.intent,
                codebase=codebase,
                log_file_path=args.log_file
            )
        else:
            # ---> INTERACTIVE MODE (Phase 2)
            session_manager = SessionManager(client=client, model_id=args.model, initial_agent=agent, codebase=codebase)
            session = repl.ReplSession(
                session_manager,
                log_file=Path(args.log_file),
                mode=args.mode
            )
            session.start()

    except KeyboardInterrupt:
        ui.print_warning("Session interrupted by user.")
        sys.exit(130)
    except Exception as e:
        ui.print_error(f"Critical Runtime Error: {e}")
        # Print stack trace for debugging if needed, or rely on ui error
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

