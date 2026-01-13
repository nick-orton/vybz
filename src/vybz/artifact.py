"""
artifact.py

Handles the parsing, routing, and persistence of generated artifacts.
Decouples text processing from the REPL session management.
"""

import re
import datetime
from dataclasses import dataclass
from pathlib import Path

from markdown_it import MarkdownIt


@dataclass
class Artifact:
    """
    Represents a structured file extracted from LLM output.
    """
    content: str
    filename: str
    directory: str  # e.g., "designs", "blueprints", "output"
    type: str       # e.g., "Design", "Blueprint", "Output"


class ArtifactProcessor:
    """
    Stateless service for extracting and saving artifacts.
    """

    def __init__(self) -> None:
        self.md = MarkdownIt()

    def parse(self, text: str) -> Artifact:
        """
        Parses the text using markdown-it-py to locate the first code block
        containing YAML frontmatter or falls back to raw text.

        Args:
            text: The raw response string from the Agent.

        Returns:
            Artifact: The populated domain object.
        """
        # 1. Parse into Tokens
        tokens = self.md.parse(text)

        candidate_content = None
        target_token = None

        # 2. Iterate tokens to find a fence block with YAML
        for token in tokens:
            if token.type == 'fence':
                # Check if the inner content starts with a YAML block
                if token.content.strip().startswith('---'):
                    candidate_content = token.content
                    target_token = token
                    break

        if target_token:
            # Check for nested block truncation (Bug Fix Logic)
            # Peek at type to see if this is a Document (Design/Blueprint)
            is_doc = False
            peek_match = re.search(
                r'type\s*:\s*["\']?(\w+)["\']?',
                target_token.content,
                re.IGNORECASE
            )
            if peek_match:
                doc_type = peek_match.group(1).capitalize()
                if doc_type in ["Design", "Blueprint", "Intent", "Bug"]:
                    is_doc = True

            if is_doc and target_token.map:
                # Greedy Extraction: Capture until the last fence in the text
                lines = text.splitlines(keepends=True)
                start_line = target_token.map[0]
                last_fence_idx = -1
                for j in range(len(lines) - 1, start_line, -1):
                    line_stripped = lines[j].strip()
                    if line_stripped.startswith('```') or line_stripped.startswith('~~~'):
                        last_fence_idx = j
                        break

                if last_fence_idx > start_line:
                    candidate_content = "".join(lines[start_line + 1: last_fence_idx])
                else:
                    candidate_content = target_token.content
            else:
                candidate_content = target_token.content

        # 3. Fallback: Check if the entire response is the artifact (no code blocks)
        if not candidate_content and text.strip().startswith('---'):
            candidate_content = text

        # If nothing found, return default wrapper
        if not candidate_content:
            return Artifact(
                content=text,
                filename="artifact.md",
                directory="output",
                type="Output"
            )

        # 4. Extract Metadata
        # Matches: --- \n ... type: Value ... \n ---
        yaml_pattern = re.compile(
            r'^---\s+.*?(?:type|Type)\s*:\s*["\']?(\w+)["\']?.*?---',
            re.DOTALL | re.MULTILINE
        )

        artifact_type = "Output"
        yaml_match = yaml_pattern.search(candidate_content)
        if yaml_match:
            artifact_type = yaml_match.group(1)

        # 5. Extract Title for Filename
        title_match = re.search(r'^#\s+(.+)$', candidate_content, re.MULTILINE)
        if title_match:
            raw_title = title_match.group(1).strip()
            clean_title = raw_title.lower().replace(" ", "-")
            clean_title = re.sub(r'[^a-z0-9-]', '', clean_title)
            filename = f"{clean_title}.md"
        else:
            ts = datetime.datetime.now().strftime("%H%M%S")
            filename = f"artifact-{ts}.md"

        # 6. Map Directory
        dir_map = {
            "Design": "designs",
            "Blueprint": "blueprints",
            "Intent": "intents"
        }
        # Normalize case
        directory = dir_map.get(artifact_type.capitalize(), "output")

        return Artifact(
            content=candidate_content,
            filename=filename,
            directory=directory,
            type=artifact_type
        )

    def save(self, artifact: Artifact, root_path: Path) -> str:
        """
        Persists the artifact to the filesystem.

        Args:
            artifact: The object to save.
            root_path: The base directory (CodeBase root or CWD).

        Returns:
            str: A status message describing the action (Saved/Overwrote).

        Raises:
            IOError: If filesystem write fails.
        """
        target_dir = root_path / artifact.directory
        target_file = target_dir / artifact.filename

        # Create Directory
        target_dir.mkdir(parents=True, exist_ok=True)

        # Check existence for feedback
        is_overwrite = target_file.exists()

        # Write File
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(artifact.content)
            # Ensure newline at end
            if not artifact.content.endswith("\n"):
                f.write("\n")

        action = "Overwrote" if is_overwrite else "Saved"
        # e.g. "Saved Design to designs/my-feature.md"
        return f"{action} {artifact.type} to {artifact.directory}/{artifact.filename}"
