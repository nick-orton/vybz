"""
src/vybz/services/logger.py

Handles persistence of interaction logs.
Decouples file I/O and formatting from the REPL session loop.
Updated to sanitize ANSI escape codes before writing to disk (Fixes Issue #5).
"""

import re
from pathlib import Path
from datetime import datetime
from vybz.client import ui


class InteractionLogger:
    """
    Manages writing conversation history to disk.
    """

    def __init__(self, log_path: Path):
        """
        Initialize the logger.

        Args:
            log_path: The file path to write logs to.
        """
        self.log_path = log_path
        self._ensure_directory()

        # Regex to match ANSI escape sequences (Issue #5)
        # This targets standard SGR (Select Graphic Rendition) codes used for colors/styling.
        self._ansi_regex = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

    def _ensure_directory(self) -> None:
        """Creates the parent directory if it does not exist."""
        try:
            if not self.log_path.parent.exists():
                self.log_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            ui.print_error(f"Failed to create log directory: {e}")

    def _sanitize(self, text: str) -> str:
        """
        Removes ANSI escape codes from text to ensure clean log files.
        """
        if not text:
            return ""
        return self._ansi_regex.sub('', text)

    def _append(self, text: str) -> None:
        """
        Appends sanitized text to the log file.
        """
        # Sanitize before persisting to disk
        clean_text = self._sanitize(text)
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(clean_text)
        except IOError as e:
            # We don't want to crash the whole application if logging fails,
            # but we should notify the UI.
            ui.print_error(f"Logging failed: {e}")

    def log_session_start(self) -> None:
        """Logs the session start banner with timestamp."""
        ts = datetime.now()
        self._append(f"\n{'='*40}\nSESSION START: {ts}\n{'='*40}\n")

    def log_user_input(self, agent_name: str, text: str) -> None:
        """Logs the user's prompt."""
        self._append(f"\n[USER ({agent_name})]: {text}\n")

    def log_model_response(self, agent_name: str, text: str) -> None:
        """Logs the model's full response."""
        self._append(f"\n[MODEL ({agent_name})]: {text}\n")
        self._append("-" * 40)

    def log_event(self, message: str) -> None:
        """Logs a system event (e.g., Agent Switch, Error)."""
        self._append(f"\n{'='*40}\n{message}\n{'='*40}\n")

    def log_error(self, error_message: str) -> None:
        """Logs an error message."""
        self._append(f"\n[ERROR]: {error_message}\n")
