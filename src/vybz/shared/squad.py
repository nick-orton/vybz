import sys
from pathlib import Path
from typing import Dict, List, Optional
from vybz.shared.agent import Agent
from vybz.shared.library import Library
from vybz.shared.config import ConfigLoader
import vybz.client.ui as ui


class Squad:
    """
    A helper class to manage a collection (Squad) of AI Agents.

    This class implements a Lazy Loading pattern. It does NOT load all agents
    at startup. Instead, it delegates discovery to the Library service.
    """
    _agents: Dict[str, Agent] = {}  # Cache of loaded agent instances
    _library: Optional[Library] = None

    @classmethod
    def _get_library(cls) -> Library:
        """
        Retrieves or initializes the Library instance.
        """
        if cls._library is None:
            # Check for 'library' in user config if not initialized via CLI
            config = ConfigLoader.load()
            lib_path = config.get("library")
            custom_root = Path(lib_path) if lib_path else None
            cls._library = Library(custom_root=custom_root)
        return cls._library

    @classmethod
    def initialize(cls, custom_library_root: Optional[Path] = None) -> None:
        """
        Explicitly initializes the Squad with a specific library root.
        This is typically called by the CLI if --library is provided.
        """
        cls._library = Library(custom_root=custom_library_root)
        cls._agents.clear() # Invalidate cache if library changes

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

        library = cls._get_library()

        # 2. Resolve Path via Library
        try:
            target_file = library.get_agent_path(name)
        except FileNotFoundError:
            available = cls.list_agents()
            raise ValueError(f"Agent '{name}' not found. Available: {available}")

        # 3. Load & Cache
        try:
            # Dependency Injection: Pass library to Agent so it can resolve skills
            agent = Agent.from_toml(target_file, library=library)
            cls._agents[name] = agent
            # We log to system (stderr) so we don't pollute stdout for tools
            ui.print_system(f"Loaded Agent: {agent.get_identity()}")
            return agent
        except Exception as e:
            raise RuntimeError(f"Failed to load agent '{name}' from {target_file}: {e}")

    @classmethod
    def list_agents(cls) -> List[str]:
        """
        Delegates to Library to list available agents.

        Returns:
            List[str]: A sorted list of available agent identifiers.
        """
        return cls._get_library().list_agents()

