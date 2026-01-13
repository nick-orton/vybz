"""
skill.py

Defines the Skill domain object.
A Skill is a modular unit of context (Knowledge) and instruction (Abilities)
that can be composed into an Agent's persona.
"""

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class Skill:
    """
    Represents a reusable capability or context module.
    """
    id: str
    name: str
    description: str
    knowledge: List[str] = field(default_factory=list)
    abilities: List[str] = field(default_factory=list)

    @classmethod
    def from_toml(cls, file_path: str | Path) -> "Skill":
        """
        Factory method to create a Skill from a TOML file.

        Args:
            file_path: Path to the .toml definition file.

        Returns:
            Initialized Skill instance.

        Raises:
            FileNotFoundError: If file is missing.
            KeyError: If required fields are missing in TOML.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Skill definition not found at: {path}")

        with open(path, "rb") as f:
            data = tomllib.load(f)

        # Validate minimal required fields
        if "name" not in data:
            raise KeyError(f"Skill TOML at {path} missing required field: 'name'")

        return cls(
            id=path.stem,
            name=data.get("name", "Unknown Skill"),
            description=data.get("description", ""),
            knowledge=data.get("knowledge", []),
            abilities=data.get("abilities", [])
        )

    def render(self) -> str:
        """
        Formats the skill into Markdown for injection into the system prompt.
        """
        lines = [f"#### {self.name}"]

        if self.description:
            lines.append(f"_{self.description}_")

        if self.knowledge:
            lines.append("")  # Spacer
            for k in self.knowledge:
                lines.append(f"* {k}")

        if self.abilities:
            lines.append("")  # Spacer
            for a in self.abilities:
                lines.append(f"* {a}")

        return "\n".join(lines)
