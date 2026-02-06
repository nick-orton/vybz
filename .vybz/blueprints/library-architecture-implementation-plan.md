---
status: "Draft"
type: "Blueprint"
author: "Senior Python Architect"
last_updated: "2026-02-06"
references: designs/library.md
---

# Library Architecture Implementation Plan

This blueprint details the structural refactoring of the Vybz codebase to 
introduce a `Library` domain object. This object centralizes the discovery and 
loading of Agents and Skills, decoupling file system paths from core logic and 
enabling a layered configuration system (User overrides System).

## 1. Architectural Deviation Note
The Design specifies moving agents/skills to the **project root**. However, to 
ensure robust Python packaging and reliable distribution via `pip` (ensuring 
defaults exist in `site-packages`), we will move them to `src/vybz/library/`. 
This keeps "System Defaults" inside the package boundary while still achieving 
the goal of centralizing resources. User overrides will still live in 
`~/.config`.

## 2. File Structure Changes

### 2.1 Repository Restructure
*   **Create:** `src/vybz/library/`
*   **Move:** `src/vybz/agents/` -> `src/vybz/library/agents/`
*   **Move:** `src/vybz/skills/` -> `src/vybz/library/skills/`
*   **Update:** `pyproject.toml` to package `src/vybz/library`.

## 3. Module Specification: `src/vybz/library.py`

### 3.1 Class: `Library`
A service class responsible for resource discovery.

*   **Attributes:**
    *   `search_paths: List[Path]`: Ordered list of roots to scan.
*   **Constructor:**
    *   Args: `custom_root: Optional[Path]`.
    *   Logic: Build `search_paths`.
        1.  `custom_root` (if provided).
        2.  `$XDG_CONFIG_HOME/vybz/library` (User).
        3.  `Path(__file__).parent / "library"` (System Defaults).
*   **Methods:**
    *   `list_agents() -> List[str]`: Scans all search paths for 
        `agents/*.toml`. Returns unique sorted list (User shadows System).
    *   `get_agent_path(agent_id: str) -> Path`: Returns the first matching 
        path. Raises `FileNotFoundError`.
    *   `get_skill_path(skill_id: str) -> Path`: Scans 
        `skills/{skill_id}/SKILL.md`. Returns directory path.

## 4. Refactoring Core Modules

### 4.1 `src/vybz/squad.py`
*   **Update:** Remove hardcoded `_source_dir`.
*   **Dependency:** Instantiate `Library` (using config from `vybz.config`).
*   **Method `get_agent`:**
    1.  Call `library.get_agent_path(name)`.
    2.  Pass the `library` instance to `Agent.from_toml` (Dependency 
        Injection).

### 4.2 `src/vybz/agent.py`
*   **Update `from_toml`:**
    *   Signature: `from_toml(path: Path, library: Library)`.
    *   Logic: When parsing `skills = ["foo"]`, call 
        `library.get_skill_path("foo")` instead of assuming a relative path.

## 5. CLI Integration

### 5.1 `src/vybz/tools/work.py`
*   **Argparse:** Add `--library <path>`.
*   **Config:** Pass this path to `Squad` / `Library` initialization.
*   **New Command:** `vybz --init-library`
    *   Logic: Copies `src/vybz/library` contents to `~/.config/vybz/library`, 
        skipping existing files.

## 6. Execution Steps

1.  **Restructure:** Move directories and update `pyproject.toml`.
2.  **Implement Library:** Create `src/vybz/library.py`.
3.  **Refactor Agent:** Update `Agent.from_toml` to accept `Library`.
4.  **Refactor Squad:** Update `Squad` to use `Library`.
5.  **Update CLI:** Wire up `--library` and initialization logic.
6.  **Verify:** Run tests.

## 7. Verification Strategy

### 7.1 Unit Tests
*   **Test:** `test_library_discovery_order`: Mock filesystem, ensure User file 
    shadows System file.
*   **Test:** `test_agent_load_with_library`: Ensure Agent can resolve a skill 
    via the Library.

```

### 3. Senior Dev Peer Review
*   **Packaging:** Moving the "System Defaults" into `src/vybz/library` is the 
    correct engineering decision. Placing them at the repo root would require 
    `MANIFEST.in` gymnastics and often fails in `pip install` scenarios, 
    leading to "FileNotFound" errors for end users.
*   **Dependency Injection:** Passing `Library` into `Agent.from_toml` is 
    crucial. It avoids global state and makes the Agent testable (we can pass 
    a MockLibrary).
*   **Backward Compatibility:** We must ensure that if the user *doesn't* have 
    a config, the System Default path resolves correctly relative to `__file__`.

### 4. Verification Script
This script simulates the `Library` discovery logic.

```python
if __name__ == "__main__":
    from pathlib import Path
    import tempfile
    import os

    # Mocking the Library Class Logic
    class MockLibrary:
        def __init__(self, user_root: Path | None, system_root: Path):
            self.roots = []
            if user_root: self.roots.append(user_root)
            self.roots.append(system_root)

        def get_agent_path(self, name: str) -> Path:
            for root in self.roots:
                candidate = root / "agents" / f"{name}.toml"
                if candidate.exists():
                    return candidate
            raise FileNotFoundError(name)

    # Simulation
    with tempfile.TemporaryDirectory() as sys_dir, tempfile.TemporaryDirectory() as user_dir:
        sys_path = Path(sys_dir)
        user_path = Path(user_dir)

        # Setup System Default
        (sys_path / "agents").mkdir()
        (sys_path / "agents" / "junior.toml").write_text("sys")

        # Setup User Override
        (user_path / "agents").mkdir()
        (user_path / "agents" / "junior.toml").write_text("user")

        # Test 1: Priority
        lib = MockLibrary(user_path, sys_path)
        found = lib.get_agent_path("junior")
        print(f"Found: {found.read_text()}")
        assert found.read_text() == "user"
        print("[PASS] User overrides System")

        # Test 2: Fallback
        (sys_path / "agents" / "senior.toml").write_text("sys_senior")
        found_senior = lib.get_agent_path("senior")
        assert found_senior.read_text() == "sys_senior"
        print("[PASS] Fallback to System")
