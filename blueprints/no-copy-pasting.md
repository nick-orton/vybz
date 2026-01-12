---
status: "Completed"
type: "Blueprint"
last_updated: "2026-01-12"
references: designs/no-copy-pasting.md, intents/refresh-blueprint-for-save.md
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
*   **Purpose:** Robustly extracts the relevant markdown content, determines the 
    artifact type, and generates a filename.
*   **Dependency:** Uses `markdown-it-py` for token-based parsing to avoid 
    regex fragility with nested code blocks.
*   **Logic:**
    1.  **Tokenization:** Parse the full text into a token stream.
    2.  **Block Extraction:** 
        *   Iterate through tokens to find a `fence` type token.
        *   Check if the inner content starts with `---` (YAML delimiter).
        *   **Win Condition:** If found, use this block as the `candidate_content`.
    3.  **Fallback Strategy:** 
        *   If no valid fenced block is found, check if the *entire* raw text 
            starts with `---`. If so, treat the whole response as the artifact.
    4.  **Metadata Parsing (Regex):**
        *   **Type:** `r'^---\s+.*?(?:type|Type)\s*:\s*["\']?(\w+)["\']?.*?---'`
            *   *Note:* Handles case-insensitivity (`Type` vs `type`) and 
                whitespace.
        *   **Title:** `r'^#\s+(.+)$'` (First H1 header).
    5.  **Routing:**
        *   Map `type` (capitalized) to directory:
            *   `Design` -> `designs/`
            *   `Blueprint` -> `blueprints/`
            *   `Intent` -> `intents/`
            *   Default -> `output/`
    6.  **Sanitization:**
        *   Convert Title to lowercase kebab-case (e.g., `# My Feature` -> 
            `my-feature.md`).
        *   Remove non-alphanumeric characters (except hyphens).
        *   Default filename: `artifact-{timestamp}.md` if no title found.
    7.  **Returns:** `(content, directory, filename)`

#### `_cmd_save(self) -> bool`
*   **Trigger:** Called when `_handle_command` receives `/save`.
*   **Logic:**
    1.  Check `self.last_response`. If None, print error.
    2.  Call `_parse_artifact(self.last_response)`.
    3.  Resolve destination path:
        *   If `self.codebase` is active: `codebase.root_path / directory`.
        *   Else: `cwd / directory`.
    4.  `mkdir -p` the target directory.
    5.  **Existence Check:** Check if target file exists.
    6.  Write the file (UTF-8).
    7.  **UI Feedback:**
        *   If overwritten: Print **Warning** "Overwrote [type] at [path]".
        *   If new: Print **Success** "Saved [type] to [path]".

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
    *   File contains *only* the design doc (no conversational fluff).

### Test Case 2: Fallback (Raw Output)
1.  **Context:** Agent outputs a valid YAML/Markdown doc but forgets to wrap it 
    in a code fence.
2.  **Action:** `/save`.
3.  **Expectation:** System detects the `---` start of the raw string and saves 
    it correctly.

## 4. Execution Steps (Completed)
1.  **Dependencies:** Added `markdown-it-py` to `pyproject.toml`.
2.  **Implementation:** Implemented `ReplSession` updates in `src/vybz/repl.py`.
3.  **Refinement:** Iterated on regex to handle "Type" vs "type" capitalization 
    issues found during QA.
