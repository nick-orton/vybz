"""
ui.py

Handles the visual presentation of the Vybz CLI using the 'rich' library.
Implements a "Cyber/Oceanic" theme for terminal output while ensuring
separation between displayed content and logged content.
"""

from datetime import datetime
from rich.console import Console
from rich.theme import Theme
from rich.panel import Panel
from rich.table import Table
from rich.box import ROUNDED
from rich.markup import escape

# -----------------------------------------------------------------------------
# Theme Configuration
# -----------------------------------------------------------------------------

# "Cyber/Oceanic" Palette
VYBZ_THEME = Theme({
    "info": "cyan",
    "warning": "bold yellow",
    "error": "bold red",
    "success": "bold spring_green1",
    "header.label": "bold cyan",
    "header.value": "spring_green1",
    "content": "white",
    "panel.border": "blue",
    "session.border": "spring_green1",
    "timestamp": "dim white",
})

# Global Console Instance
# force_terminal=None allows rich to auto-detect if we are piping output
console = Console(theme=VYBZ_THEME)

# Standard Error Console (for System Logs/Status)
# We use a separate console for logs so users can pipe stdout (generated code)
# to a file without capturing "Spinning up..." messages.
error_console = Console(theme=VYBZ_THEME, stderr=True)

# -----------------------------------------------------------------------------
# Rendering Functions
# -----------------------------------------------------------------------------

def render_header(
    agent_name: str,
    model_id: str,
    intent: str,
    timestamp: str | None = None
) -> None:
    """
    Renders a styled metadata panel to the console for one-shot tasks.

    Args:
        agent_name: Identity of the agent.
        model_id: Gemini model identifier.
        intent: The user's prompt/intent.
        timestamp: Optional ISO timestamp string.
    """
    if not timestamp:
        timestamp = datetime.now().strftime("%H:%M:%S")

    # Create an internal table for alignment within the panel
    grid = Table.grid(padding=(0, 2))
    grid.add_column(style="header.label", justify="right")
    grid.add_column(style="header.value", justify="left")

    grid.add_row("TIMESTAMP", timestamp)
    grid.add_row("MODEL", model_id)
    grid.add_row("AGENT", agent_name)
    grid.add_row("INTENT", intent)

    panel = Panel(
        grid,
        title="[bold blue]VYBZ KARTEL[/]",
        subtitle=f"[timestamp]{timestamp}[/]",
        border_style="panel.border",
        box=ROUNDED,
        padding=(1, 2),
    )

    console.print(panel)
    console.print()  # Spacer

def render_session_header(
    agent_name: str,
    model_id: str,
    codebase_root: str | None = None
) -> None:
    """
    Renders a distinct styled header for Interactive Sessions.

    Args:
        agent_name: Identity of the agent.
        model_id: Gemini model identifier.
        codebase_root: String representation of context root (optional).
    """
    timestamp = datetime.now().strftime("%H:%M:%S")
    context_str = codebase_root if codebase_root else "[dim]Greenfield (No Context)[/]"

    # Create an internal table for alignment
    grid = Table.grid(padding=(0, 2))
    grid.add_column(style="header.label", justify="right")
    grid.add_column(style="header.value", justify="left")

    grid.add_row("AGENT", agent_name)
    grid.add_row("MODEL", model_id)
    grid.add_row("CONTEXT", context_str)

    panel = Panel(
        grid,
        title="[bold spring_green1]VYBZ KARTEL // INTERACTIVE SESSION[/]",
        subtitle="[dim]Commands: /exit, /clear, /help | Submit: Alt+Enter[/]",
        border_style="session.border",
        box=ROUNDED,
        padding=(1, 2),
    )

    console.print(panel)
    console.print()  # Spacer




def stream_chunk(text: str) -> None:
    """
    Prints a chunk of text to stdout using the theme's content color.

    Args:
        text: The raw text chunk from the LLM stream.
    """
    # We use end="" to ensure the stream flows naturally without extra newlines
    console.print(text, style="content", end="", highlight=False, markup=False)


# -----------------------------------------------------------------------------
# System Logging (Targeting Stderr)
# -----------------------------------------------------------------------------

def print_error(message: str) -> None:
    """Prints a styled error message."""
    error_console.print(f"[error]ERROR:[/error] {escape(message)}")

def print_warning(message: str) -> None:
    """Prints a styled warning message to stderr."""
    error_console.print(f"[warning]WARNING:[/warning] {escape(message)}")

def print_system(message: str) -> None:
    """Prints a system/info message."""
    error_console.print(f"[info]>> {escape(message)}[/info]")

def print_success(message: str) -> None:
    """Prints a success message to stderr."""
    error_console.print(f"[success]✓[/success] {escape(message)}")
