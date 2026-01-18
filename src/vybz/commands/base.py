"""
src/vybz/commands/base.py

Defines the abstract base class for REPL commands.
"""

from abc import ABC, abstractmethod
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from vybz.repl import ReplSession


class Command(ABC):
    """
    Abstract base class for all REPL commands.
    """
    name: str = ""
    description: str = ""
    aliases: List[str] = []

    @abstractmethod
    def execute(self, session: "ReplSession", args: List[str]) -> bool:
        """
        Executes the command logic.

        Args:
            session: The active ReplSession instance (context).
            args: List of arguments passed to the command.

        Returns:
            bool: True if the REPL should refresh/continue, False otherwise.
                  Raises EOFError to exit the application.
        """
        pass

