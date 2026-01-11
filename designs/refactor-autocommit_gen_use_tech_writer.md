# Autocommit Refactor Specification

## 1. High-Level Intent
Refactor `bin/autocommit_gen.py` to replace its hardcoded system instructions
with the dynamic `agents/tech-writer.toml` persona. This centralizes prompt
management and ensures commit messages adhere to the strict styling rules
defined in the Technical Writer agent configuration. This change aligns the
script with the core `vibez.py` architecture.

Ensure that the intent as specified in `designs/git-commit-helper.md` is still
respected.

Make as few changes as possible

## 2. User Stories
* As a System Maintainer, I want `autocommit_gen.py` to load the `tech-writer`
  agent dynamically, So that I can update prompt strategies in one TOML file
  rather than multiple Python scripts.
* As a Developer, I want the commit generator to strictly follow the "Lead
  Technical Writer" persona, So that my git logs remain professional and
  consistent.

## 3. Acceptance Criteria
- [ ] `bin/autocommit_gen.py` imports `Squad` and `Agent` classes from the
  project root.
- [ ] The hardcoded `SYSTEM_INSTRUCTION` constant is removed.
- [ ] The script initializes the `tech-writer` agent using
  `Squad.get_agent("tech-writer")`.
- [ ] The `generate_message` method constructs the prompt using
  `agent.construct_full_prompt()`, passing the Diff/Context as the "Intent".
- [ ] The `client.models.generate_content` call sends the full prompt as
  `contents` (aligning with `vibez.py`), NOT as a `system_instruction` config
  parameter.
- [ ] Execution from project root (via `./bin/autocommit_gen.py`) works
  correctly without `ImportError`.

## 4. Implementation Hints (Technical)
* **Imports:** Since `bin/` is a subdirectory, you must pragmatically modify
  `sys.path` to import modules from the root:
  ```python
import sys from pathlib import Path
  # Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent)) from squad import
Squad
  ```
* **Prompt Construction:**
  - The "Intent" passed to `agent.construct_full_prompt(intent)` should be the
    formatted Diff + Logs.
  - Do not use `types.GenerateContentConfig(system_instruction=...)`. Pass the
    full constructed string as the `contents` argument.
* **Architecture:** Keep the `GeminiCommitAgent` class but inject the loaded
  `Agent` object into it or load it within `__init__`.

## 5. Execution Plan
1. [ ] **Setup Imports:** Modify `bin/autocommit_gen.py` to handle `sys.path`
   and import `Squad`.
2. [ ] **Refactor Class:** Update `GeminiCommitAgent` to load `tech-writer` via
   `Squad`.
3. [ ] **Update Generation Logic:** Replace the prompt construction logic to use
   `agent.construct_full_prompt()` and remove the legacy `system_instruction`
   config.
4. [ ] **Verify:** Run a dry `git diff --cached` check to ensure the script
   executes.
