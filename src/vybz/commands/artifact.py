"""
artifact.py

Handles the parsing, routing, and persistence of generated artifacts.
Decouples text processing from the REPL session management.
"""

import re
import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Any, Dict

from markdown_it import MarkdownIt
from markdown_it.token import Token


@dataclass
class Artifact:
    """
    Represents a structured file extracted from LLM output.
    """
    content: str
    filename: str
    directory: str  # e.g., "designs", "blueprints", "output"
    type: str       # e.g., "Design", "Blueprint", "Output"

# -----------------------------------------------------------------------------
# Polymorphic Handlers (Phase 1 Refactor)
# -----------------------------------------------------------------------------

class ArtifactHandler(ABC):
    """
    Abstract base class for artifact parsing strategies.
    Each handler is responsible for recognizing and extracting a specific
    type of artifact (Document, Diff, CodeFile, etc.) from a Markdown token.
    """

    @abstractmethod
    def can_handle(self, token: Token) -> bool:
        """
        Determines if this handler can process the given Markdown token.
        """
        pass

    @abstractmethod
    def extract(self, token: Token, full_text: str) -> Artifact:
        """
        Extracts the artifact content, determines metadata, and returns
        a populated Artifact domain object.
        """
        pass


class DocumentHandler(ArtifactHandler):
    """
    Handles Documents with YAML Frontmatter (Designs, Blueprints, Intents, Bugs).
    """

    NAMESPACE = ".vybz"
    # Mapping of YAML 'type' to filesystem directory
    DIR_MAP: Dict[str, str] = {
        "Design": "designs",
        "Blueprint": "blueprints",
        "Bug": "bugs",
        "Critique": "critiques",
        "Intent": "intents"
    }

    def can_handle(self, token: Token) -> bool:
        """
        Recognizes fence blocks starting with '---' that contain a 'type:' field.
        """
        if token.type != 'fence':
            return False

        content = token.content.strip()
        # Basic check for YAML frontmatter delimiters
        if not content.startswith('---'):
            return False

        # Check for 'type:' key (case-insensitive) to distinguish from diffs
        if not re.search(r'\b[Tt]ype\s*:', content):
            return False

        return True

    def extract(self, token: Token, full_text: str) -> Artifact:
        """
        Extracts document content, handling nested block truncation logic,
        parses YAML for type, and generates a filename from the H1 header.
        """
        candidate_content = token.content

        # 1. Nested Block Truncation Fix (Greedy Extraction)
        # Only apply map logic if map exists (it won't for synthetic tokens)
        if token.map:
            lines = full_text.splitlines(keepends=True)
            start_line = token.map[0]
            last_fence_idx = -1

            for j in range(len(lines) - 1, start_line, -1):
                line_stripped = lines[j].strip()
                if line_stripped.startswith('```') or line_stripped.startswith('~~~'):
                    last_fence_idx = j
                    break

            if last_fence_idx > start_line:
                candidate_content = "".join(lines[start_line + 1: last_fence_idx])

        # 2. Extract Metadata (Type)
        yaml_pattern = re.compile(
            r'^---\s+.*?(?:type|Type)\s*:\s*["\']?(\w+)["\']?.*?---',
            re.DOTALL | re.MULTILINE
        )

        artifact_type = "Output"
        yaml_match = yaml_pattern.search(candidate_content)
        if yaml_match:
            artifact_type = yaml_match.group(1)

        # 3. Generate Filename (H1 Header)
        filename = ""
        title_match = re.search(r'^#{1,2}\s+(.+)$', candidate_content, re.MULTILINE)
        if title_match:
            raw_title = title_match.group(1).strip()
            clean_title = raw_title.lower().replace(" ", "-")
            clean_title = re.sub(r'[^a-z0-9-]', '', clean_title)
            filename = f"{clean_title}.md"
        else:
            ts = datetime.datetime.now().strftime("%H%M%S")
            filename = f"artifact-{ts}.md"

        # 4. Map Directory
        lookup_key = artifact_type.capitalize()
        subdir = self.DIR_MAP.get(lookup_key, "output")
        directory = f"{self.NAMESPACE}/{subdir}"

        return Artifact(
            content=candidate_content,
            filename=filename,
            directory=directory,
            type=artifact_type
        )


