"""
theme.py

Handles the loading and management of UI color themes.
Decouples visual aesthetics from the core UI logic by parsing TOML configurations.
"""

import os
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
    def _get_search_paths() -> List[Path]:
        """Returns an ordered list of config paths (User first, then Packaged)."""
        home = Path.home()
        xdg_config_home = os.getenv("XDG_CONFIG_HOME")
        if xdg_config_home:
            xdg_root = Path(xdg_config_home)
        else:
            xdg_root = home / ".config"

        return [
            xdg_root / "vybz" / "themes.toml",
            # theme.py is in src/vybz/client/, themes.toml is in src/vybz/
            Path(__file__).parent.parent / "themes.toml"
        ]

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
        all_themes = cls._gather_styles()
        styles = all_themes.get(name)

        # Fallback Logic
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
    def _gather_styles(cls) -> Dict[str, Dict[str, str]]:
        """Aggregates styles from all discovered files. User config overrides package."""
        aggregated: Dict[str, Dict[str, str]] = {}

        # Reverse search paths so higher precedence (user) is applied last in .update()
        for path in reversed(cls._get_search_paths()):
            if path.exists() and path.is_file():
                try:
                    with open(path, "rb") as f:
                        data = tomllib.load(f)
                        aggregated.update(data)
                except Exception:
                    continue
        return aggregated

    @classmethod
    def list_available(cls) -> List[str]:
        """
        Returns a list of available theme names found in configuration files,
        plus the built-in 'default'.

        Returns:
            List[str]: A list of theme keys.
        """
        keys = {"default"}
        keys.update(cls._gather_styles().keys())
        return sorted(list(keys))

