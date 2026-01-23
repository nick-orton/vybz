import sys
from pathlib import Path
from typing import Dict, List
from vybz.agent import Agent
import vybz.ui as ui


class Squad:
    """
    A helper class to manage a collection (Squad) of AI Agents.

    This class implements a Lazy Loading pattern. It does NOT load all agents
    at startup. Instead, it scans the filesystem only when listing agents,
    and parses/instantiates Agent objects only when specifically requested.
    """
    _agents: Dict[str, Agent] = {}  # Cache of loaded agent instances
    _source_dir: Path = Path(__file__).parent / "agents"

    @classmethod
    def get_agent(cls, name: str) -> Agent:
        """
        Retrieves a specific agent by name.
        Instantiates and caches the agent if it hasn't been loaded yet.

        Args:
            name: The identifier of the agent (filename stem, e.g., 'junior-dev').

        Returns:
            The requested Agent instance.

        Raises:
            ValueError: If the agent TOML file does not exist.
            RuntimeError: If the agent fails to load (parsing error).
        """
        # 1. Check Cache
        if name in cls._agents:
            return cls._agents[name]

        # 2. Check Filesystem
        target_file = cls._source_dir / f"{name}.toml"
        if not target_file.exists():
            # Only scan for available agents if we hit a missing agent error
            available = cls.list_agents()
            raise ValueError(f"Agent '{name}' not found. Available: {available}")

        # 3. Load & Cache
        try:
            agent = Agent.from_toml(target_file)
            cls._agents[name] = agent
            # We log to system (stderr) so we don't pollute stdout for tools
            ui.print_system(f"Loaded Agent: {agent.get_identity()}")
            return agent
        except Exception as e:
            raise RuntimeError(f"Failed to load agent '{name}' from {target_file}: {e}")

    @classmethod
    def list_agents(cls) -> List[str]:
        """
        Scans the agents directory for valid configuration files.
        Does NOT instantiate Agent objects.

        Returns:
            List[str]: A sorted list of available agent identifiers.
        """
        if not cls._source_dir.exists():
            ui.print_warning(f"Agents directory '{cls._source_dir}' not found.")
            return []

        agent_names = []
        for entry in cls._source_dir.glob("*.toml"):
            # Explicitly ignore template files
            if entry.name.endswith(".template"):
                continue
            agent_names.append(entry.stem)

        return sorted(agent_names)

