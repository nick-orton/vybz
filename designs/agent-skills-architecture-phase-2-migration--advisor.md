---
status: "Completed"
type: "Design"
author: "PM Lead"
last_updated: "2026-01-14"
references: designs/agent-skills-architecture.md, intents/modular-agent-skills-architecture.md
---

# Agent Skills Architecture Phase 2: Migration & Advisor

## 1. High-Level Intent
Phase 1 successfully established the `Skill` domain object and the loading
infrastructure. Phase 2 focuses on **Technical Debt Reduction** and **Advisor
Enlightenment**. We will aggressively refactor the remaining core agents
(`senior-dev`, `pm`, `tech-writer`, `librarian`) to strip out duplicated text
regarding OS constraints, Python standards, and Metadata rules, replacing them
with atomic `Skill` references. Furthermore, we will update the `advisor` agent
to understand this new composable architecture, ensuring future agents are
born with the correct structure.

## 2. User Stories
* As a System Maintainer, I want to define "FreeBSD/POSIX Compliance" in exactly
  one place, so that when I update the OS version, every agent (Dev, PM, Ops)
  immediately understands the new constraints.
* As a System Maintainer, I want the `senior-dev` and `junior-dev` to share
  the exact same `python-standards` skill, ensuring code style consistency
  regardless of who writes it.
* As the Advisor Agent, I want to know about the existence of the `skills/`
  library, so that when I design a new agent, I can compose it from existing
  blocks rather than hallucinating monolithic instructions.

## 3. Acceptance Criteria
- [ ] **New Skill:** `src/vybz/agents/skills/python-standards.toml` created
      (PEPs, Typing, Docstrings).
- [ ] **New Skill:** `src/vybz/agents/skills/freebsd-posix.toml` created (OS,
      Shell, Pathing).
- [ ] **New Skill:** `src/vybz/agents/skills/git-standards.toml` created
      (Conventional Commits, Line Wrapping).
- [ ] **New Skill:** `src/vybz/agents/skills/vybz-metadata.toml` created
      (YAML Frontmatter, File Lifecycle).
- [ ] **Refactor:** `senior-dev.toml` consumes `python-standards`,
      `freebsd-posix`, `vybz-metadata`, and `google-genai-v1-57`.
      Hardcoded text removed.
- [ ] **Refactor:** `pm.toml` consumes `vybz-metadata` and `freebsd-posix`.
      Hardcoded text removed.
- [ ] **Refactor:** `tech-writer.toml` consumes `git-standards` and
      `freebsd-posix`. Hardcoded text removed.
- [ ] **Refactor:** `librarian.toml` consumes `vybz-metadata`.
- [ ] **Advisor Update:** `advisor.toml` is updated to explicitly instruct the
      creation of agents using the `skills = [...]` list syntax.

## 4. Implementation Hints (Technical)

### 4.1 Skill Extraction Mapping
*   **`python-standards.toml`**: Extract "PEP 8", "PEP 484", "PEP 257", and
    "Clean Code" sections from `senior-dev.toml`.
*   **`freebsd-posix.toml`**: Extract "THE STACK" (FreeBSD 15.0, vi, Tmux) from
    `pm.toml` and `junior-dev.toml`.
*   **`git-standards.toml`**: Extract "Conventional Commits" and "72/79 char
    wrap" from `tech-writer.toml`.
*   **`vybz-metadata.toml`**: Extract the "Metadata Standard: YAML Frontmatter"
    block found in `pm.toml`, `librarian.toml`, and `senior-dev.toml`.

### 4.2 Advisor Prompt Strategy
The `advisor.toml` `operating_context` needs a new section:
```markdown
## Agent Architecture Standards
Modern Vybz agents are **Composed**, not Monolithic.
1. Check the `src/vybz/agents/skills/` directory for reusable capabilities.
2. When generating TOML, prefer referencing skills over writing raw text.
   Example: `skills = ["python-standards", "freebsd-posix"]`
