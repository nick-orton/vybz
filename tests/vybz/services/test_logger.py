# tests/vybz/services/test_logger.py

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from vybz.services.logger import InteractionLogger

class TestInteractionLogger:
    """
    Unit tests for the InteractionLogger service.
    Verifies file persistence, formatting, and error handling.
    """

    @pytest.fixture
    def log_file(self, tmp_path):
        """Returns a path to a log file in a subdirectory."""
        return tmp_path / "logs" / "session.log"

    @pytest.fixture
    def logger(self, log_file):
        """Returns an initialized logger instance."""
        return InteractionLogger(log_file)

    def test_init_creates_directory(self, log_file):
        """
        Happy Path: Verify that initializing the logger creates 
        the parent directory if it doesn't exist.
        """
        # Arrange: ensure dir doesn't exist yet
        assert not log_file.parent.exists()

        # Act
        InteractionLogger(log_file)

        # Assert
        assert log_file.parent.exists()
        assert log_file.parent.is_dir()

    def test_log_session_start(self, logger, log_file):
        """
        Verify session start banner includes timestamp.
        """
        # Arrange
        with patch("vybz.services.logger.datetime") as mock_dt:
            mock_dt.now.return_value = "2099-01-01 12:00:00"
            
            # Act
            logger.log_session_start()

        # Assert
        content = log_file.read_text(encoding="utf-8")
        assert "SESSION START: 2099-01-01 12:00:00" in content
        assert "=" * 40 in content

    def test_log_conversation_flow(self, logger, log_file):
        """
        Verify the sequence of User Input -> Model Response is appended correctly.
        """
        # Act
        logger.log_user_input("junior-dev", "Hello")
        logger.log_model_response("junior-dev", "Hi there")

        # Assert
        content = log_file.read_text(encoding="utf-8")
        
        # Check formatting
        assert "\n[USER (junior-dev)]: Hello\n" in content
        assert "\n[MODEL (junior-dev)]: Hi there\n" in content
        # Check ordering (simple string find index check)
        assert content.find("[USER") < content.find("[MODEL")

    def test_log_error(self, logger, log_file):
        """Verify error logging format."""
        # Act
        logger.log_error("Something exploded")

        # Assert
        content = log_file.read_text(encoding="utf-8")
        assert "\n[ERROR]: Something exploded\n" in content

    def test_directory_creation_failure(self, tmp_path):
        """
        Sad Path: Verify that if directory creation fails (e.g. permissions),
        it reports to UI and doesn't crash.
        """
        log_path = tmp_path / "locked" / "test.log"

        with patch("vybz.services.logger.Path.mkdir", side_effect=OSError("Permission Denied")), \
             patch("vybz.services.logger.ui") as mock_ui:
            
            # Act
            InteractionLogger(log_path)

            # Assert
            mock_ui.print_error.assert_called_with("Failed to create log directory: Permission Denied")

    def test_write_failure(self, logger):
        """
        Sad Path: Verify that if writing to the file fails,
        it reports to UI and doesn't crash.
        """
        with patch("builtins.open", side_effect=IOError("Disk Full")), \
             patch("vybz.services.logger.ui") as mock_ui:
            
            # Act
            logger.log_event("This should fail")

            # Assert
            mock_ui.print_error.assert_called_with("Logging failed: Disk Full")
