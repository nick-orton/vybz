"""
repl.py

Handles the Interactive Read-Eval-Print Loop (REPL) for Vybz.
Leverages prompt_toolkit for multi-line editing and custom keybindings.
"""

import sys
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import HTML
from vybz.agent import Agent
from vybz import ui
from rich.markup import escape

class ReplSession:
    """
    Manages the state and input loop for an interactive session.
    """

    def __init__(self, agent: Agent, model_id: str):
        self.agent = agent
        self.model_id = model_id
        self.kb = KeyBindings()
        self._setup_keybindings()

        # Initialize PromptSession with our bindings
        self.session = PromptSession(key_bindings=self.kb)

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

    def start(self) -> None:
        """
        Starts the interactive loop.
        """
        ui.print_system(f"Entering Interactive Mode with {self.agent.name}...")
        ui.print_system("Tip: Press 'Alt+Enter' (or Esc+Enter) to submit. Type '/exit' to quit.")

        # Visual Prompt Styling
        # We use HTML formatting supported by prompt_toolkit
        prompt_text = HTML(f"<b><style fg='cyan'>[{self.agent.name}]</style></b> >> ")

        while True:
            try:
                # 1. READ
                user_input = self.session.prompt(prompt_text, multiline=True)

                # Check for exit commands
                if user_input.strip().lower() in ["/exit", "quit", "exit"]:
                    raise EOFError

                if not user_input.strip():
                    continue

                # 2. EVAL (Phase 1 Stub: Echo only)
                # In Phase 2, this is where we call client.chats.send_message
                self._handle_input_stub(user_input)

            except KeyboardInterrupt:
                # User pressed Ctrl+C - interrupt current action or exit?
                # For now, let's just clear buffer or exit loop
                continue
            except EOFError:
                ui.print_system("Exiting session.")
                break
            except Exception as e:
                ui.print_error(f"REPL Error: {e}")

    def _handle_input_stub(self, text: str) -> None:
        """
        Temporary handler to verify input capture in Phase 1.
        """
        ui.console.print(f"[dim]DEBUG: Captured {len(text)} chars[/dim]")
        ui.console.print(f"[green]{escape(text)}[/green]")
        ui.console.print("-" * 40)


