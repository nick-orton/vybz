"""
src/vybz/commands/core.py

Concrete implementations of standard REPL commands.
"""

from typing import List
from pathlib import Path
from prompt_toolkit.enums import EditingMode

from vybz.commands.base import Command
from vybz import ui
from vybz.squad import Squad
from vybz.artifact import ArtifactProcessor
from vybz.assets.loader import AssetLoader
from vybz.skill import Skill



class ExitCommand(Command):
    name = "/exit"
    aliases = ["/quit", "exit", "quit"]
    description = "End the session."

    def execute(self, session, args: List[str]) -> bool:
        raise EOFError


class ClearCommand(Command):
    name = "/clear"
    description = "Clear the terminal screen."

    def execute(self, session, args: List[str]) -> bool:
        ui.console.clear()

        # Redraw header
        sm = session.session_manager
        codebase = sm.codebase
        cb_root = str(codebase.root_path) if codebase else None

        ui.render_session_header(
            agent_name=sm.active_agent.get_identity(),
            model_id=sm.model_id,
            codebase_root=cb_root
        )
        return True


class UpdateCommand(Command):
    name = "/update"
    description = "Refresh CodeBase snapshot and System Date."

    def execute(self, session, args: List[str]) -> bool:
        ui.print_system("Refreshing CodeBase snapshot and Session Context...")
        count = session.session_manager.refresh_context()
        ui.print_success(f"Context refreshed for {count} active sessions.")

        import datetime
        ui.print_system(f"System Date updated to: {datetime.datetime.now().strftime('%Y-%m-%d')}")
        return True


class HelpCommand(Command):
    name = "/help"
    aliases = ["/helpd"]
    description = "Show the help menu."

    def execute(self, session, args: List[str]) -> bool:
        content = AssetLoader.load_text("repl_help.txt")
        ui.print_panel(content, title="Help Menu")
        return True


class AgentCommand(Command):
    name = "/agent"
    description = "Switch active agent (or list available)."

    def execute(self, session, args: List[str]) -> bool:
        if not args:
            # List agents
            agents = Squad.list_agents()
            template = AssetLoader.load_text("agent_tool_tip.txt")
            ui.print_from_template(
                template,
                agent_name=session.session_manager.active_agent.name,
                agent_list=', '.join(agents)
            )
            return True

        target_name = args[0]
        try:
            agent = session.session_manager.switch_agent(target_name)

            # Log switch
            session.logger.log_event(f"SWITCHED AGENT: {agent.get_identity()}")

            # Update UI
            codebase = session.session_manager.codebase
            cb_root = str(codebase.root_path) if codebase else None
            ui.render_session_header(
                agent_name=agent.get_identity(),
                model_id=session.session_manager.model_id,
                codebase_root=cb_root
            )
            return True
        except ValueError:
            ui.print_error(f"Agent '{target_name}' not found.")
            ui.print_system(f"Available: {', '.join(Squad.list_agents())}")
            return False
        except Exception as e:
            ui.print_error(f"Error switching agent: {e}")
            return False


class SaveCommand(Command):
    name = "/save"
    description = "Auto-save the last generated artifact(s)."

    def execute(self, session, args: List[str]) -> bool:
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
                # Single file UX (Legacy feel)
                msg = messages[0]
                if "Overwrote" in msg:
                    ui.print_warning(msg)
                else:
                    ui.print_success(msg)
            elif len(messages) > 1:
                # Multi-file UX
                ui.print_success(f"Batch Save: Processed {len(messages)} artifacts.")
                for msg in messages:
                    ui.print_system(f"  • {msg}")

            # 5. Auto-Update Context if we are in a codebase
            if codebase and messages:
                session.session_manager.refresh_context()

        except Exception as e:
            ui.print_error(f"Save failed: {e}")

        return True


class LoadCommand(Command):
    name = "/load"
    description = "Load a file into context."

    def execute(self, session, args: List[str]) -> bool:
        if not args:
            ui.print_error("Usage: /load <path>")
            return True

        try:
            path = session.session_manager.load_file(args[0])
            session.session_manager.refresh_context()
            ui.print_success(f"Loaded {path} into context.")
        except Exception as e:
            ui.print_error(f"Failed to load file: {e}")
        
        return True

class SetModeCommand(Command):
    name = "/set"
    description = "Set input mode (vi | emacs)."

    def execute(self, session, args: List[str]) -> bool:
        if not args:
            ui.print_error("Usage: /set <mode> (vi | emacs)")
            return True

        # Normalize input to uppercase to match Enum member names (VI, EMACS)
        target_mode_str = args[0].upper()

        try:
            # Direct lookup against the Enum type
            new_mode = EditingMode[target_mode_str]

            # Apply state change
            session.session.editing_mode = new_mode
            ui.print_success(f"Input mode set to {target_mode_str}")

        except KeyError:
            # Dynamically generate list of valid options from the Enum
            valid_options = ", ".join([m.name.lower() for m in EditingMode])
            ui.print_error(f"Invalid mode '{args[0]}'. Options: {valid_options}")

        return True

class ThemeCommand(Command):
    name = "/theme"
    description = "Set UI color theme."

    def execute(self, session, args: List[str]) -> bool:
        if not args:
            ui.print_error("Usage: /theme <name>")
            return True

        if ui.set_theme(args[0]):
            ui.print_success(f"Theme set to '{args[0]}'")
        return True


class SkillsCommand(Command):
    name = "/skills"
    description = "Visualize the active agent's capabilities."

    def execute(self, session, args: List[str]) -> bool:
        from rich.table import Table
        agent = session.session_manager.active_agent

        table = Table(title=f"Skills for {agent.name}", box=ui.ROUNDED)
        table.add_column("ID", style="header.label")
        table.add_column("Name", style="header.value")
        table.add_column("Description")

        for skill in agent.skills:
            table.add_row(skill.id, skill.name, skill.description)

        ui.console.print(table)
        return True


class UplevelCommand(Command):
    name = "/uplevel"
    description = "Inject a local skill directory into the active agent."

    def execute(self, session, args: List[str]) -> bool:
        if not args:
            ui.print_error("Usage: /uplevel <path>")
            return True

        try:
            path = Path(args[0]).resolve()
            skill = Skill.from_directory(path)

            session.session_manager.active_agent.add_skill(skill)
            session.session_manager.refresh_context()

            ui.print_success(f"Skill '{skill.name}' injected and context refreshed.")
        except Exception as e:
            ui.print_error(f"Failed to uplevel skill: {e}")

        return True


class DownlevelCommand(Command):
    name = "/downlevel"
    description = "Remove a skill from the active agent."

    def execute(self, session, args: List[str]) -> bool:
        if not args:
            ui.print_error("Usage: /downlevel <id>")
            return True

        skill_id = args[0]
        if session.session_manager.active_agent.remove_skill(skill_id):
            session.session_manager.refresh_context()
            ui.print_success(f"Skill '{skill_id}' removed.")
        else:
            ui.print_error(f"Skill '{skill_id}' not found on active agent.")

        return True

