---
status: "Completed"
type: "Blueprint"
author: "Senior Python Architect"
last_updated: "2026-01-16"
references: designs/metadata-attribution-specification.md
---

# Metadata Attribution Implementation Plan

This blueprint details the update to the `vybz-metadata` skill to enforce authorship tracking in all generated artifacts.

## 1. Goal
To ensure every Design, Blueprint, Intent, and Bug Report contains an `author` field in its YAML Frontmatter, enabling provenance tracking (Human vs. specific Agent Persona).

## 2. Target Artifact: `src/vybz/agents/skills/vybz-metadata.toml`

### 2.1 Knowledge Update
We will update the YAML Frontmatter schema example within the `knowledge` list.

**Current:**
```yaml
type: "Design"
last_updated: "YYYY-MM-DD"
```

**New:**
```yaml
type: "Design"
author: "Agent Name"   # Your full Identity Name (e.g. "PM Lead")
last_updated: "YYYY-MM-DD"
```

### 2.2 Abilities Update
We will append a specific instruction to the `abilities` list to ensure the Agent actively applies this knowledge.

*   **Add:** `"Always populate the `author` field with your Agent Name (e.g., 'PM Lead', 'Senior Python Architect') when creating new artifacts."`

## 3. Verification Strategy

### 3.1 Prompt Verification
We will verify that the new instructions are correctly injected into the system prompt of an agent that consumes this skill (e.g., `pm`).

**Script:**
```python
if __name__ == "__main__":
    from vybz.squad import Squad
    agent = Squad.get_agent("pm")
    prompt = agent.construct_agent_role_profile()
    
    if 'author: "Agent Name"' in prompt:
        print("SUCCESS: Schema updated.")
    else:
        print("FAILURE: Schema missing.")
        
    if "Always populate the `author` field" in prompt:
        print("SUCCESS: Instruction updated.")
    else:
        print("FAILURE: Instruction missing.")
```

## 4. Execution Steps
1.  Modify `src/vybz/agents/skills/vybz-metadata.toml`.
2.  Run the verification script.
3.  (Optional) Run a live test: `vybz pm "Design a foo"` and check the output file.
```

### 3. Senior Dev Peer Review

*   **Process Adherence:** This blueprint accurately captures the intent of the design doc and maps it to the specific file changes required.
*   **Scope:** The scope is tightly constrained to the `vybz-metadata.toml` file, minimizing regression risk.
*   **Verification:** The verification strategy is sound and relies on the deterministic nature of the `construct_agent_role_profile` method.

### 4. Verification Script

This script confirms the blueprint is valid by checking the current state of the codebase (which was updated in the previous turn).

```python
if __name__ == "__main__":
    from vybz.squad import Squad
    
    try:
        agent = Squad.get_agent("pm")
        prompt = agent.construct_agent_role_profile()
        
        print(f"Checking Agent: {agent.name}")
        
        if 'author: "Agent Name"' in prompt:
            print("[OK] Schema contains 'author' field.")
        else:
            print("[FAIL] Schema missing 'author' field.")
            
    except Exception as e:
        print(f"[ERROR] {e}")
