---
status: "Draft"
type: "Design"
last_updated: "2026-01-14"
references: intents/clean-patches-post-extraction-validation.md, blueprints/save-diffs--patches-implementation-plan.md
---

# Diff Sanitization & Validation Specification

## 1. High-Level Intent
Implement a robust post-processing pipeline for generated Unified Diffs. LLMs
frequently generate "sloppy" diffs—missing leading spaces for context lines,
incorrect line counts in hunk headers, or missing trailing newlines. This feature
introduces a `DiffSanitizer` module that programmatically repairs these structural
defects before the artifact is saved to disk. This ensures that the user can
confidently run `patch -p1 < file.diff` without encountering "malformed patch"
errors.

## 2. User Stories
* As a User, I want the system to automatically fix missing leading spaces in
  diff context lines, so that `patch` recognizes them as context rather than
  garbage.
* As a User, I want the hunk headers (e.g., `@@ -10,5 +10,6 @@`) to be
  mathematically correct based on the actual content, even if the Agent failed
  arithmetic.
* As a Developer, I want diff logic isolated in its own module (`diff_utils.py`)
  to keep `artifact.py` focused on routing and persistence.

## 3. Acceptance Criteria
- [ ] **Dependency:** `unidiff` library is added to `pyproject.toml`.
- [ ] **Module:** `src/vybz/diff_utils.py` is created.
- [ ] **Heuristic Repair:** The sanitizer detects context lines that lack a
      leading space (lines not starting with `+`, `-`, `@`, or space) and
      prepends a space.
- [ ] **Header Recalculation:** The sanitizer parses the text into a `PatchSet`,
      recalculates the line counts for every hunk, and re-serializes the output.
- [ ] **Integration:** `ArtifactProcessor.save` (in `src/vybz/artifact.py`)
      calls the sanitizer when `artifact.type == "Diff"`.
- [ ] **Validation:** If the diff is unsalvageable (e.g., total garbage), the
      system saves the raw output but warns the user.

## 4. Implementation Hints (Technical)
*   **Library:** Use `unidiff` (`pip install unidiff`). It handles parsing and
    emitting standard diffs.
*   **Two-Stage Process:**
    1.  **Text Repair (Pre-Parse):** `unidiff` will throw an error if the input
        is malformed. You must run a regex pass *first* to ensure context lines
        have spaces.
        *   *Regex:* If a line does not start with `[-+@ ]` and is not inside a
            header, prepend ` `.
    2.  **Object Repair (Post-Parse):** Load the repaired text into `unidiff.PatchSet`.
        *   The library automatically calculates counts when you access properties
            or convert back to string.
*   **Architecture:**
    ```python
    # src/vybz/diff_utils.py
    def sanitize_diff(raw_diff: str) -> str:
        # 1. Fix missing spaces via Regex/String manipulation
        # 2. Parse with unidiff
        # 3. Return str(patch_set)
    ```

## 5. Execution Plan
1.  [ ] **Setup:** Add `unidiff` to `pyproject.toml`.
2.  [ ] **Core Logic:** Create `src/vybz/diff_utils.py` and implement the
        text-repair heuristics and `unidiff` integration.
3.  [ ] **Integration:** Modify `src/vybz/artifact.py` to import `diff_utils`
        and apply `sanitize_diff` inside the `save` method (or `parse` method)
        when handling Diffs.
4.  [ ] **Testing:** Create `tests/vybz/test_diff_utils.py` with specific test
        cases for:
        *   Missing context space.
        *   Wrong header math.
        *   Multiple files in one patch.
