---
status: "Completed"
type: "Design"
author: "PM Lead"
last_updated: "2026-02-04"
references: designs/agentskills/agentskillsio-standard.md, designs/agentskills/agentskillsio-standard-phase-3-runtime.md
---

# Agent Skills 2.0 - Phase 4: The Skill Creator (Advisor Enlightenment)

## 1. High-Level Intent
Empower the **Advisor** agent to autonomously extend the capabilities of the
Squad by equipping it with a meta-skill: `skill-creator`. This skill 
encapsulates the knowledge of the AgentSkills.io specification, enabling the 
Advisor to generate valid, standards-compliant `SKILL.md` directories upon 
request. Additionally, this phase includes a final "Spring Cleaning" to purge 
references to legacy TOML skills from documentation and perform a holistic 
codebase critique.

## 2. User Stories
* As a User, I want to tell the Advisor "Create a skill for Docker management,"
  and receive a complete, valid `src/vybz/skills/docker-manager/` directory
  structure, so I don't have to manually boilerplate the YAML and Markdown.
* As the Advisor Agent, I want a strict definition of the Skill format so I
  don't hallucinate invalid Frontmatter or prohibited directory names.
* As a System Maintainer, I want to ensure the Advisor generates generic
  "Agent" instructions, not specific "Claude" or "Gemini" instructions, to
  maintain model agnosticism.

## 3. Acceptance Criteria
- [ ] **New Skill:** `src/vybz/skills/skill-creator/SKILL.md` exists.
- [ ] **Skill Content:** The `skill-creator` skill accurately reflects the
      AgentSkills.io spec (directory structure, YAML schema, naming conventions).
- [ ] **Neutrality:** The skill instructions use neutral terms ("The Agent",
      "The Model") and strictly exclude references to specific provider brands
      (e.g., "Claude").
- [ ] **Advisor Update:** `src/vybz/agents/advisor.toml` includes
      `skill-creator` in its skills list.
- [ ] **Advisor Directive:** The Advisor's `task_directive` is updated to
      explicitly prefer creating atomic Skills over monolithic Agent Prompts
      when extending capabilities.
- [ ] **Cleanup:** A report is generated listing any Design or Blueprint files
      still referencing legacy `.toml` skill paths.

## 4. Implementation Hints (Technical)

### 4.1 Artifact: `src/vybz/skills/skill-creator/SKILL.md`
This file should be adapted from the community standard but tailored for Vybz.
The community standard can be found: https://github.com/anthropics/skills/tree/main/skills/skill-creator
This should not be copied, but should inform how you want skillbuilding to work
for vybz

**Frontmatter:**
```yaml
---
name: skill-creator
description: Create new Agent Skills following the AgentSkills.io standard. Use this when the user wants to teach the agent a new capability or workflow.
---
```

**Body (Markdown Instructions):**
*   **Naming Rules:** Enforce lowercase, alphanumeric, hyphens only.
*   **Directory Structure:** Mandate `skill-name/SKILL.md`.
*   **Consistency Rule:** Explicitly state that the YAML `name` field MUST match the parent directory name exactly.
*   **YAML Schema:** Define `name` and `description` as mandatory.
*   **Progressive Disclosure:** Instruct the Advisor to keep the top-level
    `SKILL.md` concise and move heavy code into `scripts/` (if applicable).
*   **Output Format:** Instruct the Advisor to output the full file content
    inside a code block with a filename comment (e.g., `# filename:
    src/vybz/skills/foo/SKILL.md`) so the `CodeFileHandler` can extract it.

### 4.2 Refactor: `src/vybz/agents/advisor.toml`
*   **Skills:** Add `"skill-creator"`.
*   **Task Directive Update:**
    ```toml
    task_directive = """
    ...
    **Extending Capabilities:**
    If the user requires a new capability (e.g., "SQL access", "Git handling"), 
    DO NOT just write it into the Agent's `operating_context`. 
    INSTEAD, use your `skill-creator` knowledge to draft a new Skill.
    1.  Design the `SKILL.md`.
    2.  Then, update the Agent definition to reference this new skill in its 
        `skills` list.
    """
    ```

### 4.3 Cleanup Task (Librarian)
*   Run `grep -r "agents/skills/" .vybz/` to find stale references in
    documentation.
*   Create a `Critique` artifact summarizing the findings.

## 5. Execution Plan
1.  [ ] **Create Skill:** Draft `src/vybz/skills/skill-creator/SKILL.md` based
        on the specification.
2.  [ ] **Update Advisor:** Modify `src/vybz/agents/advisor.toml` to consume
        the new skill and update its directive.
3.  [ ] **Verify (Manual):**
        *   Launch `vybz advisor`.
        *   Prompt: "Create a skill for parsing CSV files."
        *   Action: `/save`.
        *   Check: Does `src/vybz/skills/csv-parser/SKILL.md` exist and look valid?
4.  [ ] **Project Cleanup:**
        *   Grep for legacy paths.
        *   Update any stale Designs/Blueprints found.
5.  [ ] **Final Critique:** Run a full codebase critique to identify any
        architectural drift caused by the migration.
