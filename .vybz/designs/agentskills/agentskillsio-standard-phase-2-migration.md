---
status: "Draft"
type: "Design"
author: "PM Lead"
last_updated: "2026-02-04"
references: designs/agent-skills-20---phase-1-core-infrastructure-specification.md, designs/agentskillsio-standard.md
---

# Agent Skills 2.0 - Phase 2: Migration & Cleanup Specification

## 1. High-Level Intent
Execute "The Great Migration" of all existing Vybz skills from the legacy TOML 
format to the new `SKILL.md` directory standard. Once data migration is 
verified, we will decommission the legacy infrastructure (the `agents/skills/` 
directory and the TOML parsing logic within the `Skill` class). This phase 
enforces the new standard and pays down the technical debt introduced by the 
Phase 1 "Dual-Path" bridge.

## 2. User Stories
* As a System Maintainer, I want an automated script to convert existing TOML 
  skills into `SKILL.md` format, preserving all `knowledge` and `abilities` 
  text, so that I don't have to manually copy-paste and reformat strings.
* As a Developer, I want to remove the legacy `knowledge` and `abilities` list 
  attributes from the `Skill` domain object, simplifying the class to strictly 
  reflect the AgentSkills.io schema (Metadata + Instruction Body).
* As the System, I want to enforce that skills *must* live in 
  `src/vybz/skills/`, reducing path resolution complexity.

## 3. Acceptance Criteria
- [ ] **Migration Utility:** A script `scripts/migrate_skills.py` exists and 
      successfully converts all TOML files in `src/vybz/agents/skills/` to 
      directory-based `SKILL.md` files in `src/vybz/skills/`.
- [ ] **Content Fidelity:** The generated `SKILL.md` files contain:
    - [ ] Correct YAML Frontmatter (`name`, `description`).
    - [ ] A Markdown body where legacy `knowledge` and `abilities` lists are 
      converted into formatted Markdown sections (e.g., `## Knowledge`).
- [ ] **Agent Configuration:** All Agent TOML files (`src/vybz/agents/*.toml`) 
      are updated if necessary (though if IDs match, no change may be needed).
- [ ] **Legacy Removal:**
    - [ ] Directory `src/vybz/agents/skills/` is deleted.
    - [ ] `src/vybz/skill.py`: `from_toml` method is removed.
    - [ ] `src/vybz/skill.py`: `knowledge` and `abilities` list attributes are 
          removed from the dataclass.
    - [ ] `src/vybz/agent.py`: The fallback lookup logic for TOML files is 
          removed.
- [ ] **Verification:** `vybz junior-dev` launches successfully, and the system
      prompt contains the skill instructions.

## 4. Implementation Hints (Technical)

### 4.1 Migration Script Logic (`scripts/migrate_skills.py`)
This script is a one-time tool.
1.  **Iterate:** `src/vybz/agents/skills/*.toml`.
2.  **Parse:** Load TOML data.
3.  **Format Body:**
    ```python
    body = f"# {data['name']}\n\n"
    if data.get('knowledge'):
        body += "## Knowledge\n"
        for k in data['knowledge']:
            body += f"* {k}\n"
        body += "\n"
    if data.get('abilities'):
        body += "## Abilities\n"
        for a in data['abilities']:
            body += f"* {a}\n"
    ```
4.  **Format Frontmatter:**
    # Note: Ensure data['name'] is normalized to lowercase/kebab-case for the directory
    ```yaml
    ---
    name: {data['name']}
    description: {data['description']}
    ---
    ```
5.  **Write:**
    *   Normalize name: `safe_name = re.sub(r'[^a-z0-9-]', '', data['name'].lower().replace(' ', '-'))`
    *   Create directory: `src/vybz/skills/{safe_name}/`
    *   Write `SKILL.md`

### 4.2 Refactor: `src/vybz/skill.py` (Cleanup)
The `Skill` class should be stripped down to match the new reality.

**Current (Phase 1 Bridge):**
```python
@dataclass
class Skill:
    knowledge: List[str]
    abilities: List[str]
    instructions: str | None
```

**Target (Phase 2 Final):**
```python
@dataclass
class Skill:
    id: str
    name: str
    description: str
    instructions: str  # The entire body content

    # Remove from_toml method entirely
    # Remove render logic that iterates lists
    def render(self) -> str:
        return f"{self.instructions}" 
```

### 4.3 Refactor: `src/vybz/agent.py` (Cleanup)
Simplify the `from_toml` loading loop.
*   **Remove:** The `legacy_skills_root` path calculation.
*   **Remove:** The `if candidate_toml.exists():` block.
*   **Assert:** Only check `src/vybz/skills/{id}`.

## 5. Execution Plan

1.  [ ] **Create Migration Script:** Implement `scripts/migrate_skills.py`.
2.  [ ] **Execute Migration:** Run the script. Verify `src/vybz/skills/` is 
        populated.
3.  [ ] **Verify Agents:** Run `vybz junior-dev` (Phase 1 code should pick up 
        the new skills if they exist first).
4.  [ ] **Code Cleanup (Refactor):**
    *   Modify `src/vybz/skill.py` (Remove legacy fields/methods).
    *   Modify `src/vybz/agent.py` (Remove legacy lookup).
5.  [ ] **Delete Legacy Data:** `rm -rf src/vybz/agents/skills/`.
6.  [ ] **Update Tests:** Rewrite `tests/vybz/test_skill.py` to test *only* the
        `from_directory` path and remove TOML tests.

## 6. End-of-Phase Refactoring Directive
*   **Objective:** Ensure no "dead code" remains from the transition.
*   **Checklist:**
    1.  Scan `src/vybz/` for any usage of `tomllib` related to *Skills* (Agents
        still use TOML, so don't remove the import from `agent.py`).
    2.  Ensure `Skill.render()` is efficient and doesn't do unnecessary string 
        concatenation if `instructions` is the only source.
    3.  Verify that `conftest.py` fixtures creating temp skills use the new 
        directory structure.
