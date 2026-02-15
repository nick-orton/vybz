"""
src/vybz/commands/core.py

Concrete implementations of Agent and Session orchestration commands.
Refactored to be asynchronous and communicate with the vybzd engine.
"""

import datetime
from typing import List
from pathlib import Path

from vybz.commands.base import Command
from vybz import ui
from vybz.shared.skill import Skill
from vybz.client.api import SkillDTO
from vybz.assets.loader import AssetLoader


class UpdateCommand(Command):
    """Refreshes the local codebase snapshot and uploads it to the engine."""
    name = "/update"
    description = "Refresh CodeBase snapshot and System Date."

    async def execute(self, session, args: List[str]) -> bool:
        ui.print_system("Refreshing local CodeBase and updating remote context...")
        success = await session.session_manager.refresh_context()
        if success:
            ui.print_success("Context and CodeBase refreshed.")
        return True


class AgentCommand(Command):
    """Switches the active agent persona or lists available options from the server."""
    name = "/agent"
    description = "Switch active agent (or list available)."

    async def execute(self, session, args: List[str]) -> bool:
        sm = session.session_manager
        
        if not args:
            # Fetch available agents from the engine
            try:
                agents = await sm.client.list_agents()
                agent_ids = [a.id for a in agents]
                template = AssetLoader.load_text("agent_tool_tip.txt")
                ui.print_from_template(
                    template,
                    agent_name=sm.active_agent.name if sm.active_agent else "None",
                    agent_list=', '.join(agent_ids)
                )
            except Exception as e:
                ui.print_error(f"Failed to list agents: {e}")
            return True

        target_id = args[0]
        success = await sm.switch_agent(target_id)
        
        if success:
            # Update UI Header
            cb_root = str(sm.codebase.root_path) if sm.codebase else None
            ui.render_session_header(
                agent_name=sm.active_agent.name,
                model_id=sm.model_id,
                codebase_root=cb_root
            )
        return True


class LoadCommand(Command):
    """Surgically injects a local file's content into the remote session context."""
    name = "/load"
    description = "Load a file into context."

    async def execute(self, session, args: List[str]) -> bool:
        if not args:
            ui.print_error("Usage: /load <path>")
            return True

        path = Path(args[0]).resolve()
        if not path.is_file():
            ui.print_error(f"File not found: {path}")
            return True

        try:
            content = path.read_text(encoding="utf-8")
            sm = session.session_manager
            
            success = await sm.client.load_file_content(
                session_id=sm.session_id,
                filename=str(path),
                content=content
            )
            
            if success:
                ui.print_success(f"Loaded {path.name} into remote context.")
        except Exception as e:
            ui.print_error(f"Failed to load file: {e}")
        
        return True


class SkillsCommand(Command):
    """Visualizes the session-scoped agent's capabilities in a Rich table."""
    name = "/skills"
    description = "Visualize the active agent's capabilities."

    async def execute(self, session, args: List[str]) -> bool:
        from rich.table import Table
        sm = session.session_manager
        
        try:
            skills = await sm.client.list_session_skills(sm.session_id)
            
            table = Table(title=f"Skills for {sm.active_agent.name}", box=ui.ROUNDED)
            table.add_column("ID", style="header.label")
            table.add_column("Name", style="header.value")
            table.add_column("Description")

            for s in skills:
                table.add_row(s.id, s.name, s.description)

            ui.console.print(table)
        except Exception as e:
            ui.print_error(f"Failed to fetch skills: {e}")
            
        return True


class UplevelCommand(Command):
    """Injects a local skill directory into the remote session."""
    name = "/uplevel"
    description = "Inject a local skill directory into the active agent."

    async def execute(self, session, args: List[str]) -> bool:
        if not args:
            ui.print_error("Usage: /uplevel <path>")
            return True

        try:
            path = Path(args[0]).resolve()
            # 1. Read locally
            skill = Skill.from_directory(path)
            
            # 2. Upload to engine
            sm = session.session_manager
            dto = SkillDTO(
                id=skill.id,
                name=skill.name,
                description=skill.description,
                instructions=skill.instructions
            )
            
            success = await sm.client.uplevel_skill(sm.session_id, dto)
            if success:
                ui.print_success(f"Skill '{skill.name}' injected into remote session.")
        except Exception as e:
            ui.print_error(f"Failed to uplevel skill: {e}")

        return True


class DownlevelCommand(Command):
    """Removes a skill from the remote session."""
    name = "/downlevel"
    description = "Remove a skill from the active agent."

    async def execute(self, session, args: List[str]) -> bool:
        if not args:
            ui.print_error("Usage: /downlevel <id>")
            return True

        skill_id = args[0]
        sm = session.session_manager
        
        try:
            success = await sm.client.downlevel_skill(sm.session_id, skill_id)
            if success:
                ui.print_success(f"Skill '{skill_id}' removed from remote session.")
            else:
                ui.print_error(f"Skill '{skill_id}' not found on remote agent.")
        except Exception as e:
            ui.print_error(f"Failed to remove skill: {e}")

        return True
