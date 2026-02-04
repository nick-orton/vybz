---
status: "Draft"
type: "Blueprint"
author: "Senior Python Architect"
last_updated: "2026-02-04"
references: designs/agentskills/agentskillsio-standard-phase-2-migration.md, designs/agentskillsio-standard.md
---

# Agent Skills 2.0 - Phase 2: Migration & Cleanup Implementation

This blueprint details the execution of "The Great Migration." We will automate 
the conversion of legacy TOML skills to the AgentSkills.io `SKILL.md` standard,
verify the data integrity, and then aggressively remove the legacy 
compatibility code to pay down technical debt.

## 1. Goal
To transition the codebase to a single, standard source of truth for Skills 
(`src/vybz/skills/`) and eliminate the complexity of dual-path loading.

## 2. Migration Utility: `scripts/migrate_skills.py`

We need a robust, one-off script to handle the data transformation.

*   The script should be self-executable with a "shebang" comment at the top
*   **Input:** `src/vybz/agents/skills/*.toml`
*   **Output:** `src/vybz/skills/{skill-name}/SKILL.md`
*   **Transformation Logic:**
    1.  **Metadata:** Extract `name` and `description` for YAML Frontmatter.
    2.  **Normalization:** Convert `name` to kebab-case (lowercase, hyphens) 
        for the directory name.
    3.  **Body Generation:**
        *   Create a Level 1 Header: `# {name}`.
        *   If `description` exists, add it as italics.
        *   **Knowledge:** Convert the list of strings into a `## Knowledge` 
            section with bullet points.
        *   **Abilities:** Convert the list of strings into a `## Abilities` 
            section with bullet points.

## 3. Refactor: `src/vybz/skill.py` (The Cleanup)

Once migration is verified, we strip the `Skill` class of legacy attributes.

### 3.1 Dataclass Simplification
*   **Remove:** `knowledge: List[str]`
*   **Remove:** `abilities: List[str]`
*   **Update:** `instructions` becomes a required field (or default to empty 
    string, but semantically required).

### 3.2 Method Removal
*   **Remove:** `from_toml` factory method.
*   **Remove:** Legacy rendering logic in `render()` (the `if self.knowledge:` 
    blocks). The method should now simply return `self.instructions` (plus 
    resource discovery text).

## 4. Refactor: `src/vybz/agent.py` (The Loader)

### 4.1 Lookup Logic Simplification
*   **Remove:** The "Priority 2" fallback logic that checks `agents/skills/*.toml`.
*   **Assert:** The loader *only* checks `src/vybz/skills/{id}`.
*   **Fail Fast:** If the directory doesn't exist, raise `FileNotFoundError` 
    immediately.

## 5. Verification Strategy

### 5.1 Test Suite Updates (`tests/vybz/test_skill.py`)
The existing tests rely on TOML. They must be rewritten or replaced.
*   **Action:** Update `tests/conftest.py` `temp_skills_dir` fixture to create 
    directory-based skills instead of TOML files.
*   **Action:** Delete `test_skill_from_toml_valid` and 
    `test_skill_from_toml_missing_file`.
*   **Action:** Ensure `test_skill_v2.py` covers all loading scenarios.

### 5.2 Manual Migration Check
1.  Run `python3 scripts/migrate_skills.py`.
2.  Inspect `src/vybz/skills/python-standards/SKILL.md`.
    *   *Check:* Does it have YAML frontmatter?
    *   *Check:* Are the PEP rules listed as bullets under `## Knowledge`?
3.  Run `vybz junior-dev`.
    *   *Check:* Does the agent start without error?
    *   *Check:* Does the system prompt still contain the Python standards?

## 6. Execution Steps

1.  **Implement Script:** Create `scripts/migrate_skills.py`.
2.  **Run Migration:** Execute the script to populate `src/vybz/skills/`.
3.  **Verify Data:** Spot check the generated Markdown files.
4.  **Update Tests:** Refactor `tests/conftest.py` and 
    `tests/vybz/test_skill.py` to use the new format.
5.  **Refactor Code:**
    *   Remove legacy logic from `src/vybz/skill.py`.
    *   Remove legacy logic from `src/vybz/agent.py`.
6.  **Delete Legacy Data:** `rm -rf src/vybz/agents/skills/`.
7.  **Final Verification:** Run full test suite (`pytest`).
```

### 3. Senior Dev Peer Review

*   **Safety:** The plan correctly identifies that tests must be updated 
    *before* or *during* the code refactor, otherwise the build will stay 
    broken.
*   **Data Integrity:** The migration script logic (Lists -> Bullets) preserves
    the semantic meaning of the old TOML arrays.
*   **Completeness:** Removing `tomllib` from `skill.py` is a good cleanup 
    step, although `agent.py` will still need it for Agent definitions.

### 4. Verification Script

This script prototypes the transformation logic proposed for 
`migrate_skills.py` to ensure the string formatting produces valid Markdown.

```python
if __name__ == "__main__":
    import re
    
    # Mock Input Data (Simulating parsed TOML)
    data = {
        "name": "Python Standards",
        "description": "Strict adherence to PEP 8.",
        "knowledge": [
            "PEP 8 is mandatory.",
            "Use Type Hints."
        ],
        "abilities": [
            "Refactor complex logic.",
            "Write docstrings."
        ]
    }
    
    print("--- Simulating Migration Logic ---")
    
    # 1. Normalize Name
    safe_name = re.sub(r'[^a-z0-9-]', '', data['name'].lower().replace(' ', '-'))
    print(f"Directory Name: {safe_name}")
    
    # 2. Generate Content
    output = []
    
    # Frontmatter
    output.append("---")
    output.append(f"name: {safe_name}") # Note: YAML name should match directory
    output.append(f"description: \"{data['description']}\"")
    output.append("---")
    
    # Body
    output.append(f"\n# {data['name']}")
    output.append(f"_{data['description']}_")
    
    if data.get('knowledge'):
        output.append("\n## Knowledge")
        for k in data['knowledge']:
            output.append(f"* {k}")
            
    if data.get('abilities'):
        output.append("\n## Abilities")
        for a in data['abilities']:
            output.append(f"* {a}")
            
    final_content = "\n".join(output)
    
    print("\n--- Generated SKILL.md Content ---")
    print(final_content)
    
    # Verification
    if "## Knowledge" in final_content and "* PEP 8" in final_content:
        print("\n[PASS] Knowledge converted to Markdown bullets.")
    else:
        print("\n[FAIL] Markdown conversion failed.")
