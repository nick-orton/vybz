"""
src/vybz/assets/loader.py

Stateless service for loading static text assets.
Decouples resource management from the REPL session logic.
"""

from pathlib import Path


class AssetLoader:
    """
    Manages access to static assets within the vybz package.
    """

    @staticmethod
    def _get_assets_dir() -> Path:
        """Resolves the absolute path to the assets directory."""
        return Path(__file__).parent

    @classmethod
    def load_text(cls, filename: str) -> str:
        """
        Robustly loads text content from the assets directory.

        Args:
            filename: The name of the file to load (e.g., 'repl_help.txt').

        Returns:
            str: The content of the file, or an error message if not found.
        """
        try:
            asset_path = cls._get_assets_dir() / filename
            
            if not asset_path.exists():
                return f"Asset not found: {filename}"
            
            return asset_path.read_text(encoding="utf-8")
            
        except Exception as e:
            return f"Failed to load asset '{filename}': {e}"
