---
status: "Completed"
type: "Intent"
last_updated: "2026-01-14"
references: blueprints/no-copy-pasting.md, src/vybz/repl.py
---

# Refresh Blueprint for /save

## Context
The implementation of the `/save` command in `src/vybz/repl.py` has diverged
from the original plan in `blueprints/no-copy-pasting.md`. Specifically, the
parsing logic required iteration to handle robust artifact extraction. We moved
from simple regex/string searching to using `markdown-it-py` for token-based
parsing to correctly identify code blocks containing YAML frontmatter.

## High-Level Intent
I want to update the `blueprints/no-copy-pasting.md` file so that it accurately
reflects the current codebase. Documentation must remain the source of truth.

## Specific Updates Required
1.  **Parsing Logic:** The blueprint currently describes a regex/string-find
    approach. It needs to be updated to describe the `_parse_artifact` method's
    use of `MarkdownIt` to locate fence tokens.
2.  **Regex Details:** Update the description of how we extract the `type` and
    `title` (case-insensitive `Type`, handling of whitespace).
3.  **Fallback Behavior:** The blueprint should mention the fallback logic (if
    no code block is found, check if the whole text is the artifact).

## Desired Outcome
A `blueprints/no-copy-pasting.md` file that a developer could read and
understand exactly how the current `repl.py` works without needing to reverse-
engineer the code.
