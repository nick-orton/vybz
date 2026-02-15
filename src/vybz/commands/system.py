"""
src/vybz/commands/system.py

Concrete implementations of local system and UI-centric REPL commands.
These commands do not engage the LLM SDK or remote agent state.
"""

from typing import List
from pathlib import Path
from prompt_toolkit.enums import EditingMode

from vybz.commands.base import Command
from vybz import ui
from vybz.artifact import ArtifactProcessor
from vybz.assets.loader import AssetLoader


class ExitCommand(Command):
    """Gracefully terminates the REPL session."""
    name = "/exit"
    aliases = ["/quit", "exit", "quit"]
    description = "End the session."

    async def execute(self, session, args: List[str]) -> bool:
        raise EOFError


class ClearCommand(Command):
    """Clears the terminal buffer and re-renders the header."""
    name = "/clear"
    description = "Clear the terminal screen."

    async def execute(self, session, args: List[str]) -> bool:
        ui.console.clear()

        # Redraw header using session metadata
        sm = session.session_manager
        codebase = sm.codebase
        cb_root = str(codebase.root_path) if codebase else None

        ui.render_session_header(
            agent_name=sm.active_agent.get_identity() if hasattr(sm.active_agent, 'get_identity') else sm.active_agent.name,
            model_id=sm.model_id,
            codebase_root=cb_root
        )
        return True


class HelpCommand(Command):
    """Displays the REPL help menu from static assets."""
    name = "/help"
    aliases = ["/helpd"]
    description = "Show the help menu."

    async def execute(self, session, args: List[str]) -> bool:
        content = AssetLoader.load_text("repl_help.txt")
        ui.print_panel(content, title="Help Menu")
        return True


class SaveCommand(Command):
    """Parses the last agent response and persists artifacts to disk."""
    name = "/save"
    description = "Auto-save the last generated artifact(s)."

    async def execute(self, session, args: List[str]) -> bool:
        if not session.last_response:
            ui.print_error("Nothing to save. Generate something first.")
            return True

        processor = ArtifactProcessor()
        try:
            # 1. Parse (Returns List[Artifact])
            artifacts = processor.parse(session.last_response)

            # 2. Resolve Root
            codebase = session.session_manager.codebase
            root = codebase.root_path if codebase else Path.cwd()

            # 3. Save Loop
            messages = []
            for artifact in artifacts:
                msg = processor.save(artifact, root)
                messages.append(msg)

            # 4. Feedback
            if len(messages) == 1:
                msg = messages[0]
                if "Overwrote" in msg:
                    ui.print_warning(msg)
                else:
                    ui.print_success(msg)
            elif len(messages) > 1:
                ui.print_success(f"Batch Save: Processed {len(messages)} artifacts.")
                for msg in messages:
                    ui.print_system(f"  • {msg}")

        except Exception as e:
            ui.print_error(f"Save failed: {e}")

        return True


class SetModeCommand(Command):
    """Toggles between Vi and Emacs input modes."""
    name = "/set"
    description = "Set input mode (vi | emacs)."

    async def execute(self, session, args: List[str]) -> bool:
        if not args:
            ui.print_error("Usage: /set <mode> (vi | emacs)")
            return True

        target_mode_str = args[0].upper()
        try:
            new_mode = EditingMode[target_mode_str]
            session.session.editing_mode = new_mode
            ui.print_success(f"Input mode set to {target_mode_str}")
        except KeyError:
            valid_options = ", ".join([m.name.lower() for m in EditingMode])
            ui.print_error(f"Invalid mode '{args[0]}'. Options: {valid_options}")

        return True


class ThemeCommand(Command):
    """Hot-swaps the UI color theme."""
    name = "/theme"
    description = "Set UI color theme."

    async def execute(self, session, args: List[str]) -> bool:
        if not args:
            ui.print_error("Usage: /theme <name>")
            return True

        if ui.set_theme(args[0]):
            ui.print_success(f"Theme set to '{args[0]}'")
        return True
