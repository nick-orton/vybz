---
status: "Completed"
type: "Design"
author: "PM Lead"
last_updated: "2026-02-03"
references: 
---

# Agent Skills 2.0: Adoption of AgentSkills.io Standard

## 1. High-Level Intent
Refactor the Vybz Skill architecture to align with the open standard defined by
[AgentSkills.io](https://agentskills.io). Currently, Vybz uses a proprietary 
TOML format for skills. We will migrate to the directory-based `SKILL.md` 
format (YAML Frontmatter + Markdown Body). This standardization enables 
portability, supports bundled resources (scripts/templates), and allows us to 
leverage external skill libraries. This project covers the core infrastructure 
refactor, data migration, runtime controls (`/uplevel`), and the enlightenment 
of the Advisor agent.

## 2. User Stories
* As a System Maintainer, I want skills to be self-contained directories 
  containing code, templates, and instructions, so I can package complex 
  capabilities (like "Git Operations") into a single portable unit.
* As a User, I want to dynamically inject a skill directory using 
  `/uplevel ./my-new-skill`, so I can test new capabilities without restarting 
  the REPL.
* As the Advisor Agent, I want a `skill-builder` skill that teaches me how to 
  generate valid `SKILL.md` files, so I can autonomously expand the squad's 
  capabilities.
* As a Developer, I want to list the active skills of an agent via 
  `/skills junior-dev` to verify context injection.

## 3. Architecture Specification

### 3.1. Directory Structure
We will transition from `src/vybz/agents/skills/*.toml` to a dedicated 
top-level package `src/vybz/skills/`.

```text
src/vybz/
├── agents/
│   └── junior-dev.toml (References skills by name)
└── skills/
    ├── python-standards/
    │   └── SKILL.md
    └── freebsd-posix/
        └── SKILL.md
```

### 3.2. The `SKILL.md` Standard
We strictly adhere to the specification:
*   **File:** `SKILL.md` inside a directory matching the skill name.
*   **Frontmatter:** YAML containing `name` and `description`.
*   **Body:** Markdown instructions injected into the Agent's context.

## 4. Execution Phases

### Phase 1: Core Infrastructure (The Reader)
**Goal:** Enable Vybz to parse and load the new Skill format alongside the 
legacy format (temporarily).
1.  **Refactor `src/vybz/skill.py`:**
    *   Update `Skill` dataclass to support `path` (directory root).
    *   Implement `from_directory(path: Path)` loader.
    *   Implement parsing of YAML frontmatter and Markdown body.
2.  **Refactor `src/vybz/agent.py`:**
    *   Update loading logic to look in `src/vybz/skills/` first, then fallback
        to legacy `agents/skills/`.
    *   Update `construct_agent_role_profile` to render the Markdown body of 
        the skill directly.

### Phase 2: The Great Migration
**Goal:** Convert all existing TOML skills to the new format and decommission 
          the old directory.
1.  **Migration Script:** Create a utility to read a TOML skill and generate 
    the directory structure.
    *   Map `knowledge` list -> `## Knowledge` section.
    *   Map `abilities` list -> `## Abilities` section.
2.  **Execution:** Migrate `python-standards`, `freebsd-posix`, 
    `google-genai-v1-57`, etc.
3.  **Cleanup:** Update all Agent TOML files to reference the new skills 
    (if ID changes) 
    * delete `.toml` skills.
    * remove code paths for leveraging legacy skills
    * clean testing
    * post-cleanup refactoring of the code

### Phase 3: Runtime Dynamics (REPL Controls)
**Goal:** Empower the user to inspect and modify agent skills during a session.
1.  **Command `/skills [agent]`:**
    *   Lists loaded skills for the active (or target) agent.
    *   Displays Name and Description from metadata.
2.  **Command `/uplevel <path>`:**
    *   Accepts a path to a skill directory.
    *   Validates `SKILL.md` existence.
    *   Dynamically loads the `Skill` object.
    *   Appends it to the active Agent's skill list.
    *   Triggers a **Context Refresh** (`/update` logic) to inject the new 
        instructions immediately.
3.  **Command `/downlevel <skill>`:**
    *   Drops the skill from the agent's context
    *   Removes it from the skill list
    *   Triggers a **Context Refresh**

### Phase 4: The Skill Builder
**Goal:** Teach the Advisor how to extend the system.
1.  **Create `skill-builder` Skill:**
    *   A new skill in `src/vybz/skills/skill-builder/`.
    *   **Knowledge:** The AgentSkills.io specification, YAML rules, directory 
        structure requirements.
    *   **Abilities:** Instructions on how to draft `SKILL.md` files and where 
        to save them.
2.  **Update Advisor:**
    *   Attach `skill-builder` to the Advisor agent.
    *   Update Advisor's system prompt to prefer creating Skills over 
        monolithic Agent prompts.
3.  **Extended Cleanup:***
    *   Work with librarian to identify and remove all designs and blueprints
        referencing legacy skills.
    *   Do an E2E code base critique by the Senior Architect to look for
        opportunities to clean the code
4.  **Documentation**
    *   Update the readme to point to the agentskills.io specification as well
        as this design.

## 5. High-Level Test Plan

### 5.1. Unit Tests (`tests/vybz/test_skill_v2.py`)
- [ ] **Parse Valid Skill:** Verify `from_directory` correctly extracts `name`,
      `description`, and body content.
- [ ] **Missing Metadata:** Verify failure if `name` is missing in YAML.
- [ ] **Structure Mismatch:** Verify failure if directory name does not match 
      `name` (optional spec recommendation).

### 5.2. Integration Tests
- [ ] **Agent Loading:** Verify `junior-dev` loads successfully with migrated 
      skills.
- [ ] **Prompt Rendering:** Verify the final system prompt contains the 
      Markdown body of the skills.

### 5.3. Manual QA (REPL)
- [ ] **List:** Run `/skills`. Expect table output of loaded skills.
- [ ] **Uplevel:**
    1. Create a dummy skill `src/vybz/skills/joke-teller/SKILL.md`.
    2. Run `/uplevel src/vybz/skills/joke-teller`.
    3. Ask agent to tell a joke.
    4. Verify agent complies (Context was refreshed).

## 6. Acceptance Criteria
- [ ] Legacy `src/vybz/agents/skills/*.toml` files are deleted.
- [ ] New `src/vybz/skills/` directory contains all migrated skills.
- [ ] `vybz junior-dev` starts without errors.
- [ ] `/skills` command lists active skills.
- [ ] `/uplevel` successfully injects a new skill at runtime.
- [ ] The Advisor agent can generate a valid `SKILL.md` file when asked.
