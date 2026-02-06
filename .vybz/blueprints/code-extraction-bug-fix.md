---
status: "In Progress"
type: "Blueprint"
author: "Senior Python Architect"
last_updated: "2026-02-06"
references: bugs/filename-generation-failure-for-artifacts-missing-h1-headers.md
---

# Code Extraction & Shebang Safety Fix

This blueprint details the remediation of the "Filename Extraction Failure" for
code blocks. We will align the Agent's output format with the Parser's 
expectations while ensuring that executable scripts (Bash/Python) remain valid 
by programmatically stripping metadata comments.

## 1. Goal
To ensure that when an Agent generates a file (e.g., `migrate.sh`), the system 
correctly identifies the filename `migrate.sh` instead of `artifact-123.md`. 
Crucially, this must happen without breaking the script's `#!/bin/sh` shebang 
line.

## 2. Module Specification: `src/vybz/artifact.py`

### 2.1 Update `CodeFileHandler.extract`
We must modify the extraction logic to remove the metadata comment from the 
saved content.

*   **Current Logic:** Returns `token.content` verbatim.
*   **New Logic:**
    1.  If the handler matched via `FILENAME_PATTERN` (explicit comment):
        *   Extract the filename.
        *   **Action:** Remove the entire matching text (the comment line) 
            from the content string.
        *   **Cleanup:** `lstrip()` the remaining content to ensure no leading 
            blank lines remain. This promotes the `#!/bin/sh` line (originally 
            Line 2) to Line 1.
    2.  If the handler matched via `DOCSTRING_PATTERN`:
        *   **Action:** Do NOT strip the content. Docstrings are valid code and
            should be preserved.

### 2.2 Regex Refinement
Ensure `FILENAME_PATTERN` captures the full line to facilitate clean removal.

```python
# Ensure it matches the newline character so removal doesn't leave a blank line
FILENAME_PATTERN = re.compile(
    r'(?:^|\n)\s*(?:#|//|--)\s*(?:filename|file):\s*(.+?)\s*(?:\n|$)',
    re.IGNORECASE | re.MULTILINE
)
```

## 3. Configuration Updates: Agent Prompts

We need to instruct Agents to place the filename **inside** the block, but 
assure them it is safe to do so.

### 3.1 Target Files
*   `src/vybz/agents/junior-dev.toml`
*   `src/vybz/agents/senior-dev.toml`
*   `src/vybz/agents/sysadmin.toml`

### 3.2 Task Directive Update
Replace the instruction "include filename immediately before the code block" 
with:

```toml
**Code Formatting:**
*   **Filename Metadata:** You MUST include the full filename as a comment on 
    the FIRST LINE inside the code block.
    Format: `# filename: path/to/file.ext`
*   **Shebangs:** For scripts requiring a shebang (e.g., `#!/bin/sh`), place 
    the filename comment on Line 1 and the shebang on Line 2. The system will 
    automatically strip the comment line upon saving, ensuring the shebang 
    becomes valid.
```

## 4. Verification Strategy

### 4.1 Unit Test: `tests/vybz/test_code_file_handler.py`
Add a new test case: `test_extract_strips_filename_comment`.

*   **Input:**
    ```bash
    # filename: test.sh
    #!/bin/sh
    echo "hello"
    ```
*   **Expectation:**
    *   `artifact.filename == "test.sh"`
    *   `artifact.content.startswith("#!/bin/sh")` (Line 1 is Shebang).

### 4.2 Manual Verification
1.  **Run:** `vybz junior-dev "Create a bash script named hello.sh that prints 
    hello"`
2.  **Output Check:** Verify Agent puts `# filename: hello.sh` inside the block.
3.  **Action:** `/save`
4.  **File Check:** Open `hello.sh`. Verify Line 1 is `#!/bin/sh` (or `#!/usr/bin/env bash`) and the comment is gone.

## 5. Execution Steps
1.  **Refactor Code:** Update `src/vybz/artifact.py`.
2.  **Update Tests:** Add the stripping test case.
3.  **Update Agents:** Modify the TOML files for `junior-dev`, `senior-dev`, and `sysadmin`.
