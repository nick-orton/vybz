---
status: "Draft"
type: "Blueprint"
last_updated: "2026-01-13"
references: blueprints/save-diffs.md, designs/no-copy-pasting.md
---

# Refactor: Extract Artifact Manager

This blueprint details the extraction of artifact parsing and persistence logic 
from `src/vybz/repl.py` into a dedicated module `src/vybz/artifact.py`. This is
a prerequisite for implementing robust Diff/Patch saving.

## 1. Goal
Decouple "Text Processing" (identifying and saving files) from "Session 
Management" (chat loops). This reduces the cognitive load of `repl.py` and 
allows for isolated unit testing of the parsing logic.

## 2. New Module: `src/vybz/artifact.py`

### 2.1 Data Structure: `Artifact`
A simple dataclass to transport parsed data.
```python
@dataclass
class Artifact:
    content: str
    filename: str
    directory: str  # "designs", "output", etc.
    type: str       # "Design", "Diff", "Unknown"
```

### 2.2 Class: `ArtifactProcessor`
**Purpose:** Stateless service that ingests raw LLM output and returns an 
`Artifact` object.

*   **Method:** `parse(text: str) -> Artifact`
    *   **Logic:** Moves the existing `_parse_artifact` logic here.
    *   **Refinement:** Structures the logic into "Strategies" 
        (e.g., `_try_parse_yaml_block`, `_try_parse_diff_block`).
*   **Method:** `save(artifact: Artifact, root_path: Path) -> str`
    *   **Logic:** Moves the file I/O logic from `_cmd_save`.
    *   **Returns:** A success string (e.g., "Saved Design to designs/foo.md") 
        or raises an Exception.

## 3. Refactor: `src/vybz/repl.py`

### 3.1 Cleanup
*   **Remove:** `_parse_artifact` method.
*   **Remove:** `_cmd_save` method logic (replace with delegation).
*   **Remove:** Imports related to parsing (`markdown_it`, `re` specific to 
    parsing).

### 3.2 Integration
*   **Import:** `from vybz.artifact import ArtifactProcessor`.
*   **Update:** `_cmd_save` becomes a thin wrapper:
    ```python
    def _cmd_save(self):
        if not self.last_response: return
        
        processor = ArtifactProcessor()
        try:
            # 1. Parse
            artifact = processor.parse(self.last_response)
            
            # 2. Resolve Root
            root = self.codebase.root_path if self.codebase else Path.cwd()
            
            # 3. Save
            msg = processor.save(artifact, root)
            ui.print_success(msg)
            
        except Exception as e:
            ui.print_error(f"Save failed: {e}")
    ```

## 4. Execution Steps

1.  **Create `src/vybz/artifact.py`:** Copy the existing logic from `repl.py`, 
    wrapping it in the new class structure.
2.  **Unit Test:** Create `tests/vybz/test_artifact.py`. Move the existing 
    `test_repl_save_bug.py` logic there.
3.  **Refactor `repl.py`:** Delete the old code and wire up the new class.
4.  **Verify:** Run `vybz` and try to `/save` a design doc to ensure regression 
    testing passes.
5.  **Next Phase:** Once this is clean, implementing the "Diff Saving" logic 
    becomes adding a single method `_try_parse_diff_block` to `ArtifactProcessor`.

