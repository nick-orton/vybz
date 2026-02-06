---
name: unified-diff-generation
description: Expertise in generating rigorous, patch-compatible Unified Diffs for
  the 'patch' utility.
---

# Unified Diff Generation
_Expertise in generating rigorous, patch-compatible Unified Diffs for the 'patch' utility._

## Knowledge
* #### The Unified Diff Standard
      *   **Format:** We strictly use the Unified Format (`diff -u`).
      *   **Headers:**
          *   Original file: `--- a/path/to/file`
          *   New file:      `+++ b/path/to/file`
          *   **Crucial:** The `a/` and `b/` prefixes are mandatory to allow standard `patch -p1` usage.
      *   **Hunks:**
          *   Header: `@@ -start,length +start,length @@`
          *   Context: Must include exactly **3 lines** of unchanged context before and after the change.
      *   **New Files:** Represent original file as `--- /dev/null`.
      *   **Deleted Files:** Represent new file as `+++ /dev/null`.
      *   Context: Include exactly 3 lines of unchanged context before and after every change.
      *   No Truncation: Do not use comments like // ... existing code ... inside the code blocks. Write out the full lines.
      *   Headers: Ensure the @@ -old,lines +new,lines @@ headers accurately match the line counts.
      *   Whitespace: Preserve indentation exactly.
      *   Final Newline: Ensure the very last line of the diff block ends with a newline character.
* #### Patch Utility Constraints
      *   **Whitespace:** The `patch` utility is unforgiving. Context lines must match the source exactly, including indentation.
      *   **Fuzz:** While `patch` can handle some line number drift ("fuzz"), it rejects patches where context text does not match.
      *   Final Newline: Ensure the very last line of the diff block ends with a newline character.
* The Unified Diff standard requires that lines in a hunk start with a specific 
      character:
      *   `+` (Addition)
      *   `-` (Deletion)
      *   ` ` (Space - Context)
* #### Context Line Syntax
      *   **Mandatory Leading Space:** Every context line (a line that is not a
          `+` or `-`) MUST start with a single space character.
      *   **Failure Mode:** If this space is missing, the `patch` utility will 
      reject the file as malformed.
* "Uniqueness: Ensure the context lines provided are unique enough that patch doesn't insert the code in the wrong place."
* "Strict Header Math: The second number in the header (e.g., +321,51) 
      represents the TOTAL vertical height of the block. 
      Formula: Length = (Top Context Lines) + (Added/Modified Lines) + (Bottom Context Lines). 
      Warning: Do not just count the green added lines. You must add the context 
      lines to that count."

## Abilities
* Outputting changes inside markdown code blocks tagged `diff` or `patch`.
* Ensuring the file paths in the diff headers are relative to the project root.
* Calculating line counts for hunk headers (`@@ -old,len +new,len @@`) with high precision.
* Verifying that the 'Context' lines provided in the diff exist verbatim in the current CodeBase snapshot.
* Verifying that every context line in the diff block starts with a literal space character ' '.
* Verifying Final Newline: Ensure the very last line of the diff block ends with a newline character.
* Refusing to generate a diff if the file content is not in the context window (to avoid hallucinating context).
* "Step-by-Step Diff Generation: Before outputting the final code block, explicitly calculate the line counts in a temporary format.
      Count the Header Context lines (usually 3).
      Count the New Body lines.
      Count the Footer Context lines (usually 3).
      Sum them up to get the chunk length.
      Only THEN generate the final diff block with the correct integers."
