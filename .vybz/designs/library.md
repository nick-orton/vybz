---
status: "Completed"
type: "Design"
author: "PM Lead"
last_updated: "2026-02-06"
references: intents/library.md 
---

# Agents and Skills Library Architecture Specification

## 1. High-Level Intent
Restructure the Vybz codebase to decouple Agent and Skill definitions from the
core application logic. Currently, these TOML and Markdown files are buried
deep within `src/vybz/`, making them difficult for users to locate and modify.
We will move these definitions to the project root for visibility and implement
a `Library` domain object. This object will manage the discovery of resources,
supporting a layered architecture where User Definitions (in `~/.config`)
override System Defaults (in `site-packages`).

## 2. User Stories
* As a User, I want to edit `junior-dev.toml` without digging into Python
  package directories, so I can tweak the prompts easily.
* As a User, I want to create my own custom agents in
  `~/.config/vybz/library/agents/` and have them appear in the list alongside
  the built-in squad.
* As a Developer, I want the system to load Agents and Skills from a
  configurable path, so I can point `vybz` at a shared team repository of
  capabilities.

## 3. Acceptance Criteria
- [ ] **Repository Restructure:** `src/vybz/agents/` is moved to `agents/` (root).
- [ ] **Repository Restructure:** `src/vybz/skills/` is moved to `skills/` (root).
- [ ] **Build Configuration:** `pyproject.toml` is updated to package these root
      directories into `vybz.library` within the distribution wheel.
- [ ] **Domain Object:** A new class `Library` is implemented in `src/vybz/library.py`.
- [ ] **Discovery Logic:** The `Library` scans paths in this order (User overrides System):
      1. CLI `--library` argument (if provided).
      2. Config file `library` path (if defined).
      3. `$XDG_CONFIG_HOME/vybz/library/` (User Custom).
      4. `package_install_location/library/` (System Defaults).
- [ ] **Refactoring:** `Squad` and `Agent` classes delegate file finding to `Library`.
- [ ] **Provisioning:** A command `vybz --init-library` copies default agents to
      the user config directory for customization.

## 4. Implementation Hints (Technical)

### 4.1. Directory Layout Change
*   Move `src/vybz/agents` -> `./library/agents`
*   Move `src/vybz/skills` -> `./library/skills`
*   Update `pyproject.toml` to include `library` as package data or a sub-package.

### 4.2. The `Library` Class (`src/vybz/library.py`)
This class replaces the hardcoded path logic in `Squad` and `Agent`.

```python
class Library:
    def __init__(self, user_root: Path | None = None):
        self.roots = self._resolve_roots(user_root)

    def get_agent_path(self, agent_id: str) -> Path:
        # Check roots in priority order
        for root in self.roots:
            candidate = root / "agents" / f"{agent_id}.toml"
            if candidate.exists(): return candidate
        raise FileNotFoundError(...)

    def list_agents(self) -> List[str]:
        # Merge sets of agents from all roots
        pass
```

### 4.3. Configuration Update
*   Update `src/vybz/config.py` to allow a `library` key in `vybzrc`.
*   Update `src/vybz/tools/work.py` to accept `--library <path>`.

## 5. Execution Plan
1. [ ] **Restructure Repo:** Create `library/` root folder. Move `agents` and
       `skills` into it. Update `pyproject.toml`.
2. [ ] **Implement Library:** Create `src/vybz/library.py` with discovery and
       layering logic.
3. [ ] **Refactor Squad:** Update `src/vybz/squad.py` to instantiate `Library`.
4. [ ] **Refactor Agent:** Update `src/vybz/agent.py` to use `Library` for
       skill resolution.
5. [ ] **CLI Updates:** Add `--library` flag and `--init-library` utility.
6. [ ] **Verify:** Test loading a built-in agent and a custom user agent.
