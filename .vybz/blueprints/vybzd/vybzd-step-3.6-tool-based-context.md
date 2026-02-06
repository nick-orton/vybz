---
status: "Draft"
type: "Blueprint"
author: "Senior Python Architect"
last_updated: "2026-02-15"
references: blueprints/vybzd/vybzd-step-3.5-skills-and-context.md
---

# Vybz Engine Refactor - Step 3.6: Tool-Based Context (Agentic RAG)

This blueprint details the architectural pivot from "Context Stuffing" 
(injecting the entire codebase into the system prompt) to "Tool-Based 
Retrieval" (giving the Agent tools to read the filesystem).

## 1. The Problem
The current architecture snapshots the entire codebase on the Client and sends 
it as a massive Markdown string to the Server.
*   **Token Limits:** Large codebases exceed context windows.
*   **Latency:** Re-sending the snapshot on every `/update` is expensive.
*   **Staleness:** The agent relies on a static snapshot rather than the live disk state.

## 2. The Solution
We will implement **Agentic RAG**. The Server will host a `FileSystemTool` set.
The Agent will receive the `root_path` in its context and must actively query 
the filesystem (List/Read) to gather information.

**Constraint:** This assumes `vybzd` is running on the same machine as the 
codebase (Localhost) or has access to a shared mount.

## 3. Module Specification: `src/vybz/server/tools/fs.py`

We need a dedicated toolset that wraps the existing `CodeBase` logic 
(gitignore compliance) but exposes it as granular functions.

### Class: `FileSystemTools`
*   **Constructor:** `__init__(self, root_path: Path)`
    *   Initializes `self.codebase = CodeBase(root_path)` to reuse ignore logic.
*   **Tool: `list_files(rel_path: str = ".") -> str`**
    *   Uses `CodeBase._walk_tree` logic to return a tree view of the target directory.
    *   Respects `.gitignore`.
*   **Tool: `read_file(rel_path: str) -> str`**
    *   Reads a specific file.
    *   Validates path is within `root_path` (Directory Traversal Protection).
    *   Returns content wrapped in markdown code blocks.

## 4. Refactor: `src/vybz/server/state.py`

### 4.1 Update `create_session`
*   **Input Change:** The `context` argument should now be interpreted as the
    `root_path` string, not the full file dump.
*   **Tool Binding:**
    1.  Instantiate `fs_tools = FileSystemTools(root_path)`.
    2.  Wrap methods as ADK Tools: `adk.Tool.from_function(fs_tools.list_files)`.
    3.  Pass these tools to the `adk.Agent` constructor (or update the agent instance).

### 4.2 Session Isolation
Since each session might target a different codebase root, tools must be 
**Session Scoped**. The `ServerState` must ensure that the `Runner` for 
Session A has tools bound to Root A, and Session B to Root B.

## 5. Refactor: `src/vybz/services/context.py`

### 5.1 Update `ContextAssembler`
*   **Remove:** The logic that appends `codebase.render()` to the prompt.
*   **Add:** Logic to inject the `root_path` into the system instruction.
    *   *"You have access to the filesystem at `{root_path}`. Use `list_files` 
        to explore and `read_file` to examine code. Do not hallucinate file 
        contents."*

## 6. Execution Steps

1.  **Create:** `src/vybz/server/tools/fs.py`.
2.  **Refactor:** `src/vybz/server/state.py` to bind tools dynamically during `create_session`.
3.  **Refactor:** `src/vybz/services/context.py` to remove context stuffing.
4.  **Update:** `src/vybz/server/adapter.py` to allow tool injection during hydration.

## 7. Verification Strategy

### 7.1 Unit Test
*   Initialize `FileSystemTools` with a temp directory.
*   Verify `list_files` respects ignored files.
*   Verify `read_file` blocks `../` traversal.

### 7.2 Integration Test
*   Start `vybzd`.
*   Init session with `root_path="."`.
*   Send message: "List the files in src/vybz".
*   Verify Agent calls the tool and returns the list.
