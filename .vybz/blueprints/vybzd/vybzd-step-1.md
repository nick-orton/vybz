---
status: "Draft"
type: "Blueprint"
author: "Senior Python Architect"
last_updated: "2026-02-06"
references: blueprints/vybzd/vybzd-top-level-blueprint.md
---

# Vybz Engine Refactor - Step 1: Structural Separation

This blueprint details the physical restructuring of the codebase to create the
`shared` namespace. This is the prerequisite for separating the Client (CLI) 
from the Server (ADK Runtime).

## 1. Goal
To move core domain entities and logic shared by both Client and Server into 
`src/vybz/shared/`, ensuring that neither the UI nor the Engine has a circular 
dependency on the other.

## 2. File Moves & Renames

We will create a new package `src/vybz/shared/` and migrate the following modules:

| Source | Destination | Rationale |
| :--- | :--- | :--- |
| `src/vybz/agent.py` | `src/vybz/shared/agent.py` | Domain Object used by both. |
| `src/vybz/skill.py` | `src/vybz/shared/skill.py` | Domain Object used by both. |
| `src/vybz/context_engine.py` | `src/vybz/shared/codebase.py` | Renamed to match Class `CodeBase`. |
| `src/vybz/biblos.py` | `src/vybz/shared/library.py` | Renamed for clarity. |
| `src/vybz/squad.py` | `src/vybz/shared/squad.py` | Factory/Registry used by both. |

## 3. Placeholder Creation
We will establish the empty packages for future phases:
*   `src/vybz/server/__init__.py`
*   `src/vybz/client/__init__.py`

## 4. Import Refactoring Strategy

We must update all references in the codebase.

### 4.1. Consumer Modules
The following modules must be updated to import from `vybz.shared.*`:
*   `src/vybz/repl.py`
*   `src/vybz/vibez.py`
*   `src/vybz/tools/work.py`
*   `src/vybz/tools/autocommit_gen.py`
*   `src/vybz/services/session.py`
*   `src/vybz/services/context.py`
*   `src/vybz/commands/core.py`

### 4.2. Internal Dependencies
The moved files themselves reference each other.
*   `squad.py` imports `agent`, `library`.
*   `agent.py` imports `skill`, `library`.
*   **Action:** Update these relative imports to use intra-package references 
    (e.g., `from .agent import Agent`) or absolute `vybz.shared` imports.

## 5. Test Suite Updates
The `tests/` directory mirrors `src/`. We should restructure it to match.
*   Move `tests/vybz/test_agent.py` -> `tests/vybz/shared/test_agent.py`
*   Move `tests/vybz/test_skill.py` -> `tests/vybz/shared/test_skill.py`
*   Update imports in `conftest.py` and all test files.

## 6. Verification Strategy
1.  **Static Analysis:** Run `grep -r "from vybz.agent" .` to ensure no stale 
    imports remain.
2.  **Unit Tests:** Run `pytest`. All tests must pass.
3.  **Manual:** Run `vybz junior-dev` to ensure the CLI still boots using the 
    new paths.

## 7. Execution Steps
1.  Create directories `src/vybz/shared`, `src/vybz/server`, `src/vybz/client`.
2.  Perform file moves (git mv).
3.  Perform search-and-replace for imports.
4.  Move and update tests.
5.  Verify.
