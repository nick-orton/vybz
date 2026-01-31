---
status: "Draft"
type: "Intent"
author: "Lead Technical Writer"
last_updated: "2026-01-29"
references: 
---

# Load file Functionality

## Context
Currently, the `CodeBase` context is determined solely by the root directory specified at startup (or the CWD). Users cannot easily inject specific files that might be outside this tree or ignored by `.gitignore` without modifying the project structure. Furthermore, relying solely on `/update` to refresh the entire tree can be heavy if the user just wants to add one specific reference file to the conversation.

## High-Level Intent
I want to implement a `/load <filename>` command in the REPL. This command allows the user to manually inject the content of a specific file into the active Agent's context window.

## Requirements

### 1. The Command
*   **Syntax:** `/load <filename>`
*   **Path Resolution:** The filename argument should be resolved relative to the Current Working Directory (CWD) of the running `vybz` instance.

### 2. Persistence Strategy
*   **State Tracking:** Files loaded via `/load` must be tracked separately from the automatic `CodeBase` snapshot.
*   **Durability:** When the user runs `/update` (which refreshes the `CodeBase` from disk), the manually loaded files **must not be lost**. They should be re-read and re-injected into the new system instruction alongside the refreshed CodeBase.

### 3. User Experience
*   **Feedback:** The system should confirm success: "Loaded [filename] into context."
*   **Error Handling:** If the file does not exist or is unreadable, display a clear error message.

