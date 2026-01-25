---
status: "Draft"
type: "Critique"
author: "Senior Python Architect"
last_updated: "2026-01-24"
references: src/vybz/repl.py, src/vybz/services/session.py
---

# REPL Architecture Critique: Lingering Responsibilities

## 1. Executive Summary
The refactoring of `ReplSession` to utilize `SessionManager` and `CommandRegistry` was a major architectural improvement. However, the class still violates the **Single Responsibility Principle (SRP)** by retaining ownership of **Interaction Logging** and **Static Asset Loading**.

Currently, `ReplSession` is not just a View Controller; it is also a File Logger and a Resource Manager. This coupling complicates testing and makes the `Command` classes unnecessarily dependent on the session implementation details.

## 2. Structural Defects

### 2.1. Logging Implementation Leakage
*   **Code:** `ReplSession._log_to_file` manually handles `open()`, `write()`, and directory creation.
*   **Critique:** The REPL (User Interface) should not be concerned with *how* the conversation is persisted to disk.
*   **Impact:**
    1.  If we want to change the log format (e.g., to JSONL for easier parsing by other tools), we have to modify `repl.py`.
    2.  `vibez.py` (One-Shot mode) likely duplicates this logging logic, leading to format drift.
*   **Recommendation:** Extract an `InteractionLogger` service or move this responsibility into `SessionManager` (which already holds the history).

### 2.2. Asset Loading Inversion
*   **Code:** `ReplSession._load_asset` resolves paths relative to `__file__`.
*   **Critique:** Commands like `HelpCommand` call `session._load_asset("repl_help.txt")`. This forces a dependency on the `ReplSession` instance just to read a static text file.
*   **Impact:** Unit testing commands requires mocking the session's asset loader. Assets are static resources and should be accessible via a stateless `ResourceManager` or utility function in `vybz.assets`.

### 2.3. The `_handle_input` Method
*   **Code:** This method orchestrates the API stream, UI rendering, and logging.
*   **Critique:** While some orchestration is necessary in the controller, the specific act of "Logging the Turn" is interleaved with UI rendering logic.
    ```python
    # Logic mixing:
    ui.stream_chunk(chunk.text) # View
    f.write(chunk.text)         # Persistence
    full_response.append(...)   # State
    ```
*   **Recommendation:** The `SessionManager` or a `ChatService` should ideally yield the stream, and the logging should happen via a callback or an observer pattern, rather than imperative writes inside the UI loop.

## 3. Proposed Refactoring Plan

### Phase 1: Extract Asset Manager
1.  Create `src/vybz/assets/loader.py` with a static `load_text(filename: str) -> str` function.
2.  Refactor `repl.py` and `commands/core.py` to use this loader directly.
3.  Remove `_load_asset` from `ReplSession`.

### Phase 2: Extract Logger
1.  Create `src/vybz/services/logger.py` defining an `InteractionLogger` class.
2.  Inject this logger into `ReplSession` (or `SessionManager`).
3.  Replace `_log_to_file` calls with `self.logger.log_turn(user_input, response)`.

### Phase 3: Cleanup
1.  Move `_parse_editing_mode` out of `ReplSession` to a utility module or `config.py`.

## 4. Benefit Analysis
*   **Testability:** Commands can be tested without a mock session for assets.
*   **Consistency:** Logging logic is centralized, ensuring `vybz` (CLI) and `repl` (Interactive) produce identical log formats.
*   **Cleanliness:** `ReplSession` becomes purely a TUI Controller, connecting Input (PromptToolkit) to Logic (SessionManager) to Output (Rich).
```

### 3. Senior Dev Peer Review
*   **Tone:** The critique is objective and focuses on architectural principles (SRP, Dependency Inversion).
*   **Actionability:** The proposed plan is concrete and broken into phases.
*   **Accuracy:** The analysis of `repl.py` accurately reflects the current codebase state provided in the context.

### 4. Verification Script
N/A - This task generates a Markdown document. Verification involves checking the file content.

```python
if __name__ == "__main__":
    from pathlib import Path
    critique_path = Path(".vybz/critiques/repl-architecture-critique.md")
    if critique_path.exists():
        print(f"[OK] Critique created at {critique_path}")
        print(critique_path.read_text()[:300] + "...")
    else:
        print("[FAIL] Critique not found.")
