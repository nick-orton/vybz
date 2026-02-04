---
status: "Draft"
type: "Design"
author: "PM Lead"
last_updated: "2026-02-04"
references: designs/agentskillsio-standard.md
---

# Agent Skills 2.0 - Phase 1: Core Infrastructure Specification

## 1. High-Level Intent
Implement the "Reader" infrastructure required to support the AgentSkills.io
standard. This phase focuses on extending the `Skill` domain object to parse
directory-based skills (`SKILL.md` with YAML Frontmatter) while maintaining
backward compatibility with the legacy TOML format. Crucially, it implements
**Resource Discovery**: ensuring that if a skill includes auxiliary files (in
`scripts/` or `references/`), the Agent is made aware of their existence within
the system prompt.

## 2. User Stories
* As a System, I want to parse `SKILL.md` files using a robust YAML parser so
  that I can extract metadata (`name`, `description`) and the instruction body
  reliably.
* As an Agent, I want to see a list of available scripts and reference documents
  associated with a skill, so I know what tools are at my disposal without
  cluttering my context window with their full content immediately (Progressive
  Disclosure).
* As a Developer, I want the `Agent` loader to automatically check the new
  `src/vybz/skills/` directory first, so that if I migrate a skill, the agent
  picks up the new version without changing the agent definition.

## 3. Acceptance Criteria
- [ ] **Dependency:** `PyYAML` is added to `pyproject.toml`.
- [ ] **Domain Update:** `src/vybz/skill.py` is refactored:
    - [ ] `Skill` dataclass includes `instructions: str` (Markdown body).
    - [ ] `Skill` dataclass includes `path: Path` (Root directory of the skill).
    - [ ] `from_directory(path: Path)` factory method is implemented.
    - [ ] **Validation:** `from_directory` raises `ValueError` if the directory
          name does not match the YAML `name` field (Spec Requirement).
- [ ] **Rendering Logic:** `Skill.render()` is updated:
    - [ ] Creates a header indicating the following instruction is a skill
    - [ ] Returns the `instructions` body.
    - [ ] Scans all subdirectories.
    - [ ] Appends all markdown content in subdirectories if they exist, with
          appropriate headers ensuring the content is perceived as details of
          the skill by the agent
- [ ] **Loader Logic:** `src/vybz/agent.py` implements "Dual-Path" lookup
      (check `src/vybz/skills/` first, fallback to `agents/skills/`).

## 4. Implementation Hints (Technical)

### 4.1 Module: `src/vybz/skill.py`

**Dataclass Update:**
```python
@dataclass
class Skill:
    # ... existing fields ...
    path: Path | None = None     # New: Track the source directory
    instructions: str | None = None
```

**New Factory Method:**
```python
@classmethod
def from_directory(cls, dir_path: Path) -> "Skill":
    # 1. Validate SKILL.md exists
    skill_file = dir_path / "SKILL.md"
    if not skill_file.exists():
        raise FileNotFoundError(f"Invalid skill directory: {skill_file} missing")

    # 2. Parse Frontmatter & Body (PyYAML)
    # ... extraction logic ...
    
    # 3. Spec Validation: Name Consistency
    if data["name"] != dir_path.name:
        raise ValueError(f"Skill violation: YAML name '{data['name']}' must match directory '{dir_path.name}'")
    
    return cls(
        id=dir_path.name,
        name=data["name"],
        path=dir_path, # Store the root for later scanning
        description=data["description"],
        instructions=body_content
    )
```

**Render Update (Resource Discovery):**
```python
def render(self) -> str:
    # 1. New Format Priority
    if self.instructions:
        output = f"#### {self.name}\n_{self.description}_\n\n{self.instructions}"
        
        # Dynamic Resource Scanning
        if self.path:
            # Scripts
            scripts_dir = self.path / "scripts"
            if scripts_dir.exists():
                scripts = [f.name for f in scripts_dir.iterdir() if f.is_file()]
                if scripts:
                    output += "\n\n**Available Scripts:**\n"
                    for s in scripts:
                        output += f"* `{s}` (in {scripts_dir})\n"

            # References
            refs_dir = self.path / "references"
            if refs_dir.exists():
                refs = [f.name for f in refs_dir.iterdir() if f.is_file()]
                if refs:
                    output += "\n\n**Reference Docs:**\n"
                    for r in refs:
                        output += f"* `{r}` (in {refs_dir})\n"
        
        return output
    
    # 2. Legacy Fallback
    # ... existing logic ...
```

### 4.2 Module: `src/vybz/agent.py`
*   Implement the priority lookup loop in `from_toml` as previously specified.

## 5. Execution Plan
1.  [ ] **Setup:** Add `PyYAML` to `pyproject.toml`.
2.  [ ] **Refactor Skill:** Update `src/vybz/skill.py` with `path` field,
        `from_directory` loader, and the resource-aware `render` method.
3.  [ ] **Refactor Agent:** Update `src/vybz/agent.py` to implement the
        priority lookup logic.
4.  [ ] **Test:** Create `tests/vybz/test_skill_v2.py`.
        *   Create a temp skill with a `scripts/test.py` file.
        *   Verify `render()` output contains "**Available Scripts:**" and
            "test.py".
