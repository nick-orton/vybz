---
status: "Completed"
type: "Design"
last_updated: "2026-01-14"
references: intents/modular-agent-skills-architecture.md, intents/skills-advisor-changes.md
---

# Modular Agent Skills Architecture

## 1. High-Level Intent
Transition the Vybz Agent architecture from monolithic TOML definitions to a
composable "Skill-based" system. Currently, critical context (SDK usage, OS
constraints, Git standards) is duplicated across multiple agents. This refactor
introduces a `Skill` domain object and a central repository of shared
capabilities. This ensures the "Don't Repeat Yourself" (DRY) principle, allows
for atomic updates to the technical stack (e.g., upgrading SDK versions), and
empowers the Advisor agent to compose new specialized agents from existing
building blocks.

## 2. User Stories
* As a System Maintainer, I want to update the "Google GenAI SDK" instructions
  in one file (`skills/google-genai.toml`) and have `junior-dev`,
  `senior-dev`, and `pm` immediately inherit the changes.
* As an Advisor Agent, I want to draft new agents by simply referencing a list
  of skill IDs rather than hallucinating boilerplate instructions.
* As a User, I want to dynamically inject a new capability (e.g.,
  `/upskill freebsd-sysadmin`) into an active session without restarting.

## 3. Architecture Specification

### 3.1 Domain Model
*   **Skill:** A new class representing a unit of capability.
    *   Attributes: `name`, `description`, `knowledge` (List[str]),
        `abilities` (List[str]).
    *   Source: `src/vybz/agents/skills/*.toml`.
*   **Agent:** Updated to include a `skills` attribute (List[str] of
    filenames).
    *   Logic: During initialization, the `Agent` resolves these string IDs
        into `Skill` objects via the `Squad` or a new `SkillRegistry`.
    *   Prompt Construction: `construct_agent_role_profile()` appends skill
        content to the System Instruction.

### 3.2 File Structure
```text
src/vybz/
├── agents/
│   ├── junior-dev.toml  (references skills=["python", "genai-sdk"])
│   └── skills/          (New Directory)
│       ├── python.toml
│       └── genai-sdk.toml
```

## 4. Execution Phases

### Phase 1: Core Infrastructure & Pilot
**Goal:** Enable the loading and rendering of Skills.
1.  **Infrastructure:** Create `src/vybz/skill.py` and the `skills/`
    directory.
2.  **Refactor Agent:** Update `src/vybz/agent.py` to parse the `skills` list
    from TOML.
3.  **Rendering Logic:** Update `construct_agent_role_profile` to iterate
    loaded skills and format their `knowledge` and `abilities` into the prompt.
4.  **Pilot Migration:** Extract *one* major shared context (e.g., the Google
    GenAI SDK instructions) into `skills/google-genai-v1-57.toml` and update
    `junior-dev` to use it.

### Phase 2: Full Migration & Advisor Update
**Goal:** Eradicate duplicate context and teach the Advisor.
1.  **Mass Migration:** Refactor `senior-dev`, `pm`, and `tech-writer`. Extract
    OS context, Git standards, and Python standards into respective Skill
    files.
2.  **Advisor Upgrade:** Update `advisor.toml` to understand the new schema.
    Give it the list of available skills so it can compose new agents
    effectively.
3.  **Validation:** Verify that all agents still behave correctly with the
    composed prompts.

### Phase 3: Dynamic Runtime Upskilling
**Goal:** Allow users to modify agent capabilities on the fly.
1.  **REPL Command:** Implement `/upskill <skill_name>` in `repl.py`.
2.  **Hot Injection:** Logic to load the skill, append it to the active
    agent's definition, and trigger a Context Refresh (similar to `/update`)
    to make the LLM aware of its new abilities.

## 5. Acceptance Criteria
- [ ] `src/vybz/agents/skills/` directory exists.
- [ ] `Agent` objects successfully load referenced skills from TOML.
- [ ] The `google-genai` SDK instructions exist in exactly one place but are
      used by multiple agents.
- [ ] The system prompt generated for `junior-dev` contains the text from its
      attached skills.
- [ ] The Advisor agent can generate valid TOML for a new agent using the
      `skills = [...]` syntax.
`       └── genai-sdk.toml
