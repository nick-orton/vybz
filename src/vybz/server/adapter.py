"""
src/vybz/server/adapter.py

The ADK Adapter Layer.
Responsible for hydrating Vybz proprietary configuration objects (Agents, Skills)
into executable Google Agent Development Kit (ADK) objects.
"""

from typing import Dict
from vybz.shared.agent import Agent as VybzAgent
from vybz.shared.library import Library
from google.genai import types
import google.adk as adk


class AdkHydrator:
    """
    Service class to convert Vybz domain objects into ADK runtime objects.
    """

    def hydrate_agent(self, vybz_agent: VybzAgent, model: str) -> adk.Agent:
        """
        Converts a Vybz Agent (configuration) into an ADK Agent (executable).

        Args:
            vybz_agent: The loaded Vybz agent definition.
            model: The Google GenAI model ID to use.

        Returns:
            adk.Agent: An initialized ADK agent ready for the runtime.
        """

        # System Prompt Assembly
        # Reuse existing logic that combines Role, Context, and Skills
        system_prompt = vybz_agent.construct_agent_role_profile()

        # Model Configuration
        # ADK v1.24+ Agent initialization
        adk_id = vybz_agent.id.replace("-","_")

        # Define the Thinking Config
        thinking_config = types.ThinkingConfig(
            include_thoughts=True,
            thinking_budget=1024  # Optional: token budget for reasoning
        )

        return adk.Agent(
            name=adk_id,
            model=model,
            description=vybz_agent.name, # Map human-readable name to description
            instruction=system_prompt,
            planner=adk.planners.BuiltInPlanner(thinking_config=thinking_config),
            tools=[] # Future: Hydrate tools from Skills if executable
        )

    def hydrate_squad_templates(self, library: Library) -> Dict[str, VybzAgent]:
        """
        Loads the Vybz Agent definitions from the library.
        Returns a dictionary of VybzAgent objects to serve as templates.

        We do NOT hydrate ADK agents here because we need a fresh ADK Agent instance
        per session to support unique context injection (mutable instructions).

        Args:
            library: The initialized Vybz Library service.

        Returns:
            Dict[str, VybzAgent]: Mapping of agent_id to Vybz Agent configuration objects.
        """
        registry: Dict[str, VybzAgent] = {}
        agent_ids = library.list_agents()

        for agent_id in agent_ids:
            try:
                path = library.get_agent_path(agent_id)
                vybz_agent = VybzAgent.from_toml(path, library=library)
                registry[agent_id] = vybz_agent
            except Exception as e:
                print(f"Failed to load agent template '{agent_id}': {e}")

        return registry
