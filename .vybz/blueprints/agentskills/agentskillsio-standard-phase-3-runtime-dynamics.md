---
status: "Draft"
type: "Blueprint"
author: "Senior Python Architect"
last_updated: "2026-02-05"
references: designs/agentskills/agentskillsio-standard-phase-3-runtime.md, designs/agentskillsio-standard.md
---

# Agent Skills 2.0 - Phase 3: Runtime Dynamics Implementation

This blueprint details the implementation of dynamic skill management within the 
Vybz REPL. We will enable users to inspect, inject, and eject capabilities 
at runtime without modifying persistent configuration files.

## 1. Domain Updates: `src/vybz/agent.py`

We must enable the `Agent` dataclass to mutate its skill set.

### 1.1 Mutation Methods
*   **`add_skill(self, skill: Skill) -> None`**:
    *   Iterate `self.skills`. If a skill with the same `id` exists, replace it 
        (Update).
    *   Otherwise, append the new skill to the list.
*   **`remove_skill(self, skill_id: str) -> bool`**:
    *   Filter the `self.skills` list to remove the matching ID.
    *   Return `True` if a skill was actually removed, `False` otherwise.

## 2. Command Implementation: `src/vybz/commands/core.py`

We will implement three new command classes.

### 2.1 `SkillsCommand` (`/skills`)
*   **Purpose:** Visualize the active agent's capabilities.
*   **Logic:**
    1.  Get `active_agent` from `session.session_manager`.
    2.  Construct a `rich.table.Table`.
    3.  Columns: `ID`, `Name`, `Description`.
    4.  Populate rows from `active_agent.skills`.
    5.  Print to `ui.console`.

### 2.2 `UplevelCommand` (`/uplevel <path>`)
*   **Purpose:** Inject a local skill directory into the active agent.
*   **Logic:**
    1.  Validate `args[0]` exists.
    2.  Resolve `path = Path(args[0]).resolve()`.
    3.  Call `skill = Skill.from_directory(path)`.
    4.  Call `session.session_manager.active_agent.add_skill(skill)`.
    5.  Call `session.session_manager.refresh_context()`.
    6.  `ui.print_success(f"Skill '{skill.name}' injected and context refreshed.")`.

### 2.3 `DownlevelCommand` (`/downlevel <id>`)
*   **Purpose:** Remove a skill from the active agent.
*   **Logic:**
    1.  Call `removed = session.session_manager.active_agent.remove_skill(args[0])`.
    2.  If `removed`:
        *   Call `session.session_manager.refresh_context()`.
        *   `ui.print_success(f"Skill '{args[0]}' removed.")`.
    3.  Else: `ui.print_error(f"Skill '{args[0]}' not found on active agent.")`.

## 3. Integration: `src/vybz/commands/registry.py`

*   Update `initialize()` to register `SkillsCommand`, `UplevelCommand`, and 
    `DownlevelCommand`.

## 4. Senior Dev Peer Review

*   **Idempotency:** `add_skill` handles updates by ID, preventing the same 
    skill from appearing twice in the system prompt if `/uplevel` is run 
    repeatedly on the same path.
*   **UX:** Using a `Table` for `/skills` provides high information density 
    compared to simple bullet points.
*   **Persistence:** These changes are strictly in-memory. If the user 
    restarts `vybz`, the agent reverts to its TOML-defined skills. This is the 
    correct "Safe-to-Fail" experimentation model.
*   **Error Handling:** `UplevelCommand` must wrap the `from_directory` call 
    in a try/except to catch `ValueError` (name mismatch) or `FileNotFoundError` 
    and report them via `ui.print_error`.

## 5. Verification Script

```python
if __name__ == "__main__":
    from vybz.agent import Agent
    from vybz.skill import Skill
    from pathlib import Path

    # 1. Setup Mock Agent
    agent = Agent(
        id="test-agent", name="Tester", version="1",
        role_spec="", operating_context="", task_directive="",
        skills=[]
    )

    # 2. Setup Mock Skill
    skill = Skill(id="py-std", name="Python Standards", description="PEP 8", instructions="...")

    print("--- Testing Agent Mutation ---")
    
    # Test Add
    agent.add_skill(skill)
    print(f"[OK] Added Skill: {len(agent.skills) == 1}")

    # Test Update (Same ID)
    skill_v2 = Skill(id="py-std", name="Python Standards V2", description="PEP 8", instructions="...")
    agent.add_skill(skill_v2)
    print(f"[OK] Updated Skill (No Duplicates): {len(agent.skills) == 1}")
    print(f"[OK] Name Updated: {agent.skills[0].name == 'Python Standards V2'}")

    # Test Remove
    agent.remove_skill("py-std")
    print(f"[OK] Removed Skill: {len(agent.skills) == 0}")
```
```

---

### Senior Dev Peer Review

*   **Logic Check:** The `add_skill` logic specifically addresses the "Update" use case. This is vital for developers who are iteratively editing a `SKILL.md` and running `/uplevel` to see the changes.
*   **Security:** The `Path(args[0]).resolve()` step is important. It prevents any ambiguity about which directory is being loaded, especially if the user is deep in a subdirectory of the codebase.
*   **Consistency:** By triggering `refresh_context()` in both `uplevel` and `downlevel`, we guarantee that the very next prompt sent to the LLM will contain the updated skill instructions.

---

### Verification Script

This script validates that the `Agent` mutation logic is ready for implementation.

```python
import dataclasses
from typing import List

@dataclasses.dataclass
class MockSkill:
    id: str
    name: str

class MockAgent:
    def __init__(self, skills: List[MockSkill]):
        self.skills = skills

    def add_skill(self, skill: MockSkill) -> None:
        for i, s in enumerate(self.skills):
            if s.id == skill.id:
                self.skills[i] = skill
                return
        self.skills.append(skill)

    def remove_skill(self, skill_id: str) -> bool:
        orig_len = len(self.skills)
        self.skills = [s for s in self.skills if s.id != skill_id]
        return len(self.skills) < orig_len

if __name__ == "__main__":
    agent = MockAgent(skills=[])
    s1 = MockSkill("git", "Git Ops")
    s2 = MockSkill("git", "Git Ops V2")
    
    print("Test 1: Add Skill")
    agent.add_skill(s1)
    assert len(agent.skills) == 1
    print("  [PASS]")

    print("Test 2: Update Skill (ID Match)")
    agent.add_skill(s2)
    assert len(agent.skills) == 1
    assert agent.skills[0].name == "Git Ops V2"
    print("  [PASS]")

    print("Test 3: Remove Skill")
    agent.remove_skill("git")
    assert len(agent.skills) == 0
    print("  [PASS]")
