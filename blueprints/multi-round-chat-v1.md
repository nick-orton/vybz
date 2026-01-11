---
status: "Draft"
type: "Blueprint"
last_updated: "2026-01-11"
references: blueprints/multi-round-chat.md, designs/multi-round-chat.md
---

# Phase 1: REPL Foundation & Input Handling

This blueprint specifies the implementation of the **Read-Eval-Print Loop (REPL)** foundation. 
**Goal:** Enable the `vybz` CLI to enter an interactive session where users can type multi-line input and submit it via custom keybindings. 
**Constraint:** No LLM integration in this phase. The "Eval" step will simply echo the input back to the screen to verify the loop mechanics.

## 1. Dependency Management
*   **Target:** `pyproject.toml`
*   **Action:** Add `prompt_toolkit >= 3.0.0`.

## 2. Module Specification: `src/vybz/repl.py`
A new module responsible for handling the user input loop.

### Class: `ReplSession`
*   **Attributes:**
    *   `session`: Instance of `prompt_toolkit.PromptSession`.
    *   `agent`: The active `Agent` (used for prompt styling).
*   **Keybindings:**
    *   **Standard:** `Enter` inserts a newline (allowing multi-line code pasting).
    *   **Submit:** `Meta+Enter` (Alt+Enter) or `Esc` followed by `Enter` submits the buffer.
    *   **Exit:** `Ctrl+C` or `Ctrl+D` handles graceful exit.
*   **Methods:**
    *   `loop()`: The main `while True` loop.
    *   `_configure_styles()`: Sets up the visual prompt (e.g., `[Junior-Dev] >>`).

## 3. CLI Integration: `src/vybz/tools/work.py`
*   **Logic Change:** The `intent` argument becomes **OPTIONAL**.
*   **Flow:**
    *   If `intent` is provided -> Run existing "One-Shot" logic.
    *   If `intent` is missing -> Initialize `ReplSession` and start `loop()`.

## 4. Verification Strategy
1.  Run `vybz junior-dev`.
2.  Verify prompt appears: `[Tactical Python Architect] >>`.
3.  Type a multi-line python function.
4.  Press `Enter` (Should make new line).
5.  Press `Alt+Enter` (Should submit).
6.  System should print: "DEBUG: Received <content>".
7.  Type `/exit` or hit `Ctrl+D` to quit.
```

---

## 2. Execution Plan (Junior Developer Tasks)

Here are the specific implementation steps. Execute them in order.

### Task 1: Update Dependencies
**File:** `pyproject.toml`
**Action:** Add `prompt_toolkit` to the dependencies list.

```toml
# ... existing config ...
dependencies = [
    "google-genai>=1.57",
    "python-dotenv",
    "pathspec>=0.11.0",
    "rich>=13.0",
    "prompt_toolkit>=3.0.0", # <--- ADD THIS
]
# ... existing config ...
```

### Task 2: Create the REPL Module
**File:** `src/vybz/repl.py`
**Action:** Create this file with the following content. This handles the input loop and keybindings.

```python
"""
repl.py

Handles the Interactive Read-Eval-Print Loop (REPL) for Vybz.
Leverages prompt_toolkit for multi-line editing and custom keybindings.
"""

import sys
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import HTML
from vybz.agent import Agent
from vybz import ui

class ReplSession:
    """
    Manages the state and input loop for an interactive session.
    """

    def __init__(self, agent: Agent, model_id: str):
        self.agent = agent
        self.model_id = model_id
        self.kb = KeyBindings()
        self._setup_keybindings()
        
        # Initialize PromptSession with our bindings
        self.session = PromptSession(key_bindings=self.kb)

    def _setup_keybindings(self) -> None:
        """
        Define custom keybindings:
        - Meta+Enter (Alt+Enter): Submit input.
        - Enter: Insert newline (default behavior for easy code pasting).
        """
        @self.kb.add('escape', 'enter')
        def _(event):
            """Submit when Meta+Enter or Esc+Enter is pressed."""
            event.current_buffer.validate_and_handle()

    def start(self) -> None:
        """
        Starts the interactive loop.
        """
        ui.print_system(f"Entering Interactive Mode with {self.agent.name}...")
        ui.print_system("Tip: Press 'Alt+Enter' (or Esc+Enter) to submit. Type '/exit' to quit.")

        # Visual Prompt Styling
        # We use HTML formatting supported by prompt_toolkit
        prompt_text = HTML(f"<b><style fg='cyan'>[{self.agent.name}]</style></b> >> ")

        while True:
            try:
                # 1. READ
                user_input = self.session.prompt(prompt_text, multiline=True)
                
                # Check for exit commands
                if user_input.strip().lower() in ["/exit", "quit", "exit"]:
                    raise EOFError

                if not user_input.strip():
                    continue

                # 2. EVAL (Phase 1 Stub: Echo only)
                # In Phase 2, this is where we call client.chats.send_message
                self._handle_input_stub(user_input)

            except KeyboardInterrupt:
                # User pressed Ctrl+C - interrupt current action or exit?
                # For now, let's just clear buffer or exit loop
                continue
            except EOFError:
                ui.print_system("Exiting session.")
                break
            except Exception as e:
                ui.print_error(f"REPL Error: {e}")

    def _handle_input_stub(self, text: str) -> None:
        """
        Temporary handler to verify input capture in Phase 1.
        """
        ui.console.print(f"[dim]DEBUG: Captured {len(text)} chars[/dim]")
        ui.console.print(f"[green]{text}[/green]")
        ui.console.print("-" * 40)

