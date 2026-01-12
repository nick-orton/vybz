---
status: "Draft"
type: "Blueprint"
last_updated: "2026-01-11"
references: designs/no-copy-pasting.md
---

# Auto-Save Artifacts Implementation Plan

This blueprint details the implementation of the `/save` command in the `vybz` 
REPL. This feature allows users to persist the Agent's most recent output as a 
structured file without manual copy-pasting.

## 1. Goal
Enable a frictionless "Generate -> Review -> Save" loop by allowing the user to 
type `/save` to write the last generated artifact (Design, Blueprint, Intent) 
to its correct directory based on its internal metadata.

## 2. Module Specification: `src/vybz/repl.py`

### 2.1 Class `ReplSession` Updates

#### New Attribute
*   `self.last_response: Optional[str]`: Stores the full text of the most 
    recent Agent response (accumulated from the stream).

#### Update: `_handle_input`
*   **Logic:** At the end of the streaming loop, assign the joined 
    `full_response` string to `self.last_response`.

### 2.2 New Helper Methods

#### `_parse_artifact(self, text: str) -> Tuple[str, str, str]`
*   **Purpose:** Analyzes text to determine content, filename, and destination.
*   **Logic:**
    1.  **Extraction:**
        *   Check for Markdown code blocks (` ```markdown...``` or ```md ...``` `).
            *   Likely the Markdown code block will have other code blocks inside of
                it, so you need to be robust to nested delimeters.
        *   If more than one markdown block, use the **entire** text (assuming 
            the Agent output *is* the document).
    2.  **Metadata Parsing (Regex):**
        *   **Type:** `^---\s+.*type:\s*["']?(\w+)["']?.*---` (YAML Frontmatter).
        *   **Title:** `^#\s+(.+)$` (First H1 header).
    3.  **Routing:**
        *   Map `type` to directory:
            *   `Design` -> `designs/`
            *   `Blueprint` -> `blueprints/`
            *   `Intent` -> `intents/`
            *   Default -> `output/`
    4.  **Sanitization:**
        *   Convert Title to kebab-case (lowercase, hyphens, alphanumeric only) 
            for the filename.
        *   ensure that the "```" delimeters are not included in the markdown 
            body
        *   If the agent has provided a filename, prefer that over the title
    5.  **Returns:** `(content, directory, filename)`

#### `_cmd_save(self) -> bool`
*   **Trigger:** Called when `_handle_command` receives `/save`.
*   **Logic:**
    1.  Check `self.last_response`. If None, print error.
    2.  Call `_parse_artifact(self.last_response)`.
    3.  Resolve destination path relative to `self.codebase.root_path` 
        (if active) or `cwd`.
    4.  `mkdir -p` the target directory.
    5.  Write the file.
    6.  `ui.print_success(f"Saved {type} to {path}")`.

### 2.3 Update: `_handle_command`
*   Add case for `/save`.

## 3. Verification Strategy

### Test Case 1: Saving a Design (PM Agent)
1.  **Input:** `vybz pm` -> "Design a login system."
2.  **Output:** Agent generates a Markdown spec with YAML `type: "Design"` and 
    `# Login System`.
3.  **Action:** User types `/save`.
4.  **Expectation:**
    *   System prints: `Saved Design to designs/login-system.md`.
    *   File exists at `designs/login-system.md`.
    *   File contains the content.

## 4. Execution Steps
1.  **Modify `ReplSession.__init__`**: Initialize `self.last_response = None`.
2.  **Modify `_handle_input`**: Capture the stream result.
3.  **Implement `_parse_artifact`**: Regex logic.
4.  **Implement `_cmd_save`**: File I/O logic.
5.  **Register Command**: Update command parser.
