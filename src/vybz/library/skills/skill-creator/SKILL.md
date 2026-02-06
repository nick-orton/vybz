---
name: skill-creator
description: Expertise in designing and documenting portable AI capabilities following the AgentSkills.io standard. Use this when the user wants to teach you a new workflow, standard, or technical domain.
compatibility: Vybz Coding Workbench
metadata:
  author: Principal Architect
  version: "2.0"
  status: Completed
  last_updated: 2026-02-05
---

# Skill Creator
_Expertise in designing and documenting portable AI capabilities following the AgentSkills.io standard._

You use this skill to extend the capabilities of the Vybz Squad by architecting new, reusable "Skills." A skill is a self-contained directory that encapsulates knowledge, behavioral rules, and optional executable resources.

## 1. Skill Architecture
When designing a new skill, prioritize **Atomic Portability**. 
*   **Single Responsibility:** A skill should do one thing well (e.g., `pytest-mastery`, not `python-testing-and-deployment`).
*   **Progressive Disclosure:** Keep the main `SKILL.md` focused on instructions. Move deep technical references to the `references/` directory and executable logic to the `scripts/` directory.

## 2. The SKILL.md Format
Every skill must contain a `SKILL.md` file at its root with valid YAML frontmatter.

### Frontmatter Requirements
*   **`name`**: Must be lowercase, kebab-case, and match the parent directory name exactly.
*   **`description`**: A concise summary (max 1024 chars) explaining what the skill does and when you should use it.
*   **`metadata`**: Always include `author` (your persona name) and `status` (e.g., Draft, Completed).

### Body Content
The body should be directive. Use the following structure:
*   **Introduction:** A brief italicized summary of the skill's purpose.
*   **Knowledge:** Facts, standards, and conceptual frameworks the agent must know.
*   **Abilities:** Specific actions, logic patterns, or "If-This-Then-That" behavioral rules the agent must follow.

## 3. Resource Discovery & Aggregation
Vybz recursively crawls all `.md` files in a skill's subdirectories and appends them to the system prompt.
*   **Scripts:** List available tools in a `scripts/` directory.
*   **References:** Store complex schemas, man pages, or API documentation in a `references/` directory.
*   **Aggregation:** When you define a skill, assume the contents of these sub-files are already part of your mental model.

## 4. Vybz Workbench Conventions
*   **Root Path:** Internal skills reside in `src/vybz/skills/`.
*   **Naming:** Use descriptive, hyphenated names (e.g., `text-processing-awk--sed`).
*   **Output Format:** To ensure the user can immediately persist the skill using the `/save` command, you must output the file content within a code block including a filename comment.

### Example Output Pattern
```markdown
# filename: src/vybz/skills/my-new-skill/SKILL.md
---
name: my-new-skill
description: ...
metadata:
  author: Your Persona
  status: Draft
---
# My New Skill
...
```

## 5. Validation Checklist
Before outputting a new skill, verify:
1.  Does the directory name match the YAML `name`?
2.  Is the YAML valid (check colons and indentation)?
3.  Are the instructions written in an actionable, directive tone?
4.  Is the `# filename:` comment present at the top of the block?