```

### Task 3: Refactor CLI Entry Point
**File:** `src/vybz/tools/work.py`
**Action:** Update `argparse` configuration to make `intent` optional (`nargs='?'`) and branch the logic to call `repl.py`.

```python
#!/usr/bin/env python3
"""
work.py

The primary CLI entry point for Vybz Kartel.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

# Vybz Kartel Core Imports
import vybz.vibez as vibez
import vybz.ui as ui
import vybz.repl as repl  # <--- NEW IMPORT
from vybz.context_engine import CodeBase
from vybz.squad import Squad


def main() -> None:
    """
    Parses command line arguments and orchestrates the Vibe Coding session.
    """
    parser = argparse.ArgumentParser(
        description="Vybz Kartel: AI-Orchestrated Vibe Coding CLI",
        formatter_class=argparse.RawTextHelpFormatter
    )

    # Positional Arguments
    parser.add_argument(
        "agent",
        help="Target Agent Persona \n['junior-dev', 'pm', 'senior-dev', 'advisor', 'tech-writer' ]"
    )
    
    # CHANGED: 'intent' is now optional via nargs='?'
    parser.add_argument(
        "intent",
        nargs='?', 
        default=None,
        help="The task description. If omitted, enters Interactive Mode."
    )

    # Optional Arguments
    parser.add_argument(
        "-m", "--model",
        default="gemini-3-pro-preview",
        help="Target Gemini Model ID.\nDefault: gemini-3-pro-preview"
    )
    parser.add_argument(
        "-l", "--log-file",
        default="/tmp/vybz.log",
        help="Path to the interaction log file.\nDefault: /tmp/vybz.log"
    )
    parser.add_argument(
        "-c", "--codebase",
        default=None,
        help=(
            "Root path to snapshot for context.\n"
            "If omitted, runs in 'Greenfield' mode (no code context)."
        )
    )

    args = parser.parse_args()

    try:
        # 1. Initialize the Google GenAI Client
        client = vibez.configure_genai_client()

        # 2. Load the Agent
        try:
            agent = Squad.get_agent(args.agent)
        except ValueError:
            ui.print_error(f"Agent '{args.agent}' not found.")
            ui.print_system(f"Available Agents: {', '.join(Squad.list_agents())}")
            sys.exit(1)

        # 3. Snapshot Codebase (Optional)
        codebase: Optional[CodeBase] = None
        if args.codebase:
            cb_path = Path(args.codebase)
            ui.print_system(f"Snapshotting codebase at: {cb_path.resolve()} ...")
            try:
                codebase = CodeBase(cb_path)
            except (FileNotFoundError, NotADirectoryError) as e:
                ui.print_error(f"CodeBase Error: {e}")
                sys.exit(1)
        else:
            ui.print_system("No codebase provided. Running in GREENFIELD mode.")

        # 4. Execution Branching
        if args.intent:
            # ---> ONE-SHOT MODE (Legacy)
            vibez.generate_and_continuous_log(
                client=client,
                model_id=args.model,
                agent=agent,
                intent=args.intent,
                codebase=codebase,
                log_file_path=args.log_file
            )
        else:
            # ---> INTERACTIVE MODE (New Phase 1)
            # Note: We aren't passing 'client' or 'codebase' to the stub yet in Phase 1
            session = repl.ReplSession(agent=agent, model_id=args.model)
            session.start()

    except KeyboardInterrupt:
        ui.print_warning("Session interrupted by user.")
        sys.exit(130)
    except Exception as e:
        ui.print_error(f"Critical Runtime Error: {e}")
        # Print stack trace for debugging if needed, or rely on ui error
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
```

### Verification Script
Run this immediately after applying changes to confirm Phase 1 success.

```bash
# 1. Install new dependency
pip install prompt_toolkit

# 2. Run in Interactive Mode
# Should show: "[Tactical Python Architect] >>"
vybz junior-dev

# 3. Test Input (Paste this whole block)
def hello():
    print("Multi-line works!")
    return True

# 4. Press Alt+Enter to submit
# Expected: The code echoes back in green.

