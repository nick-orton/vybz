---
status: "Completed"
type: "Design"
last_updated: "2026-01-12"
references: designs/agent-skills-architecture.md
---

# Phase 1: Skills Infrastructure & Pilot Specification

## 1. High-Level Intent
Implement the foundational Python infrastructure required to support the new
"Skills" architecture. This involves creating a `Skill` domain object,
refactoring the `Agent` class to ingest referenced skills, and performing a
pilot migration by extracting the "Google GenAI SDK" context into a reusable
skill module. The goal is to prove the composition model works before migrating
the entire Squad.

## 2. User Stories
* As a System Maintainer, I want to define a `Skill` in a TOML file containing
  specific `knowledge` and `abilities` blocks, so that I can isolate technical
  context.
* As a Developer, I want the `Agent` object to automatically load and render
  these skills into the system prompt, so I don't have to manually copy-paste
  SDK rules into every agent definition.
* As a System, I want to ensure that if a referenced skill is missing, the Agent
  fails to load (fail-fast), preventing "brain-damaged" agents from running.

## 3. Acceptance Criteria
- [ ] **Module:** `src/vybz/skill.py` exists and defines the `Skill` dataclass.
- [ ] **Schema:** `Skill` objects support `name`, `description`, `knowledge`
      (List[str]), and `abilities` (List[str]).
- [ ] **Storage:** Directory `src/vybz/agents/skills/` exists.
- [ ] **Agent Refactor:** `Agent` class in `src/vybz/agent.py`:
    - [ ] Accepts an optional `skills` list in TOML (list of filenames).
    - [ ] Stores a list of `Skill` objects (not just strings).
    - [ ] `construct_agent_role_profile()` appends rendered skill text to the
          prompt.
- [ ] **Pilot Artifact:** `src/vybz/agents/skills/google-genai-v1-57.toml` is
      created containing the SDK rules currently found in `junior-dev.toml`.
- [ ] **Pilot Integration:** `src/vybz/agents/junior-dev.toml` is updated:
    - [ ] `skills = ["google-genai-v1-57"]` added.
    - [ ] Hardcoded SDK context removed from `operating_context`.
- [ ] **Verification:** The generated system prompt for `junior-dev` contains
      the SDK instructions.

## 4. Implementation Hints (Technical)

### 4.1. `src/vybz/skill.py`
```python
@dataclass
class Skill:
    id: str
    name: str
    description: str
    knowledge: List[str]  # Facts, Context, Constraints
    abilities: List[str]  # Instructions on how to perform tasks

    @classmethod
    def from_toml(cls, path: Path) -> "Skill":
        # Load TOML, validate fields
        pass
```

### 4.2. `src/vybz/agent.py` Refactor
*   **Dependency Injection:** The `Agent.from_toml` method currently instantiates
    the class directly. It needs to look up `Skill` objects.
*   **Loading Strategy:** To avoid circular dependencies with `Squad`, `Agent`
    can load skills directly if given a `skill_root_dir`, OR `Agent` stores
    skill *IDs* and resolves them at runtime.
    *   *Decision:* Let `Agent.from_toml` resolve them immediately. It can calculate the path `path.parent / "skills" / f"{skill_id}.toml"`.

### 4.3. Prompt Rendering Strategy
In `construct_agent_role_profile`:
```python
prompt = f"### ROLE SPECIFICATION\n{self.role_spec}\n\n"
# ... existing context ...

if self.skills:
    prompt += "### SKILLS & CAPABILITIES\n"
    for skill in self.skills:
        prompt += f"#### {skill.name}\n"
        for k in skill.knowledge:
            prompt += f"* {k}\n"
        for a in skill.abilities:
            prompt += f"* {a}\n"
        prompt += "\n"
```

## 5. Execution Plan
1.  [ ] **Create Infrastructure:** Create `src/vybz/skill.py` and `src/vybz/agents/skills/`.
2.  [ ] **Create Pilot Skill:** Extract GenAI rules from `junior-dev.toml` into
        `src/vybz/agents/skills/google-genai-v1-57.toml`.
3.  [ ] **Refactor Agent Class:** Update `agent.py` to handle skill loading and
        rendering.
4.  [ ] **Update Junior Dev:** Modify `junior-dev.toml` to use the new skill.
5.  [ ] **Verify:** Run a dummy `vybz junior-dev` session and check the logs to
        ensure the prompt includes the SDK rules.

