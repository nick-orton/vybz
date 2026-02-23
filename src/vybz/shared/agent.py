import tomllib  # Built-in in Python 3.11+
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, TYPE_CHECKING
from vybz.shared.skill import Skill
from vybz.shared.library import Library

@dataclass
class Agent:
    """
    Represents an AI Persona with specific role, context, and task definitions.
    Designed to be loaded from configuration files (TOML).
    """
    id: str
    name: str
    version: str
    role_spec: str
    operating_context: str
    task_directive: str
    skills: List[Skill] = field(default_factory=list)

    @classmethod
    def from_toml(cls, file_path: str | Path, library: "Library") -> "Agent":
        """
        Factory method to create an Agent from a TOML file.

        Args:
            file_path: Path to the .toml definition file.
            library: The Library instance for resolving skill paths.

        Returns:
            Initialized Agent instance.

        Raises:
            FileNotFoundError: If file is missing.
            KeyError: If required fields are missing in TOML.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Agent definition not found at: {path}")

        with open(path, "rb") as f:
            data = tomllib.load(f)

        # Validate required fields
        required = ["name", "version", "role_spec", "operating_context", "task_directive"]
        for field in required:
            if field not in data:
                raise KeyError(f"Agent TOML missing required field: '{field}'")

        # Load Skills
        skills_list = []
        skill_ids = data.get("skills", [])

        for skill_id in skill_ids:
            skill_dir = library.get_skill_path(skill_id)
            skills_list.append(Skill.from_directory(skill_dir))

        return cls(
            id=path.stem,
            name=data["name"],
            version=data["version"],
            role_spec=data["role_spec"],
            operating_context=data["operating_context"],
            task_directive=data["task_directive"],
            skills=skills_list
        )

    def get_identity(self) -> str:
        """Returns the signature for logging purposes."""
        return f"{self.name} (v{self.version})"

    def construct_agent_role_profile(self) -> str:
        """
        Composes the system instructions for the model to behave as the agent
        """
        prompt = (
            f"### ROLE SPECIFICATION\n{self.role_spec}\n\n"
            f"### OPERATING CONTEXT\n{self.operating_context}\n\n"
            f"### TASK GUIDELINES\n{self.task_directive}\n\n"
        )

        if self.skills:
            prompt += "### SKILLS & CAPABILITIES\n"
            for skill in self.skills:
                prompt += f"{skill.render()}\n\n"

        return prompt

    def add_skill(self, skill: Skill) -> None:
        """
        Adds a skill to the agent's memory. If a skill with the same ID
        already exists, it is updated.
        """
        for i, s in enumerate(self.skills):
            if s.id == skill.id:
                self.skills[i] = skill
                return
        self.skills.append(skill)

    def remove_skill(self, skill_id: str) -> bool:
        """
        Removes a skill from the agent's memory by ID.
        Returns True if a skill was removed, False otherwise.
        """
        original_len = len(self.skills)
        self.skills = [s for s in self.skills if s.id != skill_id]
        return len(self.skills) < original_len
