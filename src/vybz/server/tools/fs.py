"""
src/vybz/server/tools/fs.py

FileSystem tools for Agentic RAG.
Wraps CodeBase logic to provide gitignore-aware file exploration.
Hardened against path injection/traversal via strict resolution checks.
"""

from pathlib import Path
from typing import Optional
from vybz.shared.codebase import CodeBase


class FileSystemTools:
    """
    Encapsulates filesystem operations bound to a specific root.
    """

    def __init__(self, root_path: str | Path):
        # Resolve the root to an absolute path immediately
        self.root = Path(root_path).resolve()
        # Instantiate CodeBase just to leverage its ignore logic
        self.codebase = CodeBase(self.root)

    def _secure_path(self, rel_path: str) -> Path:
        """
        Resolves and validates that a path is safely within the root directory.
        
        Args:
            rel_path: The user-provided relative path.
            
        Returns:
            Path: The resolved absolute path.
            
        Raises:
            PermissionError: If the path is outside the root.
            FileNotFoundError: If the path does not exist.
        """
        # Join and resolve to handle .. and symlinks
        target = (self.root / rel_path).resolve()

        # Check if the resolved path is still under root.
        # .is_relative_to() is safer than string.startswith()
        try:
            target.relative_to(self.root)
        except ValueError:
            raise PermissionError(f"Access denied: {rel_path} is outside root directory.")

        if not target.exists():
            raise FileNotFoundError(f"Path does not exist: {rel_path}")

        return target

    def list_files(self, rel_path: str = ".") -> str:
        """
        Lists files and directories in a given path, respecting .gitignore.
        
        Args:
            rel_path: The path relative to the project root (default: ".").
            
        Returns:
            str: A tree-like string representation of the directory.
        """
        try:
            target = self._secure_path(rel_path)
        except (PermissionError, FileNotFoundError) as e:
            return f"Error: {e}"
        except Exception as e:
            return f"Error: Invalid path '{rel_path}': {e}"

        # Leverage the existing walk_tree logic from CodeBase
        output = [f"Listing for {rel_path}:"]
        for line, _ in self.codebase._walk_tree(target):
            if line:
                output.append(line)
        
        return "\n".join(output)

    def read_file(self, rel_path: str) -> str:
        """
        Reads the content of a specific file.
        
        Args:
            rel_path: The path to the file relative to the project root.
            
        Returns:
            str: The file content wrapped in markdown code blocks, or an error.
        """
        try:
            target = self._secure_path(rel_path)
            
            if not target.is_file():
                return f"Error: {rel_path} is not a file."

            if self.codebase._is_binary(target):
                return f"Error: {rel_path} is a binary file and cannot be read as text."

            content = target.read_text(encoding="utf-8")
            ext = target.suffix.lstrip(".") or "text"
            return f"### {rel_path}\n```{ext}\n{content}\n```"
            
        except (PermissionError, FileNotFoundError) as e:
            return f"Error: {e}"
        except Exception as e:
            return f"Error reading {rel_path}: {str(e)}"

