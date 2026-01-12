---
status: "Draft"
type: "Intent"
last_updated: "2026-01-11"
references: 
---

# Refresh Codebase Context via /update

When running an interactive session, the `CodeBase` snapshot is generated once 
at initialization. If I (or the agent) modify files during the session, the 
agent's "memory" of the file content becomes stale.

I want a new REPL command: `/update`.

When executed, it should:
1.  Re-scan the project directory (re-running the `CodeBase` traversal).
2.  Update the system instructions of all the chat sessions across agents with 
    the fresh snapshot.
3.  Confirm to the user that the context has been refreshed.
4.  The current date should be updated as well

This allows for long-running sessions where I can refactor code, run `/update`,
and then ask the agent to verify the changes without restarting `vybz`.
