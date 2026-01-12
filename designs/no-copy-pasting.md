---
status: "Draft"
type: "Design"
last_updated: "2026-01-11"
references: intents/no-copy-pasting.md
---

# Artifact Persistence (Auto-Save) Specification

## 1. High-Level Intent
Implement a "Smart Save" feature via the `/save` command in the REPL. Unlike a
standard "save as" dialog, this feature automatically determines the
destination directory and filename based on the content of the Agent's last
response. This relies on the Agent adhering to the project's Metadata Standards
(YAML Frontmatter and H1 Headers) to route artifacts to `designs/`,
`blueprints/`, or `intents/` without user intervention.

## 2. User Stories
* As a User, I want to type `/save` immediately after an Agent generates a spec,
  and have the system automatically write it to the correct folder (e.g.,
  `designs/` for PM output, `blueprints/` for Architect output).
* As a User, I want the filename to be auto-generated from the document title
  (kebab-case) so I don't have to type it manually.
* As a User, I want the system to handle directory creation if the target folder
  doesn't exist.
* As a User, I want the system to warn me if it cannot determine the file type
  or title, rather than saving garbage.

## 3. Acceptance Criteria
- [ ] **State Tracking:** `ReplSession` captures the most recent Agent response text.
- [ ] **Smart Extraction:** Logic extracts the *last* Markdown code block from the response.
- [ ] **Metadata Parsing (Regex):**
    - Extracts YAML Frontmatter to determine `type`.
    - Extracts the first H1 Header (`# Title`) to determine the filename.
- [ ] **Routing Logic:**
    - `type: Design` -> `designs/`
    - `type: Blueprint` -> `blueprints/`
    - `type: Intent` -> `intents/`
    - Unknown/Missing Type -> `output/` (Fallback).
- [ ] **Filename Sanitization:** H1 title is converted to lowercase kebab-case
      (e.g., `# My Cool Feature` -> `my-cool-feature.md`).
- [ ] **Path Resolution:** Relative to `--codebase` root (if active) or CWD.
- [ ] **Feedback:** UI prints "Saved [Type] to [RelPath]" in green.

## 4. Implementation Hints (Technical)
*   **Module:** `src/vybz/repl.py`
*   **Parsing Logic:**
    ```python
    import re
    
    # 1. Extract YAML Type
    # Looks for type: "Value" or type: Value inside --- blocks
    type_pattern = re.compile(r'^---\s+.*type:\s*["\']?(\w+)["\']?.*---', re.DOTALL | re.MULTILINE)
    
    # 2. Extract H1 Title
    # Looks for # Title
    title_pattern = re.compile(r'^#\s+(.+)$', re.MULTILINE)
    ```
*   **Sanitization:**
    ```python
    filename = title.lower().strip().replace(" ", "-")
    filename = re.sub(r'[^a-z0-9-]', '', filename) + ".md"
    ```
*   **Routing Table:**
    ```python
    DIR_MAP = {
        "Design": "designs",
        "Blueprint": "blueprints",
        "Intent": "intents"
    }
    ```

## 5. Execution Plan
1.  [ ] **Helper Methods:** Implement `_parse_artifact(text)` in `ReplSession`.
        It should return a tuple `(content, directory, filename)`.
2.  [ ] **Command Logic:** Implement `_cmd_save(self)` to call the parser.
3.  [ ] **File IO:** Implement the write logic using `pathlib.Path`. Ensure
        `parent.mkdir(parents=True, exist_ok=True)` is called.
4.  [ ] **Integration:** Bind `/save` in `_handle_command`.
