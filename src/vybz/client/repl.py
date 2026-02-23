"""
repl.py

Handles the Interactive Read-Eval-Print Loop (REPL) for Vybz.
Leverages prompt_toolkit for multi-line editing and custom keybindings.
Communicates with the vybzd engine via ClientSessionManager.
"""

from pathlib import Path
from typing import Optional, Tuple, List

from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.enums import EditingMode

from vybz.client.session import ClientSessionManager
from vybz.commands.registry import CommandRegistry
from vybz.services.logger import InteractionLogger
from vybz.shared.config import parse_editing_mode
from vybz.client import ui

class ReplSession:
    """
    Manages the state and input loop for an interactive session.
    Delegates LLM logic to the remote ClientSessionManager.
    """

    def __init__(
        self,
        session_manager: ClientSessionManager,
        log_file: Optional[Path] = None,
        mode: str = "emacs"
    ):
        log_path = log_file or Path("/tmp/vybz.log")
        self.logger = InteractionLogger(log_path)
        self.session_manager = session_manager

        # State Tracking for Auto-Save
        self.last_response: Optional[str] = None

        self.kb = KeyBindings()
        self._setup_keybindings()

        # Command Registry
        self.registry = CommandRegistry()
        self.registry.initialize()

        # Editing Mode
        editing_mode = parse_editing_mode(mode)

        # Initialize PromptSession with our bindings
        self.session = PromptSession(key_bindings=self.kb, editing_mode=editing_mode)


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

    async def start(self) -> None:
        """
        Starts the interactive loop.
        """
        ui.print_system("Tip: Press 'Alt+Enter' (or Esc+Enter) to submit. Type '/help' for commands.")

        # Log Session Start
        self.logger.log_session_start()

        while True:
            try:
                # 1. READ
                user_input = await self.session.prompt_async(
                    self._get_prompt_tokens,
                    rprompt=self._get_rprompt_tokens,
                    style=ui.get_ptk_style(),
                    multiline=True
                )

                if not user_input.strip():
                    continue

                # 2. CHECK COMMANDS
                if await self._handle_command(user_input):
                    continue

                # 3. EVAL & PRINT
                await self._handle_input(user_input)

            except KeyboardInterrupt:
                continue
            except EOFError:
                ui.print_system("Exiting session.")
                break
            except Exception as e:
                ui.print_error(f"REPL Error: {e}")

    async def _handle_command(self, text: str) -> bool:
        """
        Intercepts slash commands using the CommandRegistry.
        Returns True if a command was handled (skipping LLM inference).
        """
        parts = text.strip().split()
        if not parts:
            return False

        cmd_name = parts[0].lower()
        args = parts[1:]

        if not cmd_name.startswith("/"):
            return False

        command = self.registry.get_command(cmd_name)
        if command:
            return await command.execute(self, args)

        ui.print_error(f"Unknown command '{cmd_name}'. Type /help for list.")
        return True

    async def _handle_input(self, text: str) -> None:
        """
        Sends input to the vybzd engine, streams the response, and logs the turn.
        """
        agent = self.session_manager.active_agent
        agent_name = agent.name if agent else "vybz"

        # 1. Log User Input
        self.logger.log_user_input(agent_name, text)

        # Visual separator
        ui.console.print()

        full_response = []

        try:
            # 2. Consume Remote Stream
            async for chunk in self.session_manager.chat(text):
                if chunk:
                    ui.stream_chunk(chunk)
                    full_response.append(chunk)

            # 3. Finalize Turn
            ui.console.print()
            self.last_response = "".join(full_response)
            self.logger.log_model_response(agent_name, self.last_response)

        except Exception as e:
            ui.print_error(f"Generation Error: {e}")
            self.logger.log_error(str(e))
