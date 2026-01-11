import tomllib  # Built-in in Python 3.11+
from pathlib import Path
from dataclasses import dataclass

@dataclass
class Agent:
    """
    Represents an AI Persona with specific role, context, and task definitions.
    Designed to be loaded from configuration files (TOML).
    """
    name: str
    version: str
    role_spec: str
    operating_context: str
    task_directive: str

    @classmethod
    def from_toml(cls, file_path: str | Path) -> "Agent":
        """
        Factory method to create an Agent from a TOML file.

        Args:
            file_path: Path to the .toml definition file.

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

        return cls(
            name=data["name"],
            version=data["version"],
            role_spec=data["role_spec"],
            operating_context=data["operating_context"],
            task_directive=data["task_directive"]
        )

    def get_identity(self) -> str:
        """Returns the signature for logging purposes."""
        return f"{self.name} (v{self.version})"

    def construct_agent_role_profile(self) -> str:
        """
        Composes the system instructions for the model to behave as the agent
        """
        return (
            f"### ROLE SPECIFICATION\n{self.role_spec}\n\n"
            f"### OPERATING CONTEXT\n{self.operating_context}\n\n"
            f"### TASK GUIDELINES\n{self.task_directive}\n\n"
        )
