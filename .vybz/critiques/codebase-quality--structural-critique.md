---
status: "Completed"
type: "Critique"
author: "Senior Python Architect"
last_updated: "2026-01-17"
references: src/vybz/repl.py, src/vybz/vibez.py
---

# Codebase Quality & Structural Critique

## 1. Executive Summary
The `vybz` codebase has established a strong domain foundation with the separation of `Agent`, `Skill`, and `CodeBase` objects. The recent transition to `toml` configuration and the `rich` UI layer demonstrates a commitment to modern Python standards.

However, the rapid evolution of the interactive features has led to significant **technical debt in `src/vybz/repl.py`**. This module has accumulated responsibilities that belong elsewhere, threatening maintainability as the feature set grows.

## 2. Structural Analysis

### 2.1. The "God Object": `ReplSession`
*   **Violation:** The `ReplSession` class violates the **Single Responsibility Principle (SRP)**. It currently manages:
    1.  **TUI Rendering:** (Prompt styling, output streaming).
    2.  **GenAI API State:** (Managing `active_chat`, `sessions`, `client`).
    3.  **Command Parsing:** (The `_handle_command` method is a growing `if/elif` block).
    4.  **Business Logic:** (Context refreshing, Artifact saving).
*   **Impact:** Adding a simple command (e.g., `/history`) requires modifying the core loop class, violating the **Open/Closed Principle**. The class is becoming brittle and difficult to test in isolation.

### 2.2. Logic Duplication: Prompt Assembly
*   **Violation:** Both `vibez.py` (Legacy One-Shot) and `repl.py` (Interactive) contain nearly identical logic for constructing the System Instruction (concatenating `role_spec` + `Current Date` + `CodeBase`).
*   **Impact:** If we change how "Memory" or "Context" is injected, we must modify multiple files. This duplication invites regression bugs where the CLI behaves differently than the REPL.

### 2.3. Legacy Drift: `vibez.py`
*   **Violation:** `vibez.py` handles its own logging, UI printing, and client configuration, distinct from `repl.py`. It is effectively a parallel application path that is slowly drifting from the core architecture.
*   **Remedy:** `vibez.py` should eventually be deprecated or refactored to use the same `Session` controller as the REPL, just running in a "Headless" mode.

## 3. Object-Oriented Improvements

### 3.1. Polymorphism for Commands
Instead of string matching in `_handle_command`, the system should implement the **Command Pattern**.
*   **Current:** `if cmd == "/save": self._cmd_save()`
*   **Proposed:** An abstract `Command` class with an `execute(context)` method. This allows commands to be defined in separate files (`src/vybz/commands/`) and registered dynamically.

### 3.2. Encapsulation of Session State
The logic for "Switching Agents" and "Refreshing Context" is complex state manipulation that clutters the UI code.
*   **Proposed:** Extract a `SessionManager` service. The REPL should simply call `session_manager.switch_agent("pm")` and `session_manager.get_active_chat()`, without knowing *how* the API client is handled.

## 4. Proposed Refactoring Plan

1.  **Extract `src/vybz/services/context.py`:** A `ContextAssembler` service to centralize system prompt construction.
2.  **Extract `src/vybz/services/session.py`:** A `SessionManager` to handle GenAI client interactions and multi-agent state.
3.  **Implement Command Pattern:** Create `src/vybz/commands/` to house individual command logic, decoupling them from the REPL loop.
