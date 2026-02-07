---
status: "Draft"
type: "Blueprint"
author: "Senior Python Architect"
last_updated: "2026-02-06"
references: blueprints/vybzd/vybzd-top-level-blueprint.md, blueprints/vybzd/vybzd-step-1.md
---

# Vybz Engine Refactor - Step 2: The ADK Adapter

This blueprint details the implementation of the **ADK Adapter Layer**. This 
layer is responsible for "hydrating" Vybz's proprietary configuration objects 
(Agents defined in TOML, Skills defined in Markdown) into executable 
`google.adk` objects.

## 1. Goal
To create a translation service `AdkHydrator` that allows the Vybz Server to 
load the existing Agent Library without requiring a rewrite of the 
TOML/Markdown definitions.

## 2. Dependencies
*   **Target:** `pyproject.toml`
*   **Action:** Add `google-adk>=1.24.1` (or relevant version) to dependencies.

## 3. Module Specification: `src/vybz/server/adapter.py`

### 3.1 Class: `AdkHydrator`
A stateless service class.

#### Method: `hydrate_agent(self, vybz_agent: vybz.shared.agent.Agent) -> adk.Agent`
*   **Purpose:** Converts a Vybz Agent into an ADK Agent.
*   **Logic:**
    1.  **System Prompt Assembly:**
        *   Call `vybz_agent.construct_agent_role_profile()`.
        *   This reuses the existing logic that combines Role, Context, and 
            Skills into a single string.
    2.  **Model Configuration:**
        *   Map Vybz model strings (e.g., `gemini-3-flash`) to ADK Model 
            configurations.
    3.  **Tool Hydration (Preliminary):**
        *   *Future Scope:* This phase will strictly handle the text-based
            prompt hydration. Executable tools (scripts) will be handled in 
            Step 3.
    4.  **Instantiation:**
        *   Return `adk.Agent(name=vybz_agent.name, system_prompt=..., model=...)`.

#### Method: `hydrate_squad(self, library: vybz.shared.library.Library) -> Dict[str, adk.Agent]`
*   **Purpose:** Loads the entire squad into an ADK-compatible registry.
*   **Logic:**
    1.  Iterate `library.list_agents()`.
    2.  Load each `vybz_agent` via `library.get_agent_path` -> `Agent.from_toml`.
    3.  Call `hydrate_agent` for each.
    4.  Return a dictionary mapping `agent_id` -> `adk.Agent`.

## 4. Verification Strategy

### 4.1 Unit Tests (`tests/vybz/server/test_adapter.py`)
*   **Test:** `test_hydrate_agent_preserves_prompt`
    *   Create a mock `vybz.shared.agent.Agent`.
    *   Run `hydrate_agent`.
    *   Assert that `adk_agent.system_prompt` contains the role spec and skill 
        instructions.
*   **Test:** `test_hydrate_squad_loads_all`
    *   Mock the `Library`.
    *   Verify it iterates and hydrates all agents.

## 5. Execution Steps
1.  **Dependencies:** Update `pyproject.toml`.
2.  **Adapter:** Implement `src/vybz/server/adapter.py`.
3.  **Test:** Create and run `tests/vybz/server/test_adapter.py`.
