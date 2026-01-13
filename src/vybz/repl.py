"""
repl.py

Handles the Interactive Read-Eval-Print Loop (REPL) for Vybz.
Leverages prompt_toolkit for multi-line editing and custom keybindings.
Connects to Google GenAI SDK for stateful chat.
Supports multi-agent session switching, artifact auto-saving, and context hot-reloading.
"""

import sys
import datetime
import re
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import HTML
from markdown_it import MarkdownIt

from google import genai
from google.genai import types

from vybz.agent import Agent
from vybz.context_engine import CodeBase
from vybz.squad import Squad
from vybz import ui

class ReplSession:
    """
    Manages the state and input loop for an interactive session.
    Supports switching between multiple agent personas.
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
        self.model_id = model_id
        self.codebase = codebase
        self.log_file = log_file or Path("/tmp/vybz.log")

        # Session Management
        self.sessions: Dict[str, Any] = {} # Map agent_name -> ChatSession
        self.active_agent: Optional[Agent] = None
        self.active_chat: Any = None

        # State Tracking for Auto-Save
        self.last_response: Optional[str] = None

        self.kb = KeyBindings()
        self._setup_keybindings()

        # Initialize PromptSession with our bindings
        self.session = PromptSession(key_bindings=self.kb)

        # Initialize the starting agent
        self._switch_to_agent_by_object(agent)

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

    def _build_system_instruction(self, agent: Agent) -> str:
        """
        Helper to construct the full system prompt for an agent.
        Combines Role, Date, and current CodeBase snapshot.
        """
        # 1. Base Agent Role
        sys_instructions = agent.construct_agent_role_profile()

        # 2. Date Knowledge
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        sys_instructions += f"\n\n### SYSTEM METADATA\nCurrent Date: {current_date}\n"

        # 3. CodeBase Injection (Shared across all agents in this REPL)
        if self.codebase:
            sys_instructions += "\n\n" + self.codebase.render()

        return sys_instructions

    def _get_or_create_chat(self, agent: Agent) -> Any:
        """
        Retrieves an existing chat session for the agent or creates a new one.
        """
        if agent.id in self.sessions:
            return self.sessions[agent.id]

        ui.print_system(f"Initializing Chat Session for {agent.name}...")

        sys_instructions = self._build_system_instruction(agent)

        # Create Chat
        try:
            chat = self.client.chats.create(
                model=self.model_id,
                config=types.GenerateContentConfig(
                    system_instruction=sys_instructions,
                    temperature=0.7
                )
            )
            self.sessions[agent.id] = chat
            return chat
        except Exception as e:
            ui.print_error(f"Failed to initialize Chat for {agent.name}: {e}")
            raise e

    def _rebuild_chat_session(self, agent_id: str, old_chat: Any) -> Any:
        """
        Recreates a chat session with fresh system instructions (updated context/date)
        while preserving the conversation history.
        """
        # 1. Resolve Agent
        # Note: We use Squad to get the agent definition.
        # If the TOML changed on disk, this picks up the new role spec too!
        agent = Squad.get_agent(agent_id)

        # 2. Build Fresh System Prompt (New Date + New CodeBase)
        sys_instructions = self._build_system_instruction(agent)

        # 3. Extract History
        # The unified SDK Chat object maintains a 'history' property (List[Content])
        try:
            # Attempt standard method defined in intents/blueprints
            history = old_chat.get_history()
        except AttributeError:
            # Fallback for SDK versions where it might be private
            history = getattr(old_chat, "_history", [])

        # 4. Create New Chat with the existing history
        return self.client.chats.create(
            model=self.model_id,
            history=history,
            config=types.GenerateContentConfig(
                system_instruction=sys_instructions,
                temperature=0.7
            )
        )

    def _refresh_context(self) -> None:
        """
        Reloads the CodeBase snapshot and hot-swaps all active chat sessions
        to inject the new context and current date.
        """
        ui.print_system("Refreshing CodeBase snapshot and Session Context...")

        # 1. Reload CodeBase
        if self.codebase:
            try:
                # Re-instantiate to traverse filesystem again
                self.codebase = CodeBase(self.codebase.root_path)
                ui.print_system(f"CodeBase re-scanned: {self.codebase.root_path}")
            except Exception as e:
                ui.print_error(f"Failed to reload CodeBase: {e}")
                return
        else:
             ui.print_warning("Running in Greenfield mode (No CodeBase to refresh). Updating Date only.")

        # 2. Hot-Swap Sessions
        # Iterate over all cached sessions and rebuild them
        count = 0
        for agent_id, old_chat in list(self.sessions.items()):
            try:
                new_chat = self._rebuild_chat_session(agent_id, old_chat)
                self.sessions[agent_id] = new_chat
                count += 1
            except Exception as e:
                ui.print_error(f"Failed to refresh session for {agent_id}: {e}")

        # 3. Update Active Pointer
        # Ensure the active_chat reference points to the newly created object
        if self.active_agent:
            self.active_chat = self.sessions.get(self.active_agent.id)

        ui.print_success(f"Context refreshed for {count} active sessions.")
        ui.print_system(f"System Date updated to: {datetime.datetime.now().strftime('%Y-%m-%d')}")

    def _switch_to_agent_by_object(self, agent: Agent) -> None:
        """
        Internal helper to switch context to a specific Agent object.
        """
        try:
            self.active_chat = self._get_or_create_chat(agent)
            self.active_agent = agent

            # Log the switch
            self._log_to_file(f"\n{'='*40}\nSWITCHED AGENT: {agent.get_identity()}\n{'='*40}\n")

            # Update UI
            cb_root = str(self.codebase.root_path) if self.codebase else None
            ui.render_session_header(
                agent_name=self.active_agent.get_identity(),
                model_id=self.model_id,
                codebase_root=cb_root
            )
        except Exception as e:
            ui.print_error(f"Could not switch to agent {agent.name}: {e}")

    def _switch_to_agent_by_name(self, name: str) -> bool:
        """
        Resolves agent name via Squad and switches.
        Returns True if successful.
        """
        try:
            new_agent = Squad.get_agent(name)
            self._switch_to_agent_by_object(new_agent)
            return True
        except ValueError:
            ui.print_error(f"Agent '{name}' not found.")
            ui.print_system(f"Available: {', '.join(Squad.list_agents())}")
            return False
        except Exception as e:
            ui.print_error(f"Error switching agent: {e}")
            return False

    def start(self) -> None:
        """
        Starts the interactive loop.
        """
        ui.print_system("Tip: Press 'Alt+Enter' (or Esc+Enter) to submit. Type '/help' for commands.")

        # Log Session Start
        self._log_to_file(f"\n{'='*40}\nSESSION START: {datetime.datetime.now()}\n{'='*40}\n")

        while True:
            # Dynamic Prompt Styling based on Active Agent
            agent_label = self.active_agent.name if self.active_agent else "Unknown"
            prompt_text = HTML(f"<b><style fg='cyan'>[{agent_label}]</style></b> >> ")

            try:
                # 1. READ
                user_input = self.session.prompt(prompt_text, multiline=True)

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
            cb_root = str(self.codebase.root_path) if self.codebase else None
            ui.render_session_header(
                agent_name=self.active_agent.get_identity(),
                model_id=self.model_id,
                codebase_root=cb_root
            )
            return True

        # Update / Hot-Reload Context
        if cmd == "/update":
            self._refresh_context()
            return True

        # Help
        if cmd == "/help":
            ui.print_system("--- COMMANDS ---")
            ui.print_system(" /agent [name] : Switch active agent (or list available).")
            ui.print_system(" /update       : Refresh CodeBase snapshot and System Date.")
            ui.print_system(" /save         : Auto-save the last generated artifact.")
            ui.print_system(" /exit, /quit  : End the session.")
            ui.print_system(" /clear        : Clear the terminal screen.")
            ui.print_system(" /help         : Show this menu.")
            ui.print_system("--- KEYBINDINGS ---")
            ui.print_system(" Alt+Enter     : Submit input.")
            ui.print_system(" Enter         : Insert newline.")
            return True

        # Agent Switching
        if cmd == "/agent":
            if not args:
                # List agents
                agents = Squad.list_agents()
                ui.print_system(f"Current Agent: {self.active_agent.name}")
                ui.print_system(f"Available Agents: {', '.join(agents)}")
                ui.print_system("Usage: /agent <name>")
            else:
                target_name = args[0]
                self._switch_to_agent_by_name(target_name)
            return True

        # Auto-Save Artifact
        if cmd == "/save":
            self._cmd_save()
            return True

        return False

    def _handle_input(self, text: str) -> None:
        """
        Sends input to the model, streams the response, and logs the turn.
        """
        # Log User Input
        self._log_to_file(f"\n[USER ({self.active_agent.name})]: {text}\n")

        # Visual separator
        ui.console.print()

        full_response = []

        try:
            # SDK Call: Stream Message using ACTIVE chat
            if not self.active_chat:
                ui.print_error("No active chat session.")
                return

            response_stream = self.active_chat.send_message_stream(text)

            for chunk in response_stream:
                if chunk.text:
                    ui.stream_chunk(chunk.text)
                    full_response.append(chunk.text)

            # Print newline after stream ends
            ui.console.print()

            # Capture full response for state tracking (Auto-Save)
            self.last_response = "".join(full_response)

            # Log Model Response
            self._log_to_file(f"\n[MODEL ({self.active_agent.name})]: {self.last_response}\n")
            self._log_to_file("-" * 40)

        except Exception as e:
            ui.print_error(f"Generation Error: {e}")
            self._log_to_file(f"\n[ERROR]: {e}\n")

    def _parse_artifact(self, text: str) -> Tuple[str, str, str]:
        """
        Parses the text using markdown-it-py to locate the first code block
        containing YAML frontmatter.

        Returns:
            Tuple[str, str, str]: (content, directory, filename)
        """
        # 1. Parse into Tokens
        md = MarkdownIt()
        tokens = md.parse(text)

        candidate_content = None
        target_token = None

        # 2. Iterate tokens to find a fence block with YAML
        for token in tokens:
            if token.type == 'fence':
                # Check if the inner content starts with a YAML block
                if token.content.strip().startswith('---'):
                    candidate_content = token.content
                    target_token = token
                    break

        if target_token:
            # Check for nested block truncation (Bug Fix)
            # Peek at type to see if this is a Document (Design/Blueprint)
            is_doc = False
            peek_match = re.search(r'type\s*:\s*["\']?(\w+)["\']?', target_token.content, re.IGNORECASE)
            if peek_match and peek_match.group(1).capitalize() in ["Design", "Blueprint", "Intent", "Bug"]:
                is_doc = True

            if is_doc and target_token.map:
                # Greedy Extraction: Capture until the last fence in the text
                lines = text.splitlines(keepends=True)
                start_line = target_token.map[0]
                last_fence_idx = -1
                for j in range(len(lines) - 1, start_line, -1):
                    if lines[j].strip().startswith('```') or lines[j].strip().startswith('~~~'):
                        last_fence_idx = j
                        break

                if last_fence_idx > start_line:
                    candidate_content = "".join(lines[start_line + 1 : last_fence_idx])
                else:
                    candidate_content = target_token.content
            else:
                candidate_content = target_token.content


        # 3. Fallback: Check if the entire response is the artifact (no code blocks)
        if not candidate_content and text.strip().startswith('---'):
            candidate_content = text

        # If nothing found, return empty/default
        if not candidate_content:
            return text, "output", "artifact.md"

        # 4. Extract Metadata from the *clean* candidate content
        # Matches: --- \n ... type: Value ... \n ---
        # Note: Using case-insensitive (?i) for 'Type' based on bug report
        yaml_pattern = re.compile(
            r'^---\s+.*?(?:type|Type)\s*:\s*["\']?(\w+)["\']?.*?---',
            re.DOTALL | re.MULTILINE
        )

        artifact_type = "Output"
        yaml_match = yaml_pattern.search(candidate_content)
        if yaml_match:
            artifact_type = yaml_match.group(1)

        # 5. Extract Title for Filename
        title_match = re.search(r'^#\s+(.+)$', candidate_content, re.MULTILINE)
        if title_match:
            raw_title = title_match.group(1).strip()
            clean_title = raw_title.lower().replace(" ", "-")
            clean_title = re.sub(r'[^a-z0-9-]', '', clean_title)
            filename = f"{clean_title}.md"
        else:
            ts = datetime.datetime.now().strftime("%H%M%S")
            filename = f"artifact-{ts}.md"

        # 6. Map Directory
        dir_map = {
            "Design": "designs",
            "Blueprint": "blueprints",
            "Intent": "intents"
        }
        # Normalize case from regex capture
        directory = dir_map.get(artifact_type.capitalize(), "output")

        return candidate_content, directory, filename

    def _cmd_save(self) -> None:
        """
        Executes the save logic for the last response.
        """
        if not self.last_response:
            ui.print_error("Nothing to save. Generate something first.")
            return

        try:
            # Parse
            content, directory, filename = self._parse_artifact(self.last_response)

            # Resolve Path
            # If codebase is active, save relative to root. Else CWD.
            root = self.codebase.root_path if self.codebase else Path.cwd()
            target_dir = root / directory
            target_file = target_dir / filename

            # Create Directory
            target_dir.mkdir(parents=True, exist_ok=True)

            # Check existence for UI feedback
            is_overwrite = target_file.exists()

            # Write File
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(content)
                # Ensure newline at end
                if not content.endswith("\n"):
                    f.write("\n")

            if is_overwrite:
                ui.print_warning(f"Overwrote {directory.rstrip('s')} at {directory}/{filename}")
            else:
                ui.print_success(f"Saved {directory.rstrip('s')} to {directory}/{filename}")

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

