---
status: "Completed"
type: "Blueprint"
author: "Senior Python Architect"
last_updated: "2026-01-11"
references: designs/multi-round-chat.md
---

# Multi-Round Chat Implementation Plan

This blueprint details the architectural changes required to transition `vybz` from a purely transactional (one-shot) tool to an interactive REPL (Read-Eval-Print Loop) system.

## Phase 1: The REPL Foundation (Input/Output Layer)
**Goal:** Establish the interactive loop and input handling mechanisms without connecting to the LLM yet. This ensures the UX (keybindings, multi-line support) feels right before adding API latency.

### 1. Dependency Management
*   **Action:** Add `prompt_toolkit>=3.0` to `pyproject.toml`.
*   **Rationale:** Standard `input()` cannot handle multi-line entry or custom keybindings (e.g., `Meta+Enter` to submit).

### 2. Module Creation: `src/vybz/repl.py`
*   **Action:** Create a new module encapsulating the loop logic.
*   **Key Components:**
    *   `ReplSession` class: Manages the `prompt_toolkit.PromptSession`.
    *   `start_repl(agent, model_id, codebase)`: Entry point function.
    *   **Input Handling:** Configure `PromptSession` to accept `Meta+Enter` (or `Esc` `Enter`) for submission to allow pasting code blocks.
    *   **Loop:** `while True:` loop checking for exit commands (`/exit`, `quit`).

### 3. Verification
*   Run the REPL in isolation.
*   Verify multi-line pasting works.
*   Verify styled printing using the existing `vybz.ui` module.

---

## Phase 2: The Chat Engine (SDK Integration)
**Goal:** Connect the REPL loop to the `google-genai` SDK, enabling stateful conversations.

### 1. Chat Logic Implementation
*   **Action:** Update `src/vybz/repl.py` to handle the GenAI client.
*   **Logic:**
    *   Initialize `client = genai.Client(...)`.
    *   Construct System Instructions: `Agent Role` + `Date Knowledge` + `CodeBase Snapshot`.
    *   **SDK Usage:**
        ```python
        chat = client.chats.create(
            model=model_id,
            config=types.GenerateContentConfig(
                system_instruction=full_system_prompt,
                temperature=0.7 # Slight creativity for chat
            )
        )
        ```
*   **Streaming:**
    *   Implement `chat.send_message_stream(user_input)`.
    *   Pipe chunks to `vybz.ui.stream_chunk` to maintain the existing visual aesthetic.

### 2. History Management
*   **Action:** Ensure the `chat` object retains history.
*   **Logging:** Append user inputs and full assistant responses to the log file (`interaction_log.txt`) to maintain a record of the session.

---

## Phase 3: Integration & CLI Refactor
**Goal:** Expose the REPL via the main `vybz` command.

### 1. `src/vybz/tools/work.py` Refactor
*   **Action:** Update `argparse` definition.
*   **Change:** Make `intent` an **optional** positional argument (`nargs='?'`).
*   **Logic:**
    *   If `intent` is provided -> Call existing `vibez.generate_and_continuous_log`.
    *   If `intent` is missing -> Call new `repl.start_repl`.

### 2. UI Polish
*   **Action:** Update `src/vybz/ui.py`.
*   **Change:** Add a `render_chat_header` that implies an open session rather than a single task.

---

## Technical Constraints & Standards
*   **SDK:** strictly use `client.chats.create` from `google-genai` (Unified).
*   **Context:** `CodeBase` is injected into `system_instruction`. If the codebase is massive, we may need to monitor token limits, though Gemini 3.0 Pro handles 1M+ tokens comfortably.
*   **Keybindings:**
    *   `Meta+Enter`: Submit.
    *   `Ctrl+C`: Interrupt generation (if streaming) or Exit loop.
```

### Senior Dev Peer Review
*   **Separation of Concerns:** The blueprint correctly isolates the REPL logic in a new file (`repl.py`) rather than complicating `vibez.py`.
*   **Backward Compatibility:** Phase 3 explicitly preserves the existing "One-Shot" command capability by checking for the presence of the `intent` argument.
*   **Dependency:** `prompt_toolkit` is a heavy dependency but necessary for a professional TUI experience. It is standard for this class of problem.
*   **Context Strategy:** Injecting CodeBase into system instructions is the most robust way to ensure the model "knows" the code throughout the session without polluting the conversational history window unnecessarily (though technically system instructions count towards context).

### Verification
The blueprint itself is a documentation artifact. To verify it "works," I will check that it aligns with the `designs/multi-round-chat.md` spec.
*   *Design:* "Input Handling: Support multi-line... prompt_toolkit". -> *Blueprint Phase 1.*
*   *Design:* "SDK Integration: client.chats.create". -> *Blueprint Phase 2.*
*   *Design:* "CLI Refactor: intent positional argument becomes OPTIONAL". -> *Blueprint Phase 3.*


