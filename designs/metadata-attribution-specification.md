---
status: "Draft"
type: "Design"
author: "PM Lead"
last_updated: "2026-01-16"
references: intents/agents-sign-their-design-docs.md, src/vybz/agents/skills/vybz-metadata.toml
---

# Metadata Attribution Specification

## 1. High-Level Intent
Update the Vybz Metadata Standard to include an `author` field in the YAML
Frontmatter of all artifacts (Designs, Blueprints, Intents, Bugs). Currently,
provenance is lost once a file is saved; it is impossible to distinguish
between a human-authored Intent and an Agent-authored Design without checking
git logs. This change enforces attribution at the document level, enabling the
Librarian and users to track the "Chain of Thought" ownership.

## 2. User Stories
* As a User, I want to see `author: "PM Lead"` in a design doc so I know
  explicitly which agent persona generated the specification.
* As the Librarian Agent, I want to parse the `author` field to build a
  dependency graph of who requested what.
* As a System Maintainer, I want to update this standard in exactly one place
  (the `vybz-metadata` skill) and have all agents immediately adopt the new
  signing protocol.

## 3. Acceptance Criteria
- [ ] **Skill Update:** `src/vybz/agents/skills/vybz-metadata.toml` is updated.
- [ ] **Schema Definition:** The YAML example in the skill includes the
      `author` key.
- [ ] **Instruction:** The skill explicitly instructs Agents to use their full
      Identity Name (e.g., "Senior Python Architect") as the value for
      `author`.
- [ ] **Verification:** A newly generated artifact from `vybz pm` includes the
      `author` field in its frontmatter.

## 4. Implementation Hints (Technical)
*   **Target File:** `src/vybz/agents/skills/vybz-metadata.toml`.
*   **Content Update:**
    Update the `knowledge` block where the YAML schema is defined:
    ```yaml
    ---
    status: "Draft"
    type: "Design"
    author: "{{Your Agent Name}}"  # <--- NEW FIELD
    last_updated: "YYYY-MM-DD"
    references: ...
    ---
    ```
*   **Abilities Update:** Add a specific instruction to the `abilities` list:
    "Always populate the `author` field with your Agent Name (e.g., 'PM Lead')
    when creating new artifacts."

## 5. Execution Plan
1.  [ ] **Update Skill:** Modify `src/vybz/agents/skills/vybz-metadata.toml` to
        include the new schema and instructions.
2.  [ ] **Verify:** Run `vybz pm "Design a login system"` and check the output
        for the `author` field.
