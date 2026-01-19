---
status: "Completed"
type: "Design"
author: "PM Lead"
last_updated: "2026-01-14"
references: 
---

# Unit Testing Architecture Specification

## 1. High-Level Intent
Establish a robust, automated testing infrastructure for the Vybz codebase. 
Currently, verification is manual. We need to ensure that refactors (like the 
Skills migration) do not break existing functionality. We will adopt a 
"Test-Driven" mindset for future features.

## 2. Standards & Tools
*   **Framework:** `pytest` (Standard).
*   **Mocking:** `pytest-mock` (Wrapper around `unittest.mock`).
*   **Coverage:** `pytest-cov` (Optional, for future metric tracking).
*   **Location:** All tests reside in `tests/`.

## 3. Organization Strategy
The `tests/` directory will mirror the `src/` directory structure.

```text
vybz/
├── src/
│   └── vybz/
│       ├── agent.py
│       └── skill.py
├── tests/
│   ├── conftest.py       # Global Fixtures (Mock Clients, Env Vars)
│   └── vybz/
│       ├── test_agent.py # Tests for src/vybz/agent.py
│       └── test_skill.py # Tests for src/vybz/skill.py
```

## 4. Testing Rules
1.  **No API Calls:** The `google-genai` client must be mocked in all unit 
    tests.
2.  **No Side Effects:** Tests using file I/O must use the `tmp_path` fixture 
    provided by pytest. Do not write to the real file system.
3.  **Fast:** The entire suite should run in under 2 seconds.

## 5. Execution Plan
1.  Add dependencies to `pyproject.toml`.
2.  Create `tests/conftest.py` to handle `sys.path` and common mocks.
3.  Create a pilot test for the `Skill` object (Low dependency, high value).
