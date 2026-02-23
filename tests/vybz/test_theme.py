"""
tests/vybz/test_theme.py

Unit tests for the ThemeLoader service.
Validates TOML parsing, fallback logic, and Rich integration logic
as specified in 'designs/theming-the-repl-specification.md'.
"""
import pytest
from unittest.mock import patch, MagicMock, mock_open
from rich.theme import Theme
from vybz.client.theme import ThemeLoader, DEFAULT_STYLES

class TestThemeLoader:
    """
    Tests for the ThemeLoader service.
    """

    @pytest.fixture
    def mock_tomllib(self):
        """Mock tomllib to avoid actual parsing, focusing on logic flow."""
        with patch("vybz.client.theme.tomllib") as mock_toml:
            yield mock_toml

    @pytest.fixture
    def mock_path_exists(self):
        """Mock Path.exists to control file discovery."""
        with patch("vybz.client.theme.Path.exists") as mock_exists:
            yield mock_exists

    def test_load_default_fallback_no_file(self, mock_path_exists):
        """
        Happy Path: Verify that requesting 'default' returns the hardcoded
        DEFAULT_STYLES when the configuration file is missing.
        """
        # Arrange
        mock_path_exists.return_value = False

        # Act
        theme = ThemeLoader.load("default")

        # Assert
        assert isinstance(theme, Theme)
        # Check a known key from DEFAULT_STYLES (e.g., 'info')
        assert theme.styles["info"].color.name == DEFAULT_STYLES["info"]

    def test_load_from_toml_success(self, mock_path_exists, mock_tomllib):
        """
        Happy Path: Verify loading a custom theme from a valid TOML source.
        """
        # Arrange
        mock_path_exists.return_value = True
        mock_tomllib.load.return_value = {
            "matrix": {
                "info": "green",
                "warning": "bold yellow"
            }
        }

        # Act
        with patch("builtins.open", mock_open()):
            theme = ThemeLoader.load("matrix")

        # Assert
        assert isinstance(theme, Theme)
        assert theme.styles["info"].color.name == "green"
        assert theme.styles["warning"].bold == True
        assert theme.styles["warning"].color.name == "yellow"

    def test_load_unknown_theme_raises_error(self, mock_path_exists, mock_tomllib):
        """
        Sad Path: Verify ValueError is raised when requesting a non-existent theme,
        and that the error message helps the user.
        """
        # Arrange
        mock_path_exists.return_value = True
        mock_tomllib.load.return_value = {
            "matrix": {}
        }

        # Act & Assert
        with patch("builtins.open", mock_open()):
            with pytest.raises(ValueError) as exc:
                ThemeLoader.load("dracula")

        msg = str(exc.value)
        assert "Theme 'dracula' not found" in msg
        # Ensure it lists available options
        assert "matrix" in msg
        assert "default" in msg

    def test_list_available(self, mock_path_exists, mock_tomllib):
        """
        Verify listing available themes includes 'default' plus keys from the file.
        """
        # Arrange
        mock_path_exists.return_value = True
        mock_tomllib.load.return_value = {
            "matrix": {},
            "dracula": {}
        }

        # Act
        with patch("builtins.open", mock_open()):
            available = ThemeLoader.list_available()

        # Assert
        assert "default" in available
        assert "matrix" in available
        assert "dracula" in available
        assert len(available) == 3

    def test_load_malformed_toml_fallback(self, mock_path_exists, mock_tomllib):
        """
        Sad Path: Verify that if TOML parsing fails (Corrupt file),
        we gracefully degrade to the default theme if 'default' was requested,
        or handle the error appropriately.
        """
        # Arrange
        mock_path_exists.return_value = True
        # Simulate a TOML decode error
        mock_tomllib.load.side_effect = Exception("TOML Decode Error")

        # Act
        with patch("builtins.open", mock_open()):
            # If we request default, it should ignore the file error and return default
            theme = ThemeLoader.load("default")

        # Assert
        assert theme.styles["info"].color.name == DEFAULT_STYLES["info"]

    def test_load_malformed_toml_custom_request(self, mock_path_exists, mock_tomllib):
        """
        Sad Path: If TOML is corrupt and we ask for a custom theme,
        it should raise ValueError (because the theme can't be found).
        """
        # Arrange
        mock_path_exists.return_value = True
        mock_tomllib.load.side_effect = Exception("TOML Decode Error")

        # Act & Assert
        with patch("builtins.open", mock_open()):
            with pytest.raises(ValueError) as exc:
                ThemeLoader.load("matrix")

        assert "Theme 'matrix' not found" in str(exc.value)

