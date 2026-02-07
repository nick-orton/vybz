import sys
import argparse
from unittest.mock import patch, MagicMock

def test_vybzd_entry_point():
    """
    Verifies that the start() function parses args and calls uvicorn.run.
    """
    # 1. Mock uvicorn and sys.argv
    with patch("uvicorn.run") as mock_run, \
         patch("sys.argv", ["vybzd", "--port", "9090", "--reload"]):
        
        # 2. Import the module (which defines 'start')
        from vybz.server.main import start
        
        # 3. Execute
        start()
        
        # 4. Assert
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        
        # Check positional arg (app string)
        assert call_args[0][0] == "vybz.server.main:app"
        
        # Check kwargs
        assert call_args[1]["port"] == 9090
        assert call_args[1]["reload"] is True
        assert call_args[1]["host"] == "127.0.0.1" # Default

if __name__ == "__main__":
    try:
        test_vybzd_entry_point()
        print("[SUCCESS] vybzd entry point logic verified.")
    except Exception as e:
        print(f"[FAIL] {e}")
