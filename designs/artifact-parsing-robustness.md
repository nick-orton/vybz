---
status: "Completed"
type: "Design"
last_updated: "2026-01-11"
references: designs/no-copy-pasting.md
---

# Artifact Parsing Robustness

## 1. High-Level Intent
Refactor the `_parse_artifact` method in `src/vybz/repl.py` to address critical
reliability issues identified during QA. The current implementation uses greedy
matching (`rfind`) which corrupts output when the Agent generates multiple code
blocks in a single response (e.g., a Design doc followed by a code snippet).
Additionally, the YAML parsing is too strict regarding capitalization, causing
valid artifacts to be misrouted.

## 2. User Stories
* As a User, I want the `/save` command to extract *only* the artifact block
  containing the YAML frontmatter, ignoring any conversational text or
  secondary code blocks that follow it.
* As a User, I want the system to recognize `Type: Design` (Capitalized) as
  valid metadata, so that my files are routed to the correct directory instead
  of the generic `output/` folder.
* As a User, I want to be explicitly warned if `/save` overwrites an existing
  file, so I am aware of the destructive action.

## 3. Acceptance Criteria
- [ ] **Bounded Block Extraction:** The parser locates the opening fence of the
      YAML block and finds the *immediate next* closing fence (`find`), rather
      than the last fence in the string (`rfind`).
- [ ] **Content Isolation:** Content after the matching closing fence is
      strictly excluded from the saved file.
- [ ] **Case-Insensitive Regex:** The YAML pattern matches `type:`, `Type:`,
      and `TYPE:` with optional whitespace before the colon.
- [ ] **Overwrite Feedback:** If the target file already exists, the UI prints
      a "Overwrote [filename]" message in **Yellow/Warning** style, rather than
      the standard Green success message.

## 4. Implementation Hints (Technical)
*   **Regex Update:**
    Change the `type` capture group to be case-insensitive and tolerant of
    whitespace:
    `r'^---\s+.*?[Tt]ype\s*:\s*["\']?(\w+)["\']?.*?---'`
*   **Logic Refactor (`_parse_artifact`):**
    ```python
    # 1. Find the YAML start
    # 2. Find the fence immediately PRECEDING the YAML (start_fence)
    # 3. Find the fence immediately FOLLOWING the content (end_fence)
    #    Use text.find("```", start_of_content_index)
    # 4. Do NOT use text.rfind("```") as it jumps to the end of the string.
    ```
*   **UI Update (`_cmd_save`):**
    Check `target_file.exists()` before opening the file handle to determine
    which UI message to print (Success vs Warning).

## 5. Execution Plan
1.  [ ] **Refactor Parsing:** Modify `src/vybz/repl.py` to implement the
        bounded `find` logic for code blocks.
2.  [ ] **Update Regex:** Relax the YAML pattern in `_parse_artifact`.
3.  [ ] **Update UX:** Add the file existence check and conditional warning in
        `_cmd_save`.
4.  [ ] **Verify:** Test with a multi-block response (Design + Python snippet)
        to ensure only the Design is saved.