class DiffHandler(ArtifactHandler):
    """
    Handles Unified Diff blocks tagged as 'diff' or 'patch'.
    Performs sanitization and extracts target filenames from headers.
    """

    def can_handle(self, token: Token) -> bool:
        """
        Recognizes fence blocks with info string 'diff' or 'patch'.
        """
        if token.type != 'fence':
            return False

        lang = token.info.strip().lower()
        return lang in ['diff', 'patch']

    def extract(self, token: Token, full_text: str) -> Artifact:
        """
        Sanitizes diff content and generates filename from '+++ b/' header.
        """
        content = token.content

        # 1. Sanitize
        try:
            from vybz.tools.diff_utils import DiffSanitizer
            content = DiffSanitizer.sanitize(content)
        except ImportError:
            pass  # Graceful degradation

        # 2. Extract Filename
        filename = f"patch-{datetime.datetime.now().strftime('%H%M%S')}.diff"
        # Regex looks for the standard unified diff header: +++ b/path/to/file
        # We check the sanitized content first, then fallback to raw token content
        match = re.search(r'^\+\+\+ b/(.+)$', content, re.MULTILINE)
        if not match:
            match = re.search(r'^\+\+\+ b/(.+)$', token.content, re.MULTILINE)

        if match:
            raw_path = match.group(1).strip()
            filename = raw_path.replace("/", "-") + ".diff"

        return Artifact(
            content=content,
            filename=filename,
            directory=".vybz/output",
            type="Diff"
        )


class CodeFileHandler(ArtifactHandler):
    """
    Handles generic code blocks annotated with a filename.
    Supports two conventions:
    1. Comment annotation: # filename: src/utils.py
    2. Docstring annotation: \"\"\"\nsrc/utils.py\n\"\"\"
    """
    # Regex to capture: # filename: src/foo.py
    # Supports # (Python/Shell), // (JS/C), -- (Lua/SQL)
    FILENAME_PATTERN = re.compile(
        r'(?:^|\n)\s*(?:#|//|--)\s*(?:filename|file):\s*(.+?)\s*(?:\n|$)',
        re.IGNORECASE | re.MULTILINE
    )

    # Regex to capture path at the start of a docstring
    # Matches: start of string -> whitespace -> triple quote -> newline -> whitespace -> (PATH) -> whitespace/newline
    DOCSTRING_PATTERN = re.compile(
        r'^\s*(?:"""|\'\'\')\s*\n\s*([^\s]+\.[a-zA-Z0-9]+)',
        re.MULTILINE
    )

    def can_handle(self, token: Token) -> bool:
        if token.type != 'fence':
            return False
        # Avoid stealing Diffs or Docs
        if token.info.strip().lower() in ['diff', 'patch']:
            return False
        if token.content.strip().startswith('---'):
            return False

        # Check for explicit filename comment
        if self.FILENAME_PATTERN.search(token.content):
            return True

        # Check for docstring convention
        if self.DOCSTRING_PATTERN.search(token.content):
            return True

        return False

    def extract(self, token: Token, full_text: str) -> Artifact:
        # Try finding explicit comment first
        filename_match = self.FILENAME_PATTERN.search(token.content)

        # If no comment, try docstring
        docstring_match = None
        if not filename_match:
            docstring_match = self.DOCSTRING_PATTERN.search(token.content)

        match = filename_match or docstring_match

        # Default fallback
        ts = datetime.datetime.now().strftime("%H%M%S")
        filename = f"{ts}-snippet.txt"
        directory = ".vybz/output"
        content = token.content

        if match:
            raw_path = match.group(1).strip()
            # Handle potential quotes around filename
            raw_path = raw_path.strip('"\'')

            p = Path(raw_path)
            filename = p.name
            directory = str(p.parent)

            if filename_match:
                # Strip the metadata comment line to make shebangs valid
                start, end = filename_match.span()
                content = content[:start] + content[end:]
                content = content.lstrip()

        return Artifact(
            content=content,
            filename=filename,
            directory=directory,
            type="Code"
        )



class ArtifactProcessor:
    """
    Stateless service for extracting and saving artifacts.
    """

    def __init__(self) -> None:
        self.md = MarkdownIt()
        self.handlers: List[ArtifactHandler] = [
            DocumentHandler(),
            DiffHandler(),
            CodeFileHandler()
        ]

    def parse(self, text: str) -> List[Artifact]:
        """
        Parses the text using registered handlers to extract one or more
        artifacts from the token stream.

        Args:
            text: The raw response string from the Agent.

        Returns:
            List[Artifact]: A list of populated domain objects.
        """
        # 1. Parse into Tokens
        tokens = self.md.parse(text)
        artifacts: List[Artifact] = []

        for token in tokens:
            for handler in self.handlers:
                if handler.can_handle(token):
                    artifacts.append(handler.extract(token, text))
                    break

        # 2. Raw Text Rescue
        # If no artifacts found, check if the raw text itself is a Document (forgot fences)
        if not artifacts:
            # Create a synthetic token representing the entire text
            synthetic_token = Token("fence", "code", 0)
            synthetic_token.content = text
            synthetic_token.info = ""
            synthetic_token.map = None # No mapping for raw text

            for handler in self.handlers:
                if handler.can_handle(synthetic_token):
                    artifacts.append(handler.extract(synthetic_token, text))
                    break

        # 3. Fallback: If still no structured artifacts, treat whole text as generic Output
        if not artifacts:
            ts = datetime.datetime.now().strftime("%H%M%S")
            return [Artifact(
                content=text,
                filename=f"artifact-{ts}.md",
                directory=".vybz/output",
                type="Output"
            )]

        return artifacts

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


