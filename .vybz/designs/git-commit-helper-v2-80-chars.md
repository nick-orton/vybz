---
status: "Completed"
type: "Design"
author: "Nick Orton"
last_updated: "2026-01-10"
references: designs/git-commit-helper.md
---

## Git Commit helper refactor

Refactor the code: autocommit_gen.py

The goal of this refactor is to ensure that no line of the output is longer than
79 characters. The text should be elegantly rendered so that it neatly wraps.
