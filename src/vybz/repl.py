"""
repl.py

Handles the Interactive Read-Eval-Print Loop (REPL) for Vybz.
Leverages prompt_toolkit for multi-line editing and custom keybindings.
Connects to Google GenAI SDK for stateful chat.
"""

import sys
import datetime
from pathlib import Path
from typing import Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import HTML
from rich.markup import escape

from google import genai
from google.genai import types

from vybz.agent import Agent
from vybz.context_engine import CodeBase
from vybz import ui

class ReplSession:
    """
    Manages the state and input loop for an interactive session.
    """

    def __init__(
        self,
        client: genai.Client,
        agent: Agent,
        model_id: str,
        codebase: Optional[CodeBase] = None,
        log_file: Optional[Path] = None
    ):
        self.client = client
        self.agent = agent
        self.model_id = model_id
        self.codebase = codebase
        self.log_file = log_file or Path("/tmp/vybz.log")

        self.kb = KeyBindings()
        self._setup_keybindings()

        # Initialize PromptSession with our bindings
        self.session = PromptSession(key_bindings=self.kb)

        # Initialize the Chat Session
        self.chat = self._init_chat()

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

    def _init_chat(self) -> any:
        """
        Constructs system instructions and initializes the GenAI Chat object.
        """
        ui.print_system("Initializing Chat Session context...")

        # 1. Base Agent Role
        sys_instructions = self.agent.construct_agent_role_profile()

        # 2. Date Knowledge
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        sys_instructions += f"\n\n### SYSTEM METADATA\nCurrent Date: {current_date}\n"

        # 3. CodeBase Injection
        if self.codebase:
            ui.print_system(f"Injecting CodeBase context from: {self.codebase.root_path}")
            sys_instructions += "\n\n" + self.codebase.render()

        # 4. Create Chat
        try:
            return self.client.chats.create(
                model=self.model_id,
                config=types.GenerateContentConfig(
                    system_instruction=sys_instructions,
                    temperature=0.7
                )
            )
        except Exception as e:
            ui.print_error(f"Failed to initialize Chat: {e}")
            sys.exit(1)

    def start(self) -> None:
        """
        Starts the interactive loop.
        """
        ui.render_header(
            agent_name=self.agent.get_identity(),
            model_id=self.model_id,
            intent="Interactive Session"
        )
        ui.print_system("Tip: Press 'Alt+Enter' (or Esc+Enter) to submit. Type '/exit' to quit.")

        # Log Session Start
        self._log_to_file(f"\n{'='*40}\nSESSION START: {datetime.datetime.now()}\n{'='*40}\n")

        # Visual Prompt Styling
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

                # 2. EVAL & PRINT
                self._handle_input(user_input)

            except KeyboardInterrupt:
                continue
            except EOFError:
                ui.print_system("Exiting session.")
                break
            except Exception as e:
                ui.print_error(f"REPL Error: {e}")

    def _handle_input(self, text: str) -> None:
        """
        Sends input to the model, streams the response, and logs the turn.
        """
        # Log User Input
        self._log_to_file(f"\n[USER]: {text}\n")

        # Visual separator
        ui.console.print()

        full_response = []

        try:
            # SDK Call: Stream Message
            response_stream = self.chat.send_message_stream(text)

            for chunk in response_stream:
                if chunk.text:
                    ui.stream_chunk(chunk.text)
                    full_response.append(chunk.text)

            # Print newline after stream ends
            ui.console.print()

            # Log Model Response
            combined_response = "".join(full_response)
            self._log_to_file(f"\n[MODEL]: {combined_response}\n")
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


