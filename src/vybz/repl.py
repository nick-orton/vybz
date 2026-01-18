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
from vybz import ui

EDITING_MODE_MAP = {
    "vi": EditingMode.VI,
    "emacs": EditingMode.EMACS
}

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

        # Initialize PromptSession with our bindings
        self.editing_mode = EDITING_MODE_MAP.get(mode.lower(), EditingMode.EMACS)
        self.session = PromptSession(key_bindings=self.kb, editing_mode=self.editing_mode)

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

    def _refresh_context(self) -> None:
        """
        Reloads the CodeBase snapshot and hot-swaps all active chat sessions
        to inject the new context and current date.
        """
        ui.print_system("Refreshing CodeBase snapshot and Session Context...")
        count = self.session_manager.refresh_context()
        ui.print_success(f"Context refreshed for {count} active sessions.")
        ui.print_system(f"System Date updated to: {datetime.datetime.now().strftime('%Y-%m-%d')}")

    def _switch_to_agent_by_name(self, name: str) -> bool:
        """
        Resolves agent name via Squad and switches.
        Returns True if successful.
        """
        try:
            agent = self.session_manager.switch_agent(name)

            # Log the switch
            self._log_to_file(f"\n{'='*40}\nSWITCHED AGENT: {agent.get_identity()}\n{'='*40}\n")

            # Update UI
            codebase = self.session_manager.codebase
            cb_root = str(codebase.root_path) if codebase else None
            ui.render_session_header(
                agent_name=agent.get_identity(),
                model_id=self.session_manager.model_id,
                codebase_root=cb_root
            )
            return True
        except ValueError:
            ui.print_error(f"Agent '{name}' not found.")
            ui.print_system(f"Available: {', '.join(Squad.list_agents())}")
            return False
        except Exception as e:
            ui.print_error(f"Error switching agent: {e}")
            return False

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
        Intercepts slash commands.
        Returns True if a command was handled (skipping LLM inference).
        """
        parts = text.strip().split()
        if not parts:
            return False

        cmd = parts[0].lower()
        args = parts[1:]

        # Exit Commands
        if cmd in ["/exit", "/quit", "exit", "quit"]:
            raise EOFError

        # Clear Screen
        if cmd == "/clear":
            ui.console.clear()
            codebase = self.session_manager.codebase
            cb_root = str(codebase.root_path) if codebase else None
            ui.render_session_header(
                agent_name=self.session_manager.active_agent.get_identity(),
                model_id=self.session_manager.model_id,
                codebase_root=cb_root
            )
            return True

        # Update / Hot-Reload Context
        if cmd == "/update":
            self._refresh_context()
            return True

        # Help
        if cmd == "/help":
            content = self._load_asset("repl_help.txt")
            ui.print_panel(content, title="Help Menu")
            return True

        # Agent Switching
        if cmd == "/agent":
            if not args:
                # List agents
                agents = Squad.list_agents()
                template = self._load_asset("agent_tool_tip.txt")
                ui.print_from_template(
                    template,
                    agent_name=self.session_manager.active_agent.name,
                    agent_list=', '.join(agents)
                )
            else:
                target_name = args[0]
                self._switch_to_agent_by_name(target_name)
            return True

        # Auto-Save Artifact
        if cmd == "/save":
            self._cmd_save()
            return True

        # Set Editing Mode
        if cmd == "/set":
            if not args:
                ui.print_error("Usage: /set <mode> (vi | emacs)")
                return True

            target_mode = args[0].lower()
            if target_mode not in EDITING_MODE_MAP:
                valid_modes = ", ".join(EDITING_MODE_MAP.keys())
                ui.print_error(f"Invalid mode '{target_mode}'. Options: {valid_modes}")
                return True

            # Apply the change
            new_mode_enum = EDITING_MODE_MAP[target_mode]
            self.session.editing_mode = new_mode_enum
            ui.print_success(f"Input mode set to {target_mode.upper()}")
            return True

        # Set UI Theme
        if cmd == "/theme":
            if not args:
                ui.print_error("Usage: /theme <name>")
                return True

            if ui.set_theme(args[0]):
                ui.print_success(f"Theme set to '{args[0]}'")
            return True

        return False

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

    def _cmd_save(self) -> None:
        """
        Executes the save logic for the last response.
        """
        if not self.last_response:
            ui.print_error("Nothing to save. Generate something first.")
            return

        processor = ArtifactProcessor()

        try:
            # 1. Parse
            artifact = processor.parse(self.last_response)

            # 2. Resolve Root
            codebase = self.session_manager.codebase
            root = codebase.root_path if codebase else Path.cwd()

            # 3. Save
            msg = processor.save(artifact, root)

            # 4. Feedback
            if "Overwrote" in msg:
                ui.print_warning(msg)
            else:
                ui.print_success(msg)

            # 5. Auto-Update Context
            if codebase:
                self._refresh_context()

        except Exception as e:
            ui.print_error(f"Save failed: {e}")

    def _log_to_file(self, text: str) -> None:
        """Appends text to the interaction log file."""
        if not self.log_file.parent.exists():
            self.log_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(text)
        except IOError as e:
            ui.print_error(f"Logging failed: {e}")

