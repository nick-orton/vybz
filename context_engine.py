"""
context_engine.py

A robust, read-only filesystem snapshot engine designed for LLM context generation.
Handles .gitignore parsing, binary file exclusion, and Markdown serialization.
"""

import os
import pathspec
from pathlib import Path
from typing import Generator, List, Optional, Tuple, Set

# Type alias for clarity
FileNode = Tuple[Path, str]  # (Absolute Path, Relative Path String)


class CodeBase:
    """
    Represents a read-only snapshot of a local source directory.

    Attributes:
        root_path (Path): The absolute POSIX path to the project root.
        ignore_spec (pathspec.PathSpec): Compiled gitignore patterns.
    """

    def __init__(self, root_path: str | Path):
        """
        Initialize the CodeBase snapshot.

        Args:
            root_path: The directory to traverse.

        Raises:
            FileNotFoundError: If the root_path does not exist.
            NotADirectoryError: If root_path is not a directory.
        """
        self.root_path = Path(root_path).resolve()

        if not self.root_path.exists():
            raise FileNotFoundError(f"Root path not found: {self.root_path}")
        if not self.root_path.is_dir():
            raise NotADirectoryError(f"Root path is not a directory: {self.root_path}")

        self.ignore_spec = self._load_gitignore()

    def _load_gitignore(self) -> pathspec.PathSpec:
        """
        Loads .gitignore from the root directory if present.
        Always explicitly excludes .git directory.
        """
        patterns = [".git/"]  # Default unconditional ignores
        gitignore_path = self.root_path / ".gitignore"

        if gitignore_path.exists() and gitignore_path.is_file():
            try:
                with open(gitignore_path, "r", encoding="utf-8") as f:
                    patterns.extend(f.readlines())
            except UnicodeDecodeError:
                # If .gitignore is corrupt/binary, we fallback to default ignores
                pass

        return pathspec.PathSpec.from_lines("gitwildmatch", patterns)

    def _is_binary(self, file_path: Path) -> bool:
        """
        Heuristic binary file detection.
        Reads the first 1024 bytes and attempts UTF-8 decoding.
        """
        try:
            with open(file_path, "rb") as f:
                chunk = f.read(1024)
                if b"\0" in chunk:  # Null byte check is a strong binary indicator
                    return True
                chunk.decode("utf-8")
        except (UnicodeDecodeError, PermissionError, OSError):
            return True
        return False

    def _should_ignore(self, path: Path) -> bool:
        """
        Check if a path should be ignored based on gitignore spec.
        """
        # Calculate path relative to root for matching
        try:
            rel_path = path.relative_to(self.root_path)
            # pathspec expects string paths, specific to gitignore format (forward slashes)
            return self.ignore_spec.match_file(str(rel_path))
        except ValueError:
            # Path is not relative to root
            return True

    def _walk_tree(
        self, directory: Path, prefix: str = ""
    ) -> Generator[Tuple[str, List[FileNode]], None, None]:
        """
        Recursive generator that yields tree lines and collects valid files.

        Yields:
            Tuple[str, List[FileNode]]: (Tree View Line, List of valid files in this node)
        """
        # 1. Collect all entries, filter by ignore spec
        try:
            entries = list(directory.iterdir())
        except (PermissionError, OSError):
            yield (f"{prefix}[ACCESS DENIED]", [])
            return

        # Sort: Directories first, then files (alphabetical)
        entries.sort(key=lambda x: (not x.is_dir(), x.name.lower()))

        # Filter entries based on ignore spec
        valid_entries = [e for e in entries if not self._should_ignore(e)]

        count = len(valid_entries)
        for index, entry in enumerate(valid_entries):
            connector = "└── " if index == count - 1 else "├── "

            # Yield the tree line for this entry
            yield (f"{prefix}{connector}{entry.name}", [])

            if entry.is_dir():
                # Prepare prefix for children
                extension = "    " if index == count - 1 else "│   "
                # Recurse
                yield from self._walk_tree(entry, prefix + extension)
            else:
                # It's a file, we want to capture it for content rendering later
                rel_path = str(entry.relative_to(self.root_path))
                yield ("", [(entry, rel_path)])

    def render(self) -> str:
        """
        Generates the full Markdown representation of the codebase.

        Returns:
            str: The formatted Markdown string containing Tree and File Contents.
        """
        tree_lines: List[str] = []
        file_manifest: List[FileNode] = []

        # Header
        tree_lines.append("# CodeBase")
        tree_lines.append("")
        tree_lines.append("## Structure")
        tree_lines.append(".")

        # Perform Traversal
        for line, files in self._walk_tree(self.root_path):
            if line:
                tree_lines.append(line)
            if files:
                file_manifest.extend(files)

        # Build Output
        output_parts = ["\n".join(tree_lines), "", "## Files"]

        for abs_path, rel_path in file_manifest:
            output_parts.append(f"### {rel_path}")

            if self._is_binary(abs_path):
                output_parts.append("*[Binary File - Content Excluded]*")
                output_parts.append("")
                continue

            # Determine language for markdown fence
            ext = abs_path.suffix.lstrip(".") or "text"

            try:
                with open(abs_path, "r", encoding="utf-8") as f:
                    content = f.read()

                output_parts.append(f"```{ext}")
                output_parts.append(content)
                output_parts.append("```")
            except Exception as e:
                output_parts.append(f"*[Error reading file: {str(e)}]*")

            output_parts.append("")

        return "\n".join(output_parts)


