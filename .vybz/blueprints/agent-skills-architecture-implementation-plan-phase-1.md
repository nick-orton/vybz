---
status: "Completed"
type: "Blueprint"
author: "Senior Python Architect"
last_updated: "2026-01-12"
references: designs/agent-skills-architecture-v1.md, designs/agent-skills-architecture.md
---

# Agent Skills Architecture Implementation Plan (Phase 1)

This blueprint details the implementation of the **Skills Domain Model**. This 
refactor decouples "Capability/Context" from "Persona" by introducing a `Skill`
object and updating the `Agent` class to compose its system prompt dynamically.

## 1. Goal
Transition agents (`junior-dev`) from a monolithic TOML definition to a composed
agent that inherits the "Google GenAI SDK" knowledge from a shared skill file.

## 2. Architectural Changes & Module Specifications

### 2.1 New Module: `src/vybz/skill.py`
**Purpose:** Defines the `Skill` domain object. This is a data container for reusable context.

*   **Class:** `Skill` (Dataclass)
*   **Attributes:**
    *   `id`: str (filename stem)
    *   `name`: str (Human readable)
    *   `description`: str (For future Advisor lookup)
    *   `knowledge`: `List[str]` (Facts/Context)
    *   `abilities`: `List[str]` (Instructions/Rules)
*   **Methods:**
    *   `from_toml(path: Path) -> Skill`: Factory method.
    *   `render() -> str`: Formats the skill into Markdown for injection into the system prompt.

### 2.2 Refactor: `src/vybz/agent.py`
**Purpose:** Update the `Agent` to ingest and render `Skill` objects.

*   **Imports:** Add `from vybz.skill import Skill`.
*   **Attributes:** Add `skills: List[Skill]` to the dataclass.
*   **Method Update: `from_toml`**
    *   **Logic:**
        1.  Parse the `skills` list (strings) from the TOML data (default to empty list if missing).
        2.  Resolve the `skills/` directory relative to the agent TOML file (`path.parent / "skills"`).
        3.  Iterate the list, calculate the path for each skill (e.g., `skills/google-genai-v1-57.toml`), and instantiate `Skill` objects.
        4.  **Fail Fast:** Raise `FileNotFoundError` if a referenced skill is missing.
*   **Method Update: `construct_agent_role_profile`**
    *   **Logic:** Iterate through `self.skills` and append `skill.render()` output to the generated prompt string.

### 2.3 New Artifact: `src/vybz/agents/skills/google-genai-v1-57.toml`
**Purpose:** The single source of truth for SDK usage rules.

*   **Content:** Extracted from the current `junior-dev.toml` "SYNTAX ENFORCER" 
    section.
*   **Structure:**
    ```toml
    name = "Google GenAI SDK (Unified v1.57)"
    description = "Standards and constraints for the unified google-genai library."
    knowledge = [ "We are strictly using the Unified Google Gen AI SDK (v1.57).", ... ]
    abilities = [ "Use `client = genai.Client(...)`", "Never use `google.generativeai`", ... ]
    ```

### 2.4 Update Artifact: `src/vybz/agents/junior-dev.toml`
**Purpose:** Consume the new skill.

*   **Add:** `skills = ["google-genai-v1-57"]`
*   **Remove:** The hardcoded "SYNTAX ENFORCER" text block from `operating_context`.

## 3. Order of Operations

### Step 1: Create the Skill Infrastructure
1.  Create directory `src/vybz/agents/skills/`.
2.  Create `src/vybz/skill.py`.
    *   *Standard:* Use `tomllib` and `dataclasses`.

### Step 2: Create the Pilot Skill
1.  Create `src/vybz/agents/skills/google-genai-v1-57.toml`.
2.  Copy the SDK constraints from `src/vybz/agents/junior-dev.toml` into the `knowledge` and `abilities` lists of the new file.

### Step 3: Refactor the Agent Class
1.  Modify `src/vybz/agent.py`.
    *   Update `__init__` (add skills field).
    *   Update `from_toml` (loading logic).
    *   Update `construct_agent_role_profile` (rendering logic).

### Step 4: Migrate Junior Dev
1.  Modify `src/vybz/agents/junior-dev.toml`.
    *   Add the `skills` key.
    *   Delete the legacy text.

### Step 5: Verification
1.  Run the verification script below to ensure the final prompt still contains the SDK rules.

## 4. Verification Script

```python
if __name__ == "__main__":
    from vybz.squad import Squad
    
    try:
        # Force reload to pick up changes
        agent = Squad.get_agent("junior-dev")
        
        print(f"Loaded Agent: {agent.name}")
        print(f"Skills Loaded: {[s.name for s in agent.skills]}")
        
        prompt = agent.construct_agent_role_profile()
        
        # Verification Checks
        if "Google GenAI SDK" in prompt:
            print("SUCCESS: Skill name found in prompt.")
        else:
            print("FAILURE: Skill name missing.")
            
        if "google.generativeai" in prompt: # Checking for the "Forbidden" rule
            print("SUCCESS: Skill content found in prompt.")
        else:
            print("FAILURE: Skill content missing.")
            
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
