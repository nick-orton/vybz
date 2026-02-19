import sys
from pathlib import Path
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

# Ensure we can import vybz
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

async def test_interactive_branch_logic():
    """
    Verifies that work.main() correctly identifies the interactive branch
    and initializes the ClientSessionManager.
    """
    from vybz.tools.work import main

    # Mock CLI Args: vybz junior-dev (no intent)
    mock_args = MagicMock()
    mock_args.agent = "junior-dev"
    mock_args.intent = None
    mock_args.codebase = "/tmp"
    mock_args.theme = "default"
    mock_args.init_library = False
    mock_args.library = None
    mock_args.log_file = "/tmp/vybz.log"
    mock_args.mode = "vi"
    mock_args.model = "gemini-3-flash"

    with patch("argparse.ArgumentParser.parse_args", return_value=mock_args), \
         patch("vybz.tools.work.ClientSessionManager") as MockManager, \
         patch("vybz.tools.work.repl.ReplSession") as MockRepl, \
         patch("vybz.tools.work.ui"), \
         patch("vybz.tools.work.Squad"):

        # Setup manager mock
        instance = MockManager.return_value
        instance.connect = AsyncMock(return_value=True)
        instance.initialize = AsyncMock()

        # Setup REPL mock
        repl_instance = MockRepl.return_value
        repl_instance.start = AsyncMock()

        # Act
        await main()

        # Assert
        instance.connect.assert_called_once()
        instance.initialize.assert_called_with("junior-dev", Path("/tmp"))
        repl_instance.start.assert_called_once()
        print("[SUCCESS] work.py interactive branch verified.")

if __name__ == "__main__":
    asyncio.run(test_interactive_branch_logic())
