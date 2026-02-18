"""
src/vybz/server/state.py

Singleton container for the Vybz Server runtime state.
Manages the lifecycle of Agents, Runners, and the Session Service.
Implements the ADK v1.24+ architecture (Agent -> Runner -> Session).
"""

import uuid
from typing import Dict, Optional, List, Any

from google.adk import Runner
from google.adk.tools import FunctionTool
from google.adk.sessions import InMemorySessionService, Session

from vybz.shared.library import Library
from vybz.shared.agent import Agent as VybzAgent
from vybz.shared.skill import Skill as VybzSkill
from vybz.server.adapter import AdkHydrator
from vybz.server.tools.fs import FileSystemTools
from vybz.config import ConfigLoader
from vybz.services.context import ContextAssembler


class ServerState:
    """
    Holds the runtime state for the vybzd engine.
    Manages the mapping between Session IDs and their dedicated Runners.
    """

    def __init__(self) -> None:
        # Configuration
        self.model_id: str = "gemini-3-flash-preview"
        self.user_id: str = str(uuid.uuid4())
        self.app_name = "vybzd"

        # Domain Services
        self.library: Optional[Library] = None
        self.hydrator = AdkHydrator()
        self.session_service = InMemorySessionService()

        # Templates: VybzAgent definitions loaded from disk (Read-Only)
        self.agent_templates: Dict[str, VybzAgent] = {}

        # Runtime: Mapping of session_id -> Runner
        # We maintain a dedicated Runner per session to allow for
        # session-specific Agent instruction mutation (Context/Skills).
        self.runners: Dict[str, Runner] = {}

    def initialize(self) -> None:
        """
        Bootstraps the server state.
        Loads configuration and hydrates agent templates.
        """
        # 1. Load User Config
        config = ConfigLoader.load()
        self.model_id = config.get("model", self.model_id)

        # 2. Initialize Library
        self.library = Library()

        # 3. Load Templates
        self.agent_templates = self.hydrator.hydrate_squad_templates(self.library)

        print(f"[vybzd] Initialized. Loaded {len(self.agent_templates)} agent templates.")
        print(f"[vybzd] Model: {self.model_id}")

    async def create_session(self, agent_id: str, context: str = "") -> str:
        """
        Initializes a new chat session.

        Architecture:
        1. Retrieves the VybzAgent template.
        2. Hydrates a FRESH adk.Agent instance (to allow isolated instruction mutation).
        3. Creates a FRESH adk.Runner linked to this agent and the global SessionService.
        4. Creates a session via the service.
        5. Injects initial context (CodeBase) into the runner's agent instructions.

        Returns:
            str: The session UUID.
        """
        print(f"[vybzd] creating session for {agent_id}")
        if agent_id not in self.agent_templates:
            raise ValueError(f"Agent '{agent_id}' not found.")

        # 1. Clone Vybz Agent (for mutable state tracking like manual_context)
        # We reload from TOML or deepcopy to ensure isolation
        path = self.library.get_agent_path(agent_id)
        vybz_agent = VybzAgent.from_toml(path, library=self.library)

        # 2. Setup Session-Scoped Tools (Agentic RAG)
        tools = []
        if context:
            # In Step 3.6, 'context' is the absolute root path string
            fs_impl = FileSystemTools(context)
            tools = [
                FunctionTool(fs_impl.list_files),
                FunctionTool(fs_impl.read_file)
            ]

        # 3. Hydrate unique ADK Agent with Tools
        adk_agent = self.hydrator.hydrate_agent(vybz_agent, self.model_id, tools=tools)

        # 4. Initialize Runner
        # The Runner orchestrates this specific agent instance
        runner = Runner(
            agent=adk_agent,
            app_name=self.app_name,
            session_service=self.session_service
        )

        # 4. Create Session
        #    Initialize Vybz State within the Session object
        #    We store the VybzAgent object in the session metadata for skill/context tracking
        session = await self.session_service.create_session(
                            app_name = self.app_name,
                            user_id=self.user_id,
                            state={
                                "vybz_agent": vybz_agent,
                                "manual_context": {},
                                "codebase_context": context
                            }
        )
        session_id = session.id


        # 6. Register Runner
        self.runners[session_id] = runner


        # 7. Initial Instruction Assembly
        await self._refresh_session_instructions(session_id)

        return session_id

    def get_runner(self, session_id: str) -> Runner:
        """Retrieves the Runner responsible for a specific session."""
        if session_id not in self.runners:
            raise ValueError(f"Session '{session_id}' not found or expired.")
        return self.runners[session_id]

    async def get_session_data(self, session_id: str) -> Session:
        """Helper to get the raw session object from the service."""
        session = await self.session_service.get_session(session_id=session_id, app_name=self.app_name, user_id=self.user_id)
        if not session:
            raise ValueError(f"Session '{session_id}' not found in service.")
        return session

    # -------------------------------------------------------------------------
    # Mutation Logic
    # -------------------------------------------------------------------------

    async def get_session_skills(self, session_id: str) -> List[VybzSkill]:
        """Returns the list of skills from the session-scoped agent."""
        session = await self.get_session_data(session_id)
        vybz_agent: VybzAgent = session.state.get("vybz_agent")
        return vybz_agent.skills if vybz_agent else []

    async def uplevel_session_skill(self, session_id: str, skill_data: dict) -> None:
        """Injects a skill into the session."""
        session = await self.get_session_data(session_id)
        vybz_agent: VybzAgent = session.state.get("vybz_agent")

        new_skill = VybzSkill(
            id=skill_data["id"],
            name=skill_data["name"],
            description=skill_data["description"],
            instructions=skill_data["instructions"]
        )

        vybz_agent.add_skill(new_skill)
        await self._refresh_session_instructions(session_id)

    async def downlevel_session_skill(self, session_id: str, skill_id: str) -> bool:
        """Removes a skill from the session."""
        session = await self.get_session_data(session_id)
        vybz_agent: VybzAgent = session.state.get("vybz_agent")

        if vybz_agent and vybz_agent.remove_skill(skill_id):
            await self._refresh_session_instructions(session_id)
            return True
        return False

    async def load_session_context(self, session_id: str, filename: str, content: str) -> None:
        """Injects a specific file into the session context."""
        session = await self.get_session_data(session_id)
        manual_ctx: dict = session.state.get("manual_context", {})
        manual_ctx[filename] = content
        session.state["manual_context"] = manual_ctx

        await self._refresh_session_instructions(session_id)

    async def _refresh_session_instructions(self, session_id: str) -> None:
        """
        Re-assembles system instructions and updates the Runner's Agent.
        This is the mechanism for "Hot Reloading" context in the ADK architecture.
        """
        session = await self.get_session_data(session_id)
        runner = self.get_runner(session_id)

        vybz_agent: VybzAgent = session.state.get("vybz_agent")
        manual_context = session.state.get("manual_context", {})
        codebase_str = session.state.get("codebase_context", "")

        # 1. Build Base Prompt (Persona + Skills + Manual Context)
        base_prompt = ContextAssembler.build_system_instruction(
            vybz_agent,
            codebase_root=codebase_str, # In 3.6 this is the path
            manual_context=manual_context
        )

        # 2. Full Instruction
        full_instruction = base_prompt

        # 3. Update the ADK Agent (Dynamic Property)
        # Since we have a unique Runner/Agent per session, this is safe.
        runner.agent.instruction = full_instruction
