#!/usr/bin/env python3
"""
work.py

The primary CLI entry point for Vybz Kartel.
"""

import argparse
import asyncio
import os
import shutil
import sys
from pathlib import Path
from typing import Optional

import vybz
import vybz.vibez as vibez
import vybz.ui as ui
import vybz.repl as repl
import vybz.config as config
from vybz.shared.codebase import CodeBase
from vybz.shared.squad import Squad
from vybz.services.session import SessionManager


def _init_user_library() -> None:
    """Copies system default library to user config directory."""
    package_root = Path(vybz.__file__).parent
    system_lib = package_root / "library"

    xdg_root = os.getenv("XDG_CONFIG_HOME")
    if xdg_root:
        user_lib = Path(xdg_root) / "vybz" / "library"
    else:
        user_lib = Path.home() / ".config" / "vybz" / "library"

    if not system_lib.exists():
        ui.print_error(f"System library not found at {system_lib}")
        return

    ui.print_system(f"Initializing user library at {user_lib}...")

    count = 0
    for src_file in system_lib.rglob("*"):
        if not src_file.is_file():
            continue

        # Filter out Python package artifacts and hidden system files
        if src_file.name == "__init__.py" or src_file.suffix == ".pyc":
            continue
        if "__pycache__" in src_file.parts or src_file.name.startswith("."):
            continue

        rel_path = src_file.relative_to(system_lib)
        dest_file = user_lib / rel_path

        if not dest_file.exists():
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dest_file)
            ui.print_system(f"  Created: {rel_path}")
            count += 1

    if count > 0:
        ui.print_success(f"Initialized {count} files.")
    else:
        ui.print_system("No new files to initialize.")


async def main() -> None:
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
        nargs='?',
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
        default="gemini-3-flash-preview",
        help="Target Gemini Model ID.\nDefault: gemini-3-flash-preview"
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
    parser.add_argument(
        "--library",
        help="Path to custom library root containing agents/ and skills/ directories."
    )
    parser.add_argument(
        "--init-library",
        action="store_true",
        help="Copy system default agents and skills to user config directory."
    )

    # Load User Config
    user_defaults = config.ConfigLoader.load()
    if user_defaults:
        parser.set_defaults(**user_defaults)

    args = parser.parse_args()

    try:
        # 0. Configure UI Theme
        ui.set_theme(args.theme)

        if args.init_library:
            _init_user_library()
            sys.exit(0)

        if not args.agent:
            parser.print_help()
            sys.exit(1)

        # Initialize Squad with library path
        lib_path = Path(args.library) if args.library else None
        Squad.initialize(custom_library_root=lib_path)

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
            await session.start()

    except KeyboardInterrupt:
        ui.print_warning("Session interrupted by user.")
        sys.exit(130)
    except Exception as e:
        ui.print_error(f"Critical Runtime Error: {e}")
        # Print stack trace for debugging if needed, or rely on ui error
        import traceback
        traceback.print_exc()
        sys.exit(1)

def run_main():
    """Synchronous wrapper to run the async main."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(130)

if __name__ == "__main__":
    run_main()
