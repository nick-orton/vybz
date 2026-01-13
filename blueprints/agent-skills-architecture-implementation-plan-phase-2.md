---
status: "Draft"
type: "Blueprint"
last_updated: "2026-01-12"
references: designs/agent-skills-architecture-phase-2-migration--advisor.md, designs/agent-skills-architecture.md
---

# Agent Skills Architecture Implementation Plan (Phase 2)

This blueprint details the execution steps for the **Mass Migration** of core agents to the Skills Architecture and the enlightenment of the **Advisor** agent.

## 1. Goal
To eliminate duplicate context across the Squad by extracting shared knowledge (OS constraints, Python standards, Git rules, Metadata schemas) into atomic `Skill` TOML files, and to teach the Advisor agent how to compose new agents using this system.

## 2. Artifact Specification: New Skills

We will create four new skill definitions in `src/vybz/agents/skills/`.

### 2.1 `python-standards.toml`
*   **Source:** `src/vybz/agents/senior-dev.toml` (Role Spec & Operating Context).
*   **Content:**
    *   PEP 20 (Zen), PEP 8 (Style), PEP 484 (Typing), PEP 257 (Docstrings).
    *   Clean Code & SOLID principles.
    *   Python 3.11+ syntax requirements.

### 2.2 `freebsd-posix.toml`
*   **Source:** `src/vybz/agents/pm.toml` and `junior-dev.toml`.
*   **Content:**
    *   **OS:** FreeBSD 15.0 / Debian.
    *   **Tools:** vi, Tmux.
    *   **Pathing:** POSIX compliance.
    *   **Philosophy:** CLI-first, "Flow" state.

### 2.3 `git-standards.toml`
*   **Source:** `src/vybz/agents/tech-writer.toml`.
*   **Content:**
    *   Conventional Commits format (`feat:`, `fix:`).
    *   Line wrapping rules (72 chars for commit bodies).
    *   Laconic message style constraints.

### 2.4 `vybz-metadata.toml`
*   **Source:** `src/vybz/agents/pm.toml` and `librarian.toml`.
*   **Content:**
    *   Design Organization (`intents/`, `designs/`, `blueprints/`).
    *   YAML Frontmatter Schema (Status, Type, References).
    *   File lifecycle rules.

## 3. Refactoring Specifications

### 3.1 `senior-dev.toml`
*   **Remove:**
    *   PEP standards bullet points.
    *   Technical Stack & Constraints (moved to `freebsd-posix` and `python-standards`).
    *   Metadata Standard block.
*   **Add:**
    *   `skills = ["google-genai-v1-57", "python-standards", "freebsd-posix", "vybz-metadata"]`

### 3.2 `pm.toml`
*   **Remove:**
    *   "THE STACK" section.
    *   Design Organization section.
    *   Metadata Standard block.
*   **Add:**
    *   `skills = ["freebsd-posix", "vybz-metadata"]`

### 3.3 `tech-writer.toml`
*   **Remove:**
    *   "The Stack" section.
    *   Standards & Style Guides (Git/Markdown specific parts).
*   **Add:**
    *   `skills = ["freebsd-posix", "git-standards", "google-genai-v1-57"]`

### 3.4 `librarian.toml`
*   **Remove:**
    *   Design Organization section.
    *   Metadata Standard block.
*   **Add:**
    *   `skills = ["vybz-metadata"]`

### 3.5 `advisor.toml`
*   **Update:** `operating_context`
    *   Add a section "Agent Architecture Standards".
    *   Explain the `skills = [...]` list syntax.
    *   Instruct the Advisor to check `src/vybz/agents/skills/` before inventing new rules.

## 4. Execution Steps

1.  **Create Skills:**
    *   Create `src/vybz/agents/skills/python-standards.toml`.
    *   Create `src/vybz/agents/skills/freebsd-posix.toml`.
    *   Create `src/vybz/agents/skills/git-standards.toml`.
    *   Create `src/vybz/agents/skills/vybz-metadata.toml`.
2.  **Migrate Senior Dev:** Refactor `senior-dev.toml`.
3.  **Migrate PM:** Refactor `pm.toml`.
4.  **Migrate Tech Writer:** Refactor `tech-writer.toml`.
5.  **Migrate Librarian:** Refactor `librarian.toml`.
6.  **Update Advisor:** Refactor `advisor.toml`.
7.  **Verification:**
    *   Start `vybz senior-dev` and verify the System Prompt contains PEP rules.
    *   Start `vybz pm` and verify the System Prompt contains Metadata rules.

## 5. Verification Script

```python
if __name__ == "__main__":
    from vybz.squad import Squad
    
    agents_to_check = {
        "senior-dev": ["PEP 8", "FreeBSD"],
        "pm": ["YAML Frontmatter", "FreeBSD"],
        "tech-writer": ["Conventional Commits"],
        "librarian": ["YAML Frontmatter"]
    }

    print("--- Verifying Skill Injection ---")
    for name, keywords in agents_to_check.items():
        try:
            agent = Squad.get_agent(name)
            prompt = agent.construct_agent_role_profile()
            print(f"\nChecking Agent: {name}")
            for kw in keywords:
                if kw in prompt:
                    print(f"  [PASS] Found '{kw}'")
                else:
                    print(f"  [FAIL] Missing '{kw}'")
        except Exception as e:
            print(f"  [ERROR] Could not load {name}: {e}")
