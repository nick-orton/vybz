import sys
import vybz.ui as ui
from pathlib import Path
from typing import Dict, List, Type
from vybz.agent import Agent


class Squad:
    """
    A helper class to manage a collection (Squad) of AI Agents.

    This class implements a lazy-loading singleton pattern. It scans the
    'agents/' directory for TOML configurations and initializes them into
    Agent objects only when accessed.
    """
    _agents: Dict[str, Agent] = {}
    _initialized: bool = False
    _source_dir: Path = Path(__file__).parent / "agents"

    @classmethod
    def _initialize(cls) -> None:
        """
        Scans the agents directory and initializes Agent objects.
        This method is idempotent.
        """
        if cls._initialized:
            return

        ui.print_system(f"Spinning up the Squad ({cls._source_dir})")

        if not cls._source_dir.exists():
            ui.print_warning(f"Directory '{cls._source_dir}' not found.")
            return

        count = 0
        for entry in cls._source_dir.glob("*.toml"):
            # Explicitly ignore template files
            if entry.name.endswith(".template"):
                continue

            try:
                # Use filename stem as the unique key (e.g., 'junior-dev')
                key = entry.stem
                agent = Agent.from_toml(entry)
                cls._agents[key] = agent

                # Log success
                ui.print_success(f"Activated: {key:<15} | {agent.get_identity()}")
                count += 1
            except Exception as e:
                ui.print_error(f"Failed to load '{entry.name}': {e}")

        cls._initialized = True
        ui.print_system(f"Squad Ready: {count} agents loaded")
        # Print a visual separator to stderr to separate init from app logic
        ui.error_console.print("")

    @classmethod
    def get_agent(cls, name: str) -> Agent:
        """
        Retrieves a specific agent by name. Triggers initialization if needed.

        Args:
            name: The identifier of the agent (filename stem, e.g., 'junior-dev').

        Returns:
            The requested Agent instance.

        Raises:
            ValueError: If the agent is not found in the squad.
        """
        if not cls._initialized:
            cls._initialize()

        if name not in cls._agents:
            available = list(cls._agents.keys())
            raise ValueError(f"Agent '{name}' not found. Available: {available}")

        return cls._agents[name]

    @classmethod
    def list_agents(cls) -> List[str]:
        """
        Returns a list of available agent identifiers.

        Returns:
            List[str]: Keys of all loaded agents.
        """
        if not cls._initialized:
            cls._initialize()
        return list(cls._agents.keys())
