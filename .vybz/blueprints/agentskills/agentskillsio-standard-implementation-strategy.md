---
status: "Draft"
type: "Blueprint"
author: "Senior Python Architect"
last_updated: "2026-02-04"
references: designs/agentskillsio-standard.md
---

# AgentSkills.io Standard Implementation Strategy

This blueprint outlines the high-level architecture and phased execution plan 
to migrate the Vybz Skill system to the industry-standard **AgentSkills.io** 
format (`SKILL.md` directories).

## 1. Architectural Vision

We are transitioning from a proprietary, static configuration model to an open, 
portable, and dynamic capability model.

### 1.1 The Domain Shift
*   **Legacy (v1):** A Skill is a TOML configuration file containing lists of 
    strings (`knowledge`, `abilities`).
*   **Standard (v2):** A Skill is a **Directory** containing a `SKILL.md` file.
    *   **Metadata:** Defined in YAML Frontmatter (`name`, `description`).
    *   **Instruction:** Defined in the Markdown body.
    *   **Resources:** Optional `scripts/` or `templates/` subdirectories 
        (future-proofing).

### 1.2 Directory Structure
```text
src/vybz/
├── agents/                 # Agent TOML definitions
└── skills/                 # NEW: Top-level Skills Package
    ├── python-standards/
    │   └── SKILL.md
    └── git-operations/
        └── SKILL.md
```

## 2. Implementation Phases

### Phase 1: Core Infrastructure (The Bridge)
**Goal:** Enable the system to read the new format *without* breaking the old 
one.
*   **Dependency:** Add `PyYAML` to `pyproject.toml`.
*   **Refactor `src/vybz/skill.py`:**
    *   Implement `Skill.from_directory(path)`.
    *   Add `instructions` attribute to the dataclass (holds the Markdown body).
    *   Update `render()` to prioritize `instructions` if present, falling back
        to legacy lists.
*   **Refactor `src/vybz/agent.py`:**
    *   Implement a **Dual-Path Loader**: Check `src/vybz/skills/{id}` first; 
        if missing, check legacy `agents/skills/{id}.toml`.

### Phase 2: The Great Migration (The Switch)
**Goal:** Convert data and remove technical debt.
*   **Migration Script:** Create `scripts/migrate_skills.py` to automate the 
    conversion of TOML -> `SKILL.md`.
    *   *Logic:* Convert `knowledge` lists into `## Knowledge` markdown 
        sections.
*   **Execution:** Run migration for all core skills.
*   **Cleanup:**
    *   Delete `src/vybz/agents/skills/` (Legacy directory).
    *   Remove `tomllib` dependency from `skill.py`.
    *   Remove fallback logic from `agent.py`.

### Phase 3: Runtime Dynamics (The Flow)
**Goal:** Enable "Hot-Swapping" of capabilities in the REPL.
*   **New Commands:**
    *   `/skills`: List active skills for the current agent.
    *   `/uplevel <path>`: Load a local skill directory and inject it into the 
        active session.
    *   `/downlevel <id>`: Remove a skill from the active session.
*   **State Management:** Update `SessionManager` to trigger a 
    **Context Refresh** (re-generating system instructions) whenever skills are 
    modified.

### Phase 4: Advisor Enlightenment (The Meta)
**Goal:** Empower the AI to extend itself.
*   **New Skill:** `src/vybz/skills/skill-creator/SKILL.md`.
    *   Contains the AgentSkills.io specification and Vybz naming conventions.
*   **Advisor Update:** Equip the Advisor with `skill-creator`.
*   **Documentation:** Update all Blueprints/Designs to reference the new 
    structure.

## 3. Technical Constraints & Standards

### 3.1 Naming Conventions
*   **Directory Name:** Must match the `name` field in YAML exactly.
*   **Format:** Kebab-case (e.g., `docker-management`), lowercase, alphanumeric.

### 3.2 Parsing Robustness
*   We strictly use `PyYAML` for frontmatter parsing to ensure spec compliance.
*   We assume the `SKILL.md` file is UTF-8 encoded.

### 3.3 Persistence
*   Runtime changes via `/uplevel` are **Ephemeral** (In-Memory only). They do 
    not modify the Agent's source TOML file.
*   To make changes permanent, the user (or Advisor) must edit the Agent TOML.

## 4. Verification Strategy
*   **Unit Tests:** Verify `Skill.from_directory` correctly parses YAML/Markdown.
*   **Integration:** Verify `vybz junior-dev` loads successfully after Phase 2.
*   **Manual:** Verify `/uplevel` changes the agent's behavior immediately.
```

### 3. Senior Dev Peer Review

*   **Pattern:** The "Parallel Change" (Phase 1 -> Phase 2) is the correct 
    approach for a refactor of this magnitude. It minimizes downtime.
*   **Dependencies:** Adding `PyYAML` is necessary. While `tomllib` is stdlib 
    in 3.11, YAML is not, and regex parsing of YAML is dangerous.
*   **State:** The distinction between "Ephemeral Runtime Skills" (Phase 3) and
    "Persistent Configuration" is crucial. We must ensure `/uplevel` doesn't 
    accidentally overwrite source files, keeping the REPL safe for 
    experimentation.

### 4. Verification Script

This script verifies that we can parse the proposed `SKILL.md` format using 
standard Python string manipulation (simulating the logic before `PyYAML` is 
installed).

```python
if __name__ == "__main__":
    # Simulating the target format
    mock_skill_content = """---
name: test-skill
description: A test skill
---
# Instructions
Do the thing.
"""
    
    print("--- Simulating SKILL.md Parsing ---")
    
    # 1. Split Frontmatter
    parts = mock_skill_content.split("---", 2)
    
    if len(parts) == 3:
        frontmatter = parts[1].strip()
        body = parts[2].strip()
        
        print(f"[OK] Frontmatter extracted: {len(frontmatter)} chars")
        print(f"[OK] Body extracted: {len(body)} chars")
        
        if "name: test-skill" in frontmatter:
            print("[OK] Name found in YAML block")
        if "# Instructions" in body:
            print("[OK] Markdown body preserved")
    else:
        print("[FAIL] Could not split file correctly")
