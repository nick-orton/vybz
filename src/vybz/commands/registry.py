"""
src/vybz/commands/registry.py

Handles registration and lookup of command objects.
"""

from typing import Dict, List, Optional
from vybz.commands.base import Command
from vybz.commands.core import (
    AgentCommand,
    ClearCommand,
    ExitCommand,
    HelpCommand,
    SaveCommand,
    LoadCommand,
    SetModeCommand,
    ThemeCommand,
    UpdateCommand
)

class CommandRegistry:
    """
    Central registry for REPL commands.
    """

    def __init__(self) -> None:
        self._commands: Dict[str, Command] = {}

    def register(self, command: Command) -> None:
        """
        Registers a command and its aliases.
        """
        self._commands[command.name] = command
        for alias in command.aliases:
            self._commands[alias] = command

    def get_command(self, name: str) -> Optional[Command]:
        """
        Retrieves a command by name or alias.
        """
        return self._commands.get(name.lower())

    def list_commands(self) -> List[Command]:
        """
        Returns a list of unique command objects.
        """
        # Dedup by object identity
        return list({cmd for cmd in self._commands.values()})

    def initialize(self) -> None:
        """Registers all available commands."""
        self.register(AgentCommand())
        self.register(ClearCommand())
        self.register(ExitCommand())
        self.register(HelpCommand())
        self.register(SaveCommand())
        self.register(LoadCommand())
        self.register(SetModeCommand())
        self.register(ThemeCommand())
        self.register(UpdateCommand())

