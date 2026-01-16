"""
config.py

Handles the loading of user configuration from dotfiles.
Establishes a persistence layer for user preferences like Theme and Input Mode.
"""

import os
import tomllib
from pathlib import Path
from typing import Dict, Any, List, Set, Final

from vybz import ui

# Allowed configuration keys to prevent polluting the argparse namespace
ALLOWED_KEYS: Final[Set[str]] = {
    "theme",
    "mode",
    "model",
    "log_file",
    "agent",
    "codebase"
}


class ConfigLoader:
    """
    Stateless service responsible for discovering, parsing, and sanitizing
    user configuration files.
    """

    @staticmethod
    def _get_search_paths() -> List[Path]:
        """
        Returns the ordered list of configuration file paths to check.

        Precedence:
            1. $HOME/.vybzrc
            2. $XDG_CONFIG_HOME/vybz.config (defaults to ~/.config/vybz.config)

        Returns:
            List[Path]: Potential configuration file paths.
        """
        home = Path.home()

        # XDG Base Directory specification
        xdg_config_home = os.getenv("XDG_CONFIG_HOME")
        if xdg_config_home:
            xdg_root = Path(xdg_config_home)
        else:
            xdg_root = home / ".config"

        return [
            home / ".vybzrc",
            xdg_root / "vybz.config"
        ]

    @classmethod
    def load(cls) -> Dict[str, Any]:
        """
        Discovers and loads the user configuration file.

        Logic:
            1. Iterates through search paths.
            2. Stops at the first file that exists.
            3. Parses TOML content.
            4. Filters keys against ALLOWED_KEYS.

        Returns:
            Dict[str, Any]: A dictionary of valid configuration options.
                            Returns empty dict if no file found or parsing fails.
        """
        search_paths = cls._get_search_paths()
        config_data: Dict[str, Any] = {}

        for path in search_paths:
            if path.exists() and path.is_file():
                try:
                    with open(path, "rb") as f:
                        raw_data = tomllib.load(f)

                    # Sanitization: Only allow known keys to prevent namespace pollution
                    for key, value in raw_data.items():
                        if key in ALLOWED_KEYS:
                            config_data[key] = value

                    # Stop at the first valid file found
                    break

                except Exception as e:
                    # Fail Open strategy: Warn user but proceed with defaults
                    ui.print_warning(f"Failed to parse config at {path}: {e}")
                    return {}

        return config_data
