"""
src/vybz/commands/registry.py

Handles registration and lookup of command objects.
Aggregates commands from both core (Session) and system (Local) modules.
"""

from typing import Dict, List, Optional
from vybz.commands.base import Command

# Agent & Session Commands
from vybz.commands.core import (
    AgentCommand,
    LoadCommand,
    UpdateCommand,
    SkillsCommand,
    UplevelCommand,
    DownlevelCommand
)

# Local System & UI Commands
from vybz.commands.system import (
    ExitCommand,
    ClearCommand,
    HelpCommand,
    SaveCommand,
    SetModeCommand,
    ThemeCommand
)

class CommandRegistry:
    """
    Central registry for REPL commands.
    Shields the REPL loop from the implementation details of where commands live.
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
        return list({cmd for cmd in self._commands.values()})

    def initialize(self) -> None:
        """Registers all available commands from both modules."""
        # Core / Session
        self.register(AgentCommand())
        self.register(UpdateCommand())
        self.register(LoadCommand())
        self.register(SkillsCommand())
        self.register(UplevelCommand())
        self.register(DownlevelCommand())

        # System / UI
        self.register(ExitCommand())
        self.register(ClearCommand())
        self.register(HelpCommand())
        self.register(SaveCommand())
        self.register(SetModeCommand())
        self.register(ThemeCommand())
