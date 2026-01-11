---
status: "Draft"
type: "Design"
last_updated: "2026-01-11"
references: intents/multi-round-chat.md, designs/pretty-print-sysout.md
---

# Interactive Chat Mode (REPL) Specification

## 1. High-Level Intent
Implement a stateful, interactive Read-Eval-Print Loop (REPL) for the Vybz
Workbench. Currently, `vybz` is a "fire-and-forget" tool (One Shot). This
feature enables **Multi-Round Conversations**, allowing users to refine context,
ask follow-up questions, and iteratively develop code with a specific Agent
without reloading the entire context stack every time.

## 2. User Stories
* As a User, I want to launch `vybz <agent>` without a specific intent argument
  to enter "Interactive Mode."
* As a User, I want to type multi-line instructions (e.g., pasting a code block)
  and submit them using a specific keybind (e.g., `Meta+Enter` or `Esc` then
  `Enter`), rather than being limited to a single command-line string.
* As a User, I want the Agent to remember the previous turn's context (Chat
  History) so I can say "Now refactor that function" without re-explaining
  which function.
* As a User, I want the input and output to be visually distinct (TUI) to
  maintain the "Vibe Coding" aesthetic.

## 3. Acceptance Criteria
- [ ] `prompt_toolkit` is added to `pyproject.toml` dependencies.
- [ ] `src/vybz/tools/work.py` is refactored: The `intent` positional argument
      becomes **OPTIONAL**.
- [ ] If `intent` is missing, the system enters `InteractiveSession`.
- [ ] **Input Handling:**
    - Support multi-line input.
    - Submit via `Meta+Enter` (or generic safe keybind).
    - Exit via `Ctrl+C` or typing `/exit`.
- [ ] **SDK Integration:** Uses `client.chats.create()` from `google-genai`
      v1.57+ to maintain server-side context window history where possible, or
      client-managed history.
- [ ] **System Instructions:** The Agent's persona (`role_spec`) is strictly
      enforced throughout the chat session.
- [ ] **Logging:** The entire session transcript is appended to the log file,
      clearly demarcating User vs. Agent turns.

## 4. Implementation Hints (Technical)
*   **Libraries:**
    *   `prompt_toolkit`: For the multi-line input buffer and keybindings.
    *   `rich`: Already present, use for rendering the Agent's response stream.
*   **SDK (`google-genai` v1.57):**
    ```python
    # Chat Initialization
    chat = client.chats.create(
        model=model_id,
        config=types.GenerateContentConfig(
            system_instruction=agent.construct_agent_role_profile()
        )
    )
    # Sending Message
    response = chat.send_message_stream(content=user_input)
    ```
*   **Architecture:**
    *   Create `src/vybz/repl.py` to encapsulate the loop logic.
    *   Keep `vibez.py` for shared GenAI configuration and utility functions.
*   **UI/UX:**
    *   Use `prompt_toolkit.PromptSession`.
    *   Style the prompt (e.g., `[Junior-Dev] > `).

## 5. Execution Plan
1.  [ ] **Dependencies:** Add `prompt_toolkit>=3.0` to `pyproject.toml`.
2.  [ ] **REPL Module:** Create `src/vybz/repl.py`. Implement the `start_repl`
        function using `prompt_toolkit` for input and `vibez` logic for streaming
        responses.
3.  [ ] **Chat Logic:** Implement `client.chats.create` wrapper in `repl.py`.
        Ensure `CodeBase` (if provided) is injected as the *first* user message
        or part of system instructions to prime the context.
4.  [ ] **CLI Refactor:** Update `src/vybz/tools/work.py` to make `intent`
        nargs='?'. Add conditional logic: if `intent` is None -> `repl.start_repl(...)`.
5.  [ ] **Testing:** Verify multi-turn memory (e.g., Turn 1: "Define x=1",
        Turn 2: "What is x?").

