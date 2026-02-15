"""
src/vybz/server/tools/fs.py

FileSystem tools for Agentic RAG.
Wraps CodeBase logic to provide gitignore-aware file exploration.
"""

from pathlib import Path
from typing import Optional
from vybz.shared.codebase import CodeBase

class FileSystemTools:
    """
    Encapsulates filesystem operations bound to a specific root.
    """

    def __init__(self, root_path: str | Path):
        self.root = Path(root_path).resolve()
        # Instantiate CodeBase just to leverage its ignore logic
        self.codebase = CodeBase(self.root)

    def list_files(self, rel_path: str = ".") -> str:
        """
        Lists files and directories in a given path, respecting .gitignore.
        
        Args:
            rel_path: The path relative to the project root (default: ".").
            
        Returns:
            str: A tree-like string representation of the directory.
        """
        target = (self.root / rel_path).resolve()
        
        # Security: Prevent Directory Traversal
        if not str(target).startswith(str(self.root)):
            return f"Error: Access denied to {rel_path}. Path is outside root."

        if not target.exists():
            return f"Error: Path {rel_path} does not exist."

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
        target = (self.root / rel_path).resolve()

        # Security: Prevent Directory Traversal
        if not str(target).startswith(str(self.root)):
            return f"Error: Access denied. Path {rel_path} is outside root."

        if not target.is_file():
            return f"Error: {rel_path} is not a file or does not exist."

        if self.codebase._is_binary(target):
            return f"Error: {rel_path} is a binary file and cannot be read as text."

        try:
            content = target.read_text(encoding="utf-8")
            ext = target.suffix.lstrip(".") or "text"
            return f"### {rel_path}\n```{ext}\n{content}\n```"
        except Exception as e:
            return f"Error reading {rel_path}: {str(e)}"
