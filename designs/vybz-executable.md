---
status: "Completed"
type: "Design"
last_updated: "2026-01-10"
references: 
---

# Vybz Executable CLI Refactor Specification

## 1. High-Level Intent
Refactor the core entry point (`src/vybz/tools/work.py`) to transition from
hardcoded configuration values to a flexible Command Line Interface (CLI). This
enables users to dynamically select agents, models, and intents without editing
source code, significantly reducing friction and increasing the "Flow" state of
the Vibe Coding experience.

## 2. User Stories
* As a User, I want to run `vybz` with the agent and intent as arguments so that
  I can trigger a task in a single command (e.g., `vybz junior-dev "Fix the
  bug"`).
* As a User, I want reasonable defaults for the Model and Log File so that I
  don't have to specify them for every run.
* As a User, I want to specify a custom `--codebase` path so that I can run the
  tool against different directories. If no codebase is supplied the agents act
  as if this is greenfield development. The code is robust to ensure there are 
  no null-pointer errors
* As a User, I want to see help output (`-h`) so that I can remember available
  flags. This will tell me the available agents and models. This should be static
  content.

## 3. Acceptance Criteria
- [ ] `src/vybz/tools/work.py` utilizes `argparse` to handle arguments.
- [ ] **Agent** is a MANDATORY positional argument (e.g., first argument).
- [ ] **Intent** is a MANDATORY positional argument (e.g., second argument).
- [ ] **Model** is optional; defaults to `"gemini-3-pro-preview"`. (Flag: `-m` /
  `--model`).
- [ ] **Log File** is optional; defaults to `"/tmp/vybz.log"`. (Flag: `-l` /
  `--log-file`).
- [ ] **Codebase** is optional; defaults Nothing. (Flag:
  `-c` / `--codebase`).
- [ ] If the agent specified does not exist in `Squad`, the script exits
  gracefully with a list of available agents.
- [ ] The script executes the `vibez.generate_and_continuous_log` function using
  the parsed arguments.

## 4. Implementation Hints (Technical)
* **Library:** Use standard `argparse`.
* **Argument Structure:**
  ```python
parser.add_argument("agent", help="Target Agent (e.g., junior-dev)")
parser.add_argument("intent", help="Task description") parser.add_argument("-m",
"--model", default="gemini-3-pro-preview") parser.add_argument("-l", "--log-
file", default="/tmp/vybz.log") parser.add_argument("-c", "--codebase",
default=".", help="Root path")
  ```
* **Validation:**
  * Ensure `Squad.get_agent` call is wrapped in a `try/except` block to catch
    `ValueError` if the agent doesn't exist.
  * Resolve `--codebase` to a `Path` object immediately.

## 5. Execution Plan
1. [ ] **Setup Argparse:** Rewrite `main()` in `src/vybz/tools/work.py` to
   initialize `argparse.ArgumentParser` and define the arguments specified
   above.
2. [ ] **Connect Logic:** Replace hardcoded `TARGET_AGENT`, `TARGET_MODEL`,
   `INTENT`, etc., with values from `args`.
3. [ ] **Error Handling:** Add check to print valid agents if the user provides
   an invalid agent name.
4. [ ] **Test:** Verify `vybz -h` outputs help, and `vybz pm "Test"` executes
   correctly.
