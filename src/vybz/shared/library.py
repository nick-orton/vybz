"""
src/vybz/biblos.py

The central registry for Vybz resources (Agents and Skills).
Implements a layered discovery system allowing user configuration to override
system defaults.
"""

import os
from pathlib import Path
from typing import List, Optional, Set


class Library:
    """
    Manages the discovery and resolution of Agents and Skills.

    Implements a layered configuration system:
    1. Custom Root (CLI arg) - Highest Priority
    2. User Config (~/.config/vybz/library)
    3. System Defaults (package/library) - Lowest Priority
    """

    def __init__(self, custom_root: Optional[Path] = None):
        """
        Initialize the Library with ordered search paths.

        Args:
            custom_root: Optional override path provided via CLI/Config.
        """
        self.search_paths = self._build_search_paths(custom_root)

    def _build_search_paths(self, custom_root: Optional[Path]) -> List[Path]:
        """
        Constructs the list of paths to scan for resources.
        """
        paths = []

        # 1. Custom Root (Highest Priority)
        if custom_root:
            paths.append(custom_root)

        # 2. User Config
        xdg_root = os.getenv("XDG_CONFIG_HOME")
        if xdg_root:
            user_config = Path(xdg_root) / "vybz" / "library"
        else:
            user_config = Path.home() / ".config" / "vybz" / "library"
        paths.append(user_config)

        # 3. System Defaults (Lowest Priority)
        # Assumes this file is in src/vybz/ and the library was moved to src/vybz/library/
        system_default = Path(__file__).parent / "library"
        paths.append(system_default)

        return paths

    def list_agents(self) -> List[str]:
        """
        Scans all search paths for agent definitions.
        Returns a sorted list of unique agent IDs.
        """
        agent_ids: Set[str] = set()

        for root in self.search_paths:
            agents_dir = root / "agents"
            if agents_dir.exists():
                for entry in agents_dir.glob("*.toml"):
                    if entry.is_file() and not entry.name.endswith(".template"):
                        agent_ids.add(entry.stem)

        return sorted(list(agent_ids))

    def get_agent_path(self, agent_id: str) -> Path:
        """
        Resolves the path to an Agent TOML file.
        Respects priority order (Custom > User > System).

        Args:
            agent_id: The filename stem (e.g., 'junior-dev').

        Returns:
            Path: The absolute path to the .toml file.

        Raises:
            FileNotFoundError: If the agent is not found in any search path.
        """
        for root in self.search_paths:
            candidate = root / "agents" / f"{agent_id}.toml"
            if candidate.exists():
                return candidate

        raise FileNotFoundError(
            f"Agent '{agent_id}' not found in library paths: {[str(p) for p in self.search_paths]}"
        )

    def get_skill_path(self, skill_id: str) -> Path:
        """
        Resolves the path to a Skill directory.
        Checks for existence of SKILL.md within the directory to validate.

        Args:
            skill_id: The directory name of the skill (e.g., 'python-standards').

        Returns:
            Path: The absolute path to the skill directory.

        Raises:
            FileNotFoundError: If the skill is not found.
        """
        for root in self.search_paths:
            # Skills are directories: library/skills/{id}/SKILL.md
            candidate_dir = root / "skills" / skill_id
            candidate_file = candidate_dir / "SKILL.md"

            if candidate_dir.exists() and candidate_file.exists():
                return candidate_dir

        raise FileNotFoundError(f"Skill '{skill_id}' not found in library paths.")
