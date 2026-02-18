import asyncio
from unittest.mock import AsyncMock, MagicMock
from pathlib import Path
from vybz.repl import ReplSession

async def verify_async_loop():
    """
    Simulates a network-backed chat turn to ensure the REPL 
    correctly handles the async generator.
    """
    print("--- Verifying Async REPL Loop ---")
    
    # 1. Mock the Client Manager
    mock_sm = MagicMock()
    mock_sm.active_agent.name = "TestBot"
    mock_sm.active_agent.id = "test-bot"
    mock_sm.codebase = None
    
    async def mock_stream(text):
        yield "Part 1 "
        yield "Part 2"
        
    mock_sm.chat.side_effect = mock_stream
    
    # 2. Instantiate with mocked UI/Logger
    with MagicMock() as mock_prompt:
        repl = ReplSession(mock_sm, log_file=Path("/tmp/test.log"))
        repl.session = mock_prompt
        
        # 3. Execute Input
        await repl._handle_input("Hello")
        
        assert repl.last_response == "Part 1 Part 2"
        print("[SUCCESS] Async stream consumed and captured.")

if __name__ == "__main__":
    asyncio.run(verify_async_loop())
