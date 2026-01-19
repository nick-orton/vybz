"""
theme.py

Handles the loading and management of UI color themes.
Decouples visual aesthetics from the core UI logic by parsing TOML configurations.
"""

import tomllib
from pathlib import Path
from typing import Dict, List, Final

from rich.theme import Theme

# The hardcoded "Cyber/Oceanic" fallback ensures the app works out-of-the-box
DEFAULT_STYLES: Final[Dict[str, str]] = {
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
}


class ThemeLoader:
    """
    Stateless service responsible for discovering and parsing theme configurations.
    """

    @staticmethod
    def _get_config_path() -> Path:
        """Returns the path of the packaged themes configuration file."""
        # Fix: Resolve relative to the installed package, not CWD
        return Path(__file__).parent / "themes.toml"

    @classmethod
    def load(cls, name: str) -> Theme:
        """
        Loads a specific theme by name from themes.toml and returns a Rich Theme object.

        Args:
            name: The section key in the TOML file (e.g., 'matrix').

        Returns:
            rich.theme.Theme: The configured theme object ready for Console use.

        Raises:
            ValueError: If the theme name is not found in the configuration.
        """
        config_path = cls._get_config_path()
        styles = {}

        # 1. Load from file if exists
        if config_path.exists():
            try:
                with open(config_path, "rb") as f:
                    data = tomllib.load(f)

                if name in data:
                    styles = data[name]
            except Exception:
                # If parsing fails, we fall through to defaults if name is default
                pass

        # 2. Fallback Logic
        if not styles:
            if name == "default":
                styles = DEFAULT_STYLES
            else:
                available = cls.list_available()
                raise ValueError(
                    f"Theme '{name}' not found. Available: {', '.join(available)}"
                )

        # 3. Construction
        return Theme(styles)

    @classmethod
    def list_available(cls) -> List[str]:
        """
        Returns a list of available theme names found in themes.toml,
        plus the built-in 'default'.

        Returns:
            List[str]: A list of theme keys.
        """
        keys = {"default"}
        config_path = cls._get_config_path()

        if config_path.exists():
            try:
                with open(config_path, "rb") as f:
                    data = tomllib.load(f)
                    keys.update(data.keys())
            except Exception:
                pass

        return sorted(list(keys))
