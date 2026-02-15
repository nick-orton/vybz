"""
src/vybz/commands/core.py

Concrete implementations of Agent and Session orchestration commands.
These commands interact with the SessionManager to mutate LLM context.
"""

import datetime
from typing import List
from pathlib import Path

from vybz.commands.base import Command
from vybz import ui
from vybz.shared.squad import Squad
from vybz.shared.skill import Skill
from vybz.assets.loader import AssetLoader


class UpdateCommand(Command):
    """Refreshes the local codebase snapshot and re-primes the LLM context."""
    name = "/update"
    description = "Refresh CodeBase snapshot and System Date."

    def execute(self, session, args: List[str]) -> bool:
        ui.print_system("Refreshing CodeBase snapshot and Session Context...")
        count = session.session_manager.refresh_context()
        ui.print_success(f"Context refreshed for {count} active sessions.")

        ui.print_system(f"System Date updated to: {datetime.datetime.now().strftime('%Y-%m-%d')}")
        return True


class AgentCommand(Command):
    """Switches the active agent persona or lists available options."""
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

            # Log switch event
            if hasattr(session, 'logger'):
                session.logger.log_event(f"SWITCHED AGENT: {agent.get_identity()}")

            # Update UI Header
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


class LoadCommand(Command):
    """Surgically injects a specific file's content into the session context."""
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


class SkillsCommand(Command):
    """Visualizes the current agent's capabilities in a Rich table."""
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
    """Injects a new skill directory into the active agent at runtime."""
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
    """Removes a skill from the active agent persona."""
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
