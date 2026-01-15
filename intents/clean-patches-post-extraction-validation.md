---
status: "Completed"
type: "Intent"
last_updated: "2026-01-14"
references: src/vybz/artifact.py, intents/malformed-diff-patches-missing-context-space.md
---

# Clean Patches (Post-Extraction Validation)

## Context
While we have updated the `diff-generation` skill to instruct Agents on proper
Unified Diff syntax, LLMs are inherently probabilistic and struggle with exact
arithmetic (line counting) and invisible characters (leading spaces).

Currently, `vybz` saves the raw string output from the LLM. If the Agent
miscounts lines in the Hunk Header or forgets a space, the `patch` utility
rejects the file, forcing the user to manually fix the diff.

## High-Level Intent
I want a programmatic safety net implemented in the `ArtifactProcessor`. Before a
diff artifact is saved to disk, it should be passed through a cleaning routine
that ensures it is syntactically valid.

## Implementation Requirements

### 1. Dependency
*   Add `unidiff` (or similar robust parsing library) to `pyproject.toml`.

### 2. Logic (`src/vybz/artifact.py`)
*   When `ArtifactProcessor` detects a `Diff` type:
    1.  Ingest the raw string into a `unidiff.PatchSet` (or equivalent).
    2.  **Sanitize Hunks:** Iterate through hunks and programmatically recalculate
        the line counts based on the actual content provided.
    3.  **Sanitize Whitespace:** Detect context lines that are missing the
        mandatory leading space and inject it.
    4.  **Sanitize EOF:** Ensure the file ends with a newline.
    5.  **Serialize:** Write the corrected, strictly formatted string to the
        `.diff` file.

### 3. Approach
*   Independent diff processing module:  The artifact.py module is getting
    prett messy.  I believe that we may want to leverage diffs in more ways
    in the future and that it should be a key to how vybz works efficiently.
    I would like the logic for sanitizing diffs to be in it's own module that
    the save method in artifact.py uses before saving to disk.

## Desired Outcome
A user can run `/save`, receive a `.diff` file, and immediately run
`patch -p1 < output.diff` without encountering "malformed patch" errors due to
simple formatting slips by the AI.
