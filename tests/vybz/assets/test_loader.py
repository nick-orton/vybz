import pytest
from unittest.mock import patch, MagicMock
from vybz.assets.loader import AssetLoader

class TestAssetLoader:
    """
    Unit tests for the AssetLoader service.
    Verifies safe loading of static text resources.
    """

    def test_load_text_success(self, tmp_path):
        """
        Happy Path: Verify that an existing file is read correctly.
        """
        # Arrange
        test_filename = "help_menu.txt"
        test_content = "Commands: /help, /exit"

        # Create a real file in the temp directory
        dummy_file = tmp_path / test_filename
        dummy_file.write_text(test_content, encoding="utf-8")

        # Mock the internal directory resolution to point to our temp dir
        with patch.object(AssetLoader, "_get_assets_dir", return_value=tmp_path):
            # Act
            result = AssetLoader.load_text(test_filename)

        # Assert
        assert result == test_content

    def test_load_text_not_found(self, tmp_path):
        """
        Sad Path: Verify that requesting a non-existent file returns
        a specific error message instead of raising an exception.
        """
        # Arrange
        target_file = "ghost_file.txt"

        with patch.object(AssetLoader, "_get_assets_dir", return_value=tmp_path):
            # Act
            result = AssetLoader.load_text(target_file)

        # Assert
        assert f"Asset not found: {target_file}" in result

    def test_load_text_exception(self):
        """
        Sad Path: Verify that IO errors (e.g., PermissionError) during read
        are caught and returned as error messages.
        """
        # Arrange
        filename = "locked_file.txt"

        # We need to mock the directory path object and the file path object it produces
        mock_dir = MagicMock()
        mock_file = MagicMock()

        # Setup the chain: dir / filename -> file
        mock_dir.__truediv__.return_value = mock_file

        # Setup file behavior: It exists, but reading fails
        mock_file.exists.return_value = True
        mock_file.read_text.side_effect = PermissionError("Access Denied")

        with patch.object(AssetLoader, "_get_assets_dir", return_value=mock_dir):
            # Act
            result = AssetLoader.load_text(filename)

        # Assert
        # Verify the / operator was called correctly
        mock_dir.__truediv__.assert_called_with(filename)

        # Verify result contains the exception message
        assert f"Failed to load asset '{filename}'" in result
        assert "Access Denied" in result
