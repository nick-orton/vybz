"""
ui.py

Handles the visual presentation of the Vybz CLI using the 'rich' library.
Manages global Console instances and supports dynamic theming via ThemeLoader.
"""

from typing import Any
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.box import ROUNDED
from rich.markup import escape
from prompt_toolkit.styles import Style as PtkStyle

from vybz.theme import ThemeLoader

# -----------------------------------------------------------------------------
# Global Console Instances
# -----------------------------------------------------------------------------

# Initialize with default theme immediately
# ThemeLoader handles fallback to internal defaults if config is missing
_initial_theme = ThemeLoader.load("default")

# force_terminal=None allows rich to auto-detect if we are piping output
console = Console(theme=_initial_theme)

# Standard Error Console (for System Logs/Status)
# We use a separate console for logs so users can pipe stdout (generated code)
# to a file without capturing "Spinning up..." messages.
error_console = Console(theme=_initial_theme, stderr=True)


def set_theme(theme_name: str) -> bool:
    """
    Hot-swaps the active color theme for the UI.

    Args:
        theme_name: The key of the theme in themes.toml (e.g., 'matrix').

    Returns:
        True if successful, False if theme not found.
    """
    global console, error_console

    try:
        new_theme = ThemeLoader.load(theme_name)
        
        # Re-instantiate global consoles with new theme
        console = Console(theme=new_theme)
        error_console = Console(theme=new_theme, stderr=True)
        return True

    except ValueError as e:
        # Report failure using the current error console
        # The exception message from ThemeLoader already lists available themes
        print_error(str(e))
        return False

# -----------------------------------------------------------------------------
# Style Bridging (Rich -> Prompt Toolkit)
# -----------------------------------------------------------------------------

def _resolve_style_color(rich_style: Any, default: str) -> str:
    """
    Safely extracts a color from a Rich style object for Prompt Toolkit compatibility.
    Converts named colors (like 'spring_green1') to Hex to avoid format errors.
    """
    if not rich_style or not rich_style.color:
        return default

    try:
        # Attempt to retrieve the Hex code from the Rich color triplet.
        # This handles standard ANSI, 256-color, and TrueColor definitions.
        # rich.color.Color objects generally have a .triplet property.
        if hasattr(rich_style.color, 'triplet') and rich_style.color.triplet:
            return rich_style.color.triplet.hex

        # 2. If no triplet, check if it's a safe ANSI name supported by prompt_toolkit.
        # Common names: 'green', 'red', 'cyan', 'black', 'white', 'yellow', 'magenta', 'blue'
        # (and their 'bright' variants sometimes, but basic is safer).
        name = str(rich_style.color.name).lower()
        safe_ansi = {
            'black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white',
            'bright_black', 'bright_red', 'bright_green', 'bright_yellow',
            'bright_blue', 'bright_magenta', 'bright_cyan', 'bright_white'
        }

        if name in safe_ansi:
            return name

        # 3. If it's a weird name (like 'spring_green1') and we couldn't get a Hex,
        # fallback to default to prevent crash.
        return default
    except Exception:
        # If conversion fails, return the default to prevent crash
        return default

def get_ptk_style() -> PtkStyle:
    """
    Dynamically derives Prompt Toolkit styles from the active Rich theme.
    Used by the REPL to match the prompt color to the output color.
    """
    # Get Rich styles from the global console
    s_info = console.get_style("info")
    s_success = console.get_style("success")
    s_time = console.get_style("timestamp")

    # Extract colors safely using helper to convert extended names to Hex
    c_agent = _resolve_style_color(s_info, "cyan")
    c_sep = _resolve_style_color(s_success, "green")
    c_meta = _resolve_style_color(s_time, "gray")

    return PtkStyle.from_dict({
        "agent": f"bold {c_agent}",
        "separator": f"bold {c_sep}",
        "meta": c_meta,
    })

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
