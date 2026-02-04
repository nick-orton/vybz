"""
skill.py

Defines the Skill domain object.
A Skill is a modular unit of context (Knowledge) and instruction (Abilities)
that can be composed into an Agent's persona.
Supports both legacy TOML configuration and AgentSkills.io directory format.
"""

import tomllib
import yaml  # Requires PyYAML
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class Skill:
    """
    Represents a reusable capability or context module.
    
    Attributes:
        id: Unique identifier (filename stem or directory name).
        name: Human-readable name.
        description: Brief summary of the skill.
        knowledge: (Legacy) List of facts.
        abilities: (Legacy) List of instructions.
        instructions: (Standard) Aggregated Markdown content from SKILL.md and subdirectories.
        path: (Standard) Root directory of the skill.
    """
    id: str
    name: str
    description: str
    knowledge: List[str] = field(default_factory=list)
    abilities: List[str] = field(default_factory=list)
    
    # AgentSkills.io Standard (v2)
    instructions: Optional[str] = None
    path: Optional[Path] = None

    @classmethod
    def from_directory(cls, dir_path: Path) -> "Skill":
        """
        Factory method to create a Skill from a standard SKILL.md directory.
        
        Implements the complex parsing logic defined in Phase 1:
        1. Validates metadata in SKILL.md.
        2. Aggregates the body of SKILL.md with all other markdown files 
           found recursively in subdirectories.
        
        Args:
            dir_path: The root directory of the skill.
            
        Returns:
            Initialized Skill instance.
            
        Raises:
            FileNotFoundError: If SKILL.md is missing.
            ValueError: If metadata is invalid or name mismatch occurs.
        """
        skill_file = dir_path / "SKILL.md"
        if not skill_file.exists():
            raise FileNotFoundError(f"Invalid skill directory: {skill_file} missing")

        # 1. Parse Root SKILL.md
        content = skill_file.read_text(encoding="utf-8")
        parts = content.split("---", 2)
        if len(parts) < 3:
            raise ValueError(f"Invalid SKILL.md format in {dir_path}: Missing YAML frontmatter.")
            
        frontmatter = parts[1]
        body = parts[2].strip()
        
        try:
            data = yaml.safe_load(frontmatter)
        except yaml.YAMLError as e:
            raise ValueError(f"Failed to parse YAML in {skill_file}: {e}")

        # Spec Rule: Directory Name must match YAML Name
        if data.get("name") != dir_path.name:
            raise ValueError(
                f"Skill violation: YAML name '{data.get('name')}' "
                f"must match directory name '{dir_path.name}'."
            )

        # 2. Aggregate Subdirectory Content
        # We recursively find all .md files to build the full instructions string
        full_instructions = body
        additional_content = cls._crawl_subdirectories(dir_path)
        if additional_content:
            full_instructions += "\n\n" + additional_content

        return cls(
            id=dir_path.name,
            name=data["name"],
            description=data.get("description", ""),
            path=dir_path,
            instructions=full_instructions,
            # Legacy fields default to empty for v2 skills
            knowledge=[],
            abilities=[]
        )

    @staticmethod
    def _crawl_subdirectories(root: Path) -> str:
        """
        Recursively scans the directory for Markdown files (excluding the root SKILL.md)
        and aggregates them into a single string with structural headers.
        """
        buffer = []
        
        # Use rglob to find all markdown files recursively
        # Sort to ensure deterministic output order
        for path in sorted(root.rglob("*.md")):
            # Skip the root SKILL.md as it is already the head of the instructions
            if path.name == "SKILL.md" and path.parent == root:
                continue
                
            # Calculate relative path to use as a section header
            # e.g., "scripts/advanced_usage.md"
            rel_path = path.relative_to(root)
            
            file_content = path.read_text(encoding="utf-8")
            
            # Strip Frontmatter from sub-files if present to keep the prompt clean
            if file_content.startswith("---"):
                parts = file_content.split("---", 2)
                if len(parts) >= 3:
                    file_content = parts[2].strip()
            
            # Append with a structural header representing the tree
            buffer.append(f"### {rel_path}\n{file_content}")
            
        return "\n\n".join(buffer)

    @classmethod
    def from_toml(cls, file_path: str | Path) -> "Skill":
        """
        Factory method to create a Skill from a legacy TOML file.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Skill definition not found at: {path}")

        with open(path, "rb") as f:
            data = tomllib.load(f)

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
        # 1. New Format (AgentSkills.io)
        if self.instructions:
            output = f"#### {self.name}\n_{self.description}_\n\n{self.instructions}"
            
            # Progressive Disclosure: List Scripts/Refs even if their content was aggregated
            # This provides a quick index at the bottom of the skill block
            if self.path:
                scripts_dir = self.path / "scripts"
                if scripts_dir.exists():
                    scripts = [f.name for f in scripts_dir.iterdir() if f.is_file()]
                    if scripts:
                        output += "\n\n**Available Scripts:**\n"
                        for s in scripts:
                            output += f"* `{s}`\n"
            
            return output

        # 2. Legacy Format (TOML Lists)
        lines = [f"#### {self.name}"]

        if self.description:
            lines.append(f"_{self.description}_")

        if self.knowledge:
            lines.append("")
            lines.append("##### Knowledge")
            for k in self.knowledge:
                lines.append(f"* {k}")

        if self.abilities:
            lines.append("")
            lines.append("##### Abilities")
            for a in self.abilities:
                lines.append(f"* {a}")

        return "\n".join(lines)
