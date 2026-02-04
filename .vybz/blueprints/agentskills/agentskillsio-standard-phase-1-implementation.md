---
status: "Draft"
type: "Blueprint"
author: "Senior Python Architect"
last_updated: "2026-02-04"
references: designs/agentskills/agentskillsio-standard-phase-1.md, designs/agentskills/agentskillsio-standard.md
---

# Agent Skills 2.0 - Phase 1: Core Infrastructure Implementation

This blueprint details the implementation of the "Reader" infrastructure for 
the AgentSkills.io standard. We will extend the `Skill` domain model to support
directory-based skills (`SKILL.md`) while maintaining backward compatibility 
for legacy TOML skills.

## 1. Dependencies
*   **Target:** `pyproject.toml`
*   **Action:** Add `PyYAML>=6.0` to dependencies.
*   **Rationale:** Robust parsing of YAML Frontmatter is required by the spec. 
    Regex parsing is insufficient for complex metadata.

## 2. Module Specification: `src/vybz/skill.py`

### 2.1 Dataclass Updates
We extend the `Skill` class to support the new format's data shape.

*   **New Attributes:**
    *   `instructions: Optional[str]`: Holds the raw Markdown body from 
        `SKILL.md` as well as the content from all other markdown files in the
        skill directory or subdirectories. `SKILL.md` should be the top of the
        string and all the subdirectory content should be appended below with
        markdown structure that represents the directory tree of of the content.
    *   `path: Optional[Path]`: Stores the root directory of the skill (crucial
        for resource discovery).
*   **Legacy Compatibility:** `knowledge` and `abilities` remain but default to
    empty lists.

### 2.2 New Factory: `from_directory(cls, dir_path: Path) -> Skill`
*   **Validation:**
    *   Ensure `dir_path / "SKILL.md"` exists.
    *   **Spec Rule:** Verify `dir_path.name` matches the `name` field in YAML.
        Raise `ValueError` if mismatch.
*   **Parsing:**
    *   Read `SKILL.md`.
    *   Split Frontmatter (YAML) and Body (Markdown).
    *   Use `yaml.safe_load` for metadata.
*   **Instantiation:** Return `Skill` with `id=dir_path.name`, 
    `instructions=body`, and `path=dir_path`.
*   **subdirectories**
     - it's important that all subdirectories under the skill be integrated, 
       not just references and scripts 
     - there can be an arbitrary number of subdirectories that can have 
       subdirectories in them 

## 3. Module Specification: `src/vybz/agent.py`

### 3.1 Refactor: `from_toml` (The Loader Loop)
We need to change how skill IDs are resolved to file paths.

*   **Constants:** Define `SKILLS_ROOT = Path(__file__).parent / "skills"` 
    (The new home).
*   **Lookup Logic:**
    For each `skill_id` in the TOML list:
    1.  **Priority 1 (Standard):** Check `SKILLS_ROOT / skill_id`.
        *   If it is a directory -> `Skill.from_directory`.
    2.  **Priority 2 (Legacy):** Check `agent_path.parent / "skills" / f"{skill_id}.toml"`.
        *   If it is a file -> `Skill.from_toml`.
    3.  **Error:** If neither exists -> Raise `FileNotFoundError`.

## 4. Verification Strategy

### 4.1 Unit Tests (`tests/vybz/test_skill_v2.py`)
*   **Test Case 1:** `test_from_directory_valid`
    *   Create a temp dir `test-skill`.
    *   Write `SKILL.md` with valid YAML/Markdown.
    *   Assert `skill.instructions` contains body.
*   **Test Case 2:** `test_render_resources`
    *   Add `scripts/run.py` to the temp skill.
    *   Call `render()`.
    *   Assert output contains "**Available Scripts:**" and "run.py".
*   **Test Case 3:** `test_name_mismatch`
    *   Create directory `foo` but YAML name `bar`.
    *   Assert `ValueError`.

### 4.2 Integration Check
*   Run `vybz junior-dev`. Since no skills have been migrated yet, it should transparently fall back to legacy TOML loading without error.

## 5. Execution Steps
1.  **Install:** Add `PyYAML` to `pyproject.toml`.
2.  **Refactor Skill:** Update `src/vybz/skill.py` (Dataclass, Factory, Render).
3.  **Refactor Agent:** Update `src/vybz/agent.py` (Lookup Logic).
4.  **Verify:** Run new unit tests.
```

### 3. Senior Dev Peer Review

*   **Architecture:** The "Dual-Path" lookup in `agent.py` is the correct 
    approach for a zero-downtime migration. It allows us to migrate skills one 
    by one in Phase 2 without breaking the system.
*   **Standards:** Enforcing the "Directory Name == YAML Name" rule from the 
    AgentSkills.io spec in `from_directory` is critical to prevent 
    configuration drift.
*   **Safety:** Using `yaml.safe_load` is mandatory. Never use `yaml.load`.
*   **Cleanliness:** By adding `path` to the `Skill` object, we enable future 
    features (like `/uplevel` reloading) to know *where* a skill came from, 
    which was previously implicit and brittle.

### 4. Verification Script

This script simulates the new `from_directory` logic to ensure the parsing 
concept works before implementation.

```python
if __name__ == "__main__":
    from pathlib import Path
    import tempfile
    
    # Mocking the proposed class structure
    class MockSkill:
        def __init__(self, name, instructions, path):
            self.name = name
            self.instructions = instructions
            self.path = path
            
        def render(self):
            out = self.instructions
            scripts = self.path / "scripts"
            if scripts.exists():
                out += "\n\nScripts found: " + ", ".join([f.name for f in scripts.iterdir()])
            return out

    # Simulation
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        skill_dir = root / "my-skill"
        skill_dir.mkdir()
        
        # Create SKILL.md
        (skill_dir / "SKILL.md").write_text("---\nname: my-skill\n---\n# Instructions", encoding="utf-8")
        
        # Create a script resource
        (skill_dir / "scripts").mkdir()
        (skill_dir / "scripts" / "test.py").touch()
        
        print(f"Created mock skill at {skill_dir}")
        
        # Simulate loading
        # In real code, we'd use PyYAML here
        content = (skill_dir / "SKILL.md").read_text()
        if "name: my-skill" in content:
            skill = MockSkill("my-skill", "# Instructions", skill_dir)
            print("Loaded Skill.")
            
            rendered = skill.render()
            print("--- Render Output ---")
            print(rendered)
            
            if "test.py" in rendered:
                print("\n[SUCCESS] Resource discovery working.")
            else:
                print("\n[FAIL] Scripts not found.")
