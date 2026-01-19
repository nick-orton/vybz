---
status: "Completed"
type: "Blueprint"
author: "Senior Python Architect"
last_updated: "2026-01-19"
references: intents/restructure-vybz-artifacts.md
---

# Restructure Vybz Artifacts Implementation Plan

This blueprint details the centralization of all Vybz-related artifacts into a hidden `.vybz/` directory to declutter the project root.

## 1. Goal
To encapsulate metadata and generated artifacts (`designs/`, `intents/`, `output/`) into a single namespace `.vybz/`, and to promote `Bug` and `Critique` artifacts to top-level citizens within that namespace.

## 2. Module Specification: `src/vybz/artifact.py`

### 2.1 Update `DocumentHandler`
We will modify the `DIR_MAP` class attribute to point to the new directory structure.

**Current:**
```python
DIR_MAP = {
    "Design": "designs",
    "Bug": "intents",
    # ...
}
```

**New:**
```python
DIR_MAP = {
    "Design": ".vybz/designs",
    "Blueprint": ".vybz/blueprints",
    "Intent": ".vybz/intents",
    "Bug": ".vybz/bugs",           # Promoted
    "Critique": ".vybz/critiques"  # Promoted
}
```

### 2.2 Update `DiffHandler` & `CodeFileHandler`
*   **DiffHandler:** Change default directory from `output` to `.vybz/output`.
*   **CodeFileHandler:** Change default directory from `output` to `.vybz/output` (for snippets without paths).

## 3. Knowledge Update: `src/vybz/agents/skills/vybz-metadata.toml`

### 3.1 Path Awareness
Update the `knowledge` section to reflect the new structure.
*   "Design docs live in `.vybz/designs/`"
*   "Bugs live in `.vybz/bugs/`"

## 4. Migration Utility: `scripts/migrate_to_dot_vybz.py`
We cannot simply change the code; we must move existing user files. We will provide a script to handle this safely.

**Logic:**
1.  Create `.vybz/` structure (`intents`, `designs`, `blueprints`, `bugs`, `critiques`, `output`).
2.  Move `designs/*` -> `.vybz/designs/`.
3.  Move `blueprints/*` -> `.vybz/blueprints/`.
4.  Move `output/*` -> `.vybz/output/`.
5.  **Intents Split:**
    *   Iterate files in `intents/`.
    *   Parse YAML `type`.
    *   If `Bug` -> Move to `.vybz/bugs/`.
    *   If `Critique` -> Move to `.vybz/critiques/`.
    *   Else -> Move to `.vybz/intents/`.
6.  Remove old empty directories.

## 5. Configuration: `.gitignore`
Update to ignore the output artifact folder but allow designs.

```gitignore
.vybz/output/
```

## 6. Execution Steps
1.  **Refactor Code:** Update `src/vybz/artifact.py`.
2.  **Update Skill:** Update `src/vybz/agents/skills/vybz-metadata.toml`.
3.  **Create Migration Script:** Generate `scripts/migrate_to_dot_vybz.py`.
4.  **Update Gitignore:** Modify `.gitignore`.
5.  **Verification:** Run migration script and verify file placement.

```

### 3. Senior Dev Peer Review

*   **Migration Safety:** The migration script must be robust. It should check if the destination file already exists to avoid overwriting (e.g., if the user ran the script twice or partially manually moved files).
*   **CodeBase Visibility:** The `CodeBase` class uses `pathspec` to respect `.gitignore`. By default, it reads everything not ignored. Since we are only ignoring `.vybz/output/`, the `CodeBase` *will* see `.vybz/designs/` and include them in the context. This is the desired behavior (Agents need to read designs).
*   **Path Separation:** `pathlib` handles `/` vs `\` automatically, but hardcoding strings like `.vybz/designs` in `artifact.py` is safe as `pathlib` normalizes them on instantiation.

### 4. Verification Script

This script verifies the new routing logic in `artifact.py` *after* the changes would be applied (simulated here).

```python
if __name__ == "__main__":
    from vybz.artifact import DocumentHandler, ArtifactProcessor
    from markdown_it.token import Token
    import re

    print("--- Testing New Routing Logic ---")
    
    # Mocking the change for verification before actual edit
    # In implementation, this will be hardcoded in the class
    DocumentHandler.DIR_MAP = {
        "Design": ".vybz/designs",
        "Blueprint": ".vybz/blueprints",
        "Intent": ".vybz/intents",
        "Bug": ".vybz/bugs",
        "Critique": ".vybz/critiques"
    }

    test_cases = [
        ("Design", ".vybz/designs"),
        ("Bug", ".vybz/bugs"),
        ("Critique", ".vybz/critiques"),
        ("Intent", ".vybz/intents")
    ]

    handler = DocumentHandler()
    
    for type_name, expected_dir in test_cases:
        # Create a mock token
        content = f"---\ntype: {type_name}\n---\n# Test"
        token = Token("fence", "markdown", 0)
        token.content = content
        token.map = None
        
        artifact = handler.extract(token, "")
        
        if artifact.directory == expected_dir:
            print(f"[PASS] Type '{type_name}' routed to '{artifact.directory}'")
        else:
            print(f"[FAIL] Type '{type_name}' routed to '{artifact.directory}' (Expected: {expected_dir})")

