"""
repl.py

Handles the Interactive Read-Eval-Print Loop (REPL) for Vybz.
Leverages prompt_toolkit for multi-line editing and custom keybindings.
Connects to Google GenAI SDK for stateful chat.
Supports multi-agent session switching, artifact auto-saving, and context hot-reloading.
"""

import sys
import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List

from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.enums import EditingMode

from google import genai
from google.genai import types

from vybz.agent import Agent
from vybz.context_engine import CodeBase
from vybz.squad import Squad
from vybz.artifact import ArtifactProcessor
from vybz.services.session import SessionManager
from vybz.commands.registry import CommandRegistry
from vybz import ui

class ReplSession:
    """
    Manages the state and input loop for an interactive session.
    Supports switching between multiple agent personas.
    """

    def __init__(
        self,
        session_manager: SessionManager,
        log_file: Optional[Path] = None,
        mode: str = "emacs"
    ):
        self.log_file = log_file or Path("/tmp/vybz.log")
        #TODO import SessionManager rather than all the arguments
        self.session_manager = session_manager

        # State Tracking for Auto-Save
        self.last_response: Optional[str] = None

        self.kb = KeyBindings()
        self._setup_keybindings()

        # Command Registry
        self.registry = CommandRegistry()
        self.registry.initialize()

        # Editing Mode
        editing_mode = ReplSession._parse_editing_mode(mode)

        # Initialize PromptSession with our bindings
        self.session = PromptSession(key_bindings=self.kb, editing_mode=editing_mode)

    def _parse_editing_mode(mode_str: str):
        try:
            # Direct lookup against the Enum type
            mode = EditingMode[mode_str.upper()]
            return mode

        except KeyError:
            # Dynamically generate list of valid options from the Enum
            valid_options = ", ".join([m.name.lower() for m in EditingMode])
            ui.print_error(f"Invalid mode '{mode_str}'. Options: {valid_options}")


    def _setup_keybindings(self) -> None:
        """
        Define custom keybindings:
        - Meta+Enter (Alt+Enter): Submit input.
        - Enter: Insert newline (default behavior for easy code pasting).
        """
        @self.kb.add('escape', 'enter')
        def _(event):
            """Submit when Meta+Enter or Esc+Enter is pressed."""
            event.current_buffer.validate_and_handle()

    def _get_prompt_tokens(self) -> List[Tuple[str, str]]:
        """Generates the left-side prompt tokens."""
        agent = self.session_manager.active_agent
        label = agent.id if agent else "vybz"
        return [
            ("class:agent", f"{label} "),
            ("class:separator", "❯ "),
        ]

    def _get_rprompt_tokens(self) -> List[Tuple[str, str]]:
        """Generates the right-side status prompt tokens."""
        mode_str = "VI" if self.session.editing_mode == EditingMode.VI else "EMACS"
        ctx_str = "CTX" if self.session_manager.codebase else "NO-CTX"
        return [
            ("class:meta", f"{mode_str} | {ctx_str}"),
        ]

    def _load_asset(self, filename: str) -> str:
        """
        Robustly loads text content from the assets directory.
        """
        try:
            asset_path = Path(__file__).parent / "assets" / filename
            if not asset_path.exists():
                return f"Asset not found: {filename}"
            return asset_path.read_text(encoding="utf-8")
        except Exception as e:
            return f"Failed to load asset: {e}"

    def start(self) -> None:
        """
        Starts the interactive loop.
        """
        ui.print_system("Tip: Press 'Alt+Enter' (or Esc+Enter) to submit. Type '/help' for commands.")

        # Log Session Start
        self._log_to_file(f"\n{'='*40}\nSESSION START: {datetime.datetime.now()}\n{'='*40}\n")

        while True:
            try:
                # 1. READ
                user_input = self.session.prompt(
                    self._get_prompt_tokens,
                    rprompt=self._get_rprompt_tokens,
                    style=ui.get_ptk_style(), # <--- DELEGATED TO UI
                    multiline=True
                )

                if not user_input.strip():
                    continue

                # 2. CHECK COMMANDS
                if self._handle_command(user_input):
                    continue

                # 3. EVAL & PRINT
                self._handle_input(user_input)

            except KeyboardInterrupt:
                continue
            except EOFError:
                ui.print_system("Exiting session.")
                break
            except Exception as e:
                ui.print_error(f"REPL Error: {e}")

    def _handle_command(self, text: str) -> bool:
        """
        Intercepts slash commands using the CommandRegistry.
        Returns True if a command was handled (skipping LLM inference).
        """
        parts = text.strip().split()
        if not parts:
            return False

        cmd_name = parts[0].lower()
        args = parts[1:]

        # Check if it looks like a command
        if not cmd_name.startswith("/"):
            return False

        # Lookup
        command = self.registry.get_command(cmd_name)
        if command:
            return command.execute(self, args)

        # Unknown command but starts with /
        ui.print_error(f"Unknown command '{cmd_name}'. Type /help for list.")
        return True

    def _handle_input(self, text: str) -> None:
        """
        Sends input to the model, streams the response, and logs the turn.
        """
        agent = self.session_manager.active_agent
        chat = self.session_manager.active_chat

        # Log User Input
        self._log_to_file(f"\n[USER ({agent.name})]: {text}\n")

        # Visual separator
        ui.console.print()

        full_response = []

        try:
            # SDK Call: Stream Message using ACTIVE chat
            if not chat:
                ui.print_error("No active chat session.")
                return

            response_stream = chat.send_message_stream(text)

            for chunk in response_stream:
                if chunk.text:
                    ui.stream_chunk(chunk.text)
                    full_response.append(chunk.text)

            # Print newline after stream ends
            ui.console.print()

            # Capture full response for state tracking (Auto-Save)
            self.last_response = "".join(full_response)

            # Log Model Response
            self._log_to_file(f"\n[MODEL ({agent.name})]: {self.last_response}\n")
            self._log_to_file("-" * 40)

        except Exception as e:
            ui.print_error(f"Generation Error: {e}")
            self._log_to_file(f"\n[ERROR]: {e}\n")

    def _log_to_file(self, text: str) -> None:
        """Appends text to the interaction log file."""
        if not self.log_file.parent.exists():
            self.log_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(text)
        except IOError as e:
            ui.print_error(f"Logging failed: {e}")

