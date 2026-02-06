---
status: "Draft"
type: "Design"
author: "PM Lead"
last_updated: "2026-02-04"
references: designs/agentskills/agentskillsio-standard.md, designs/agentskills/agentskillsio-standard-phase-1.md
---

# Agent Skills 2.0 - Phase 3: Runtime Dynamics Specification

## 1. High-Level Intent
Implement dynamic runtime controls for Agent Skills within the REPL. Currently,
an agent's capabilities are fixed at startup based on their TOML definition.
This phase introduces commands to Inspect (`/skills`), Inject (`/uplevel`), and
Eject (`/downlevel`) skills during an active session. This enables a rapid
"Hot-Swap" development loop where users can draft a new skill locally and test
it immediately without restarting the application.

## 2. User Stories
* As a User, I want to type `/skills` to see a clear table of what the current
  agent knows, so I can verify that my context injection worked.
* As a Developer, I want to run `/uplevel ./new-skill-dir` to add a local
  skill to the active agent and immediately use it, speeding up the skill
  authoring process.
* As a User, I want to run `/downlevel <skill-id>` to remove a distracting or
  conflicting skill from the context window.
* As a System, I want these changes to be **ephemeral** (in-memory only), so I
  don't accidentally corrupt the permanent agent definitions on disk.

## 3. Acceptance Criteria
- [ ] **Agent Domain Update:** `Agent` class supports `add_skill(skill)` and
      `remove_skill(skill_id)` methods.
- [ ] **Command `/skills`:**
    - Lists skills for the active agent (default) or a specified agent arg.
    - Renders a Rich Table showing ID, Name, and Description.
- [ ] **Command `/uplevel <path>`:**
    - Validates path exists and contains `SKILL.md`.
    - Loads the skill using `Skill.from_directory`.
    - Adds/Updates the skill in the active Agent's memory.
    - Triggers `session_manager.refresh_context()`.
    - Reports success/failure to UI.
- [ ] **Command `/downlevel <id>`:**
    - Removes the skill by ID from the active Agent.
    - Triggers `session_manager.refresh_context()`.
    - Reports success/failure.
- [ ] **Persistence:** Changes made via these commands do NOT modify the
      source `.toml` files in `src/vybz/agents/`.

## 4. Implementation Hints (Technical)

### 4.1. Refactor: `src/vybz/agent.py`
The `Agent` class needs methods to mutate its `skills` list.

```python
def add_skill(self, skill: Skill) -> None:
    # Check if skill exists (by ID) and update, or append
    for i, s in enumerate(self.skills):
        if s.id == skill.id:
            self.skills[i] = skill
            return
    self.skills.append(skill)

def remove_skill(self, skill_id: str) -> bool:
    # Filter list, return True if something was removed
    original_len = len(self.skills)
    self.skills = [s for s in self.skills if s.id != skill_id]
    return len(self.skills) < original_len
```

### 4.2. New Commands: `src/vybz/commands/core.py`

**SkillsCommand (`/skills`)**
*   **Args:** Optional `[agent_name]`.
*   **Logic:**
    1.  Resolve target agent (Active or lookup via Squad).
    2.  Build a `rich.table.Table`.
    3.  Columns: "ID", "Name", "Description".
    4.  Print via `ui.console.print(table)`.

**UplevelCommand (`/uplevel`)**
*   **Args:** Required `<path>`.
*   **Logic:**
    1.  Resolve path (`Path(args[0]).resolve()`).
    2.  `skill = Skill.from_directory(path)`.
    3.  `session.session_manager.active_agent.add_skill(skill)`.
    4.  `session.session_manager.refresh_context()`.
    5.  `ui.print_success(f"Injected skill: {skill.name}")`.

**DownlevelCommand (`/downlevel`)**
*   **Args:** Required `<skill_id>`.
*   **Logic:**
    1.  `success = agent.remove_skill(args[0])`.
    2.  If success:
        *   `session.session_manager.refresh_context()`.
        *   `ui.print_success(...)`.
    3.  Else: `ui.print_error("Skill not found")`.

## 5. Execution Plan
1.  [ ] **Update Agent:** Add mutation methods to `src/vybz/agent.py`.
2.  [ ] **Implement Commands:** Add `SkillsCommand`, `UplevelCommand`,
        `DownlevelCommand` to `src/vybz/commands/core.py`.
3.  [ ] **Register Commands:** Update `src/vybz/commands/registry.py`.
4.  [ ] **Verify:**
        *   Launch REPL.
        *   `/skills` -> List default skills.
        *   `/uplevel src/vybz/skills/python-standards` (Reload existing).
        *   `/downlevel python-standards`.
        *   `/skills` -> Verify it's gone.
