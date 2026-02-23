---
status: "Fixed"
type: "Bug"
author: "Senior Python Architect"
last_updated: "2026-02-23"
references: src/vybz/client/api.py, src/vybz/client/session.py
---

# Bug: /agent Command Fails to Update Server-Side Session Context

## Description
When a user switches agents using the `/agent <name>` command, the TUI 
correctly updates the header to reflect the new agent. However, subsequent 
messages are still processed by the *original* agent session.

## Root Cause Analysis
The `VybzApiClient` maintains a persistent WebSocket (`self._ws`). The logic in
`_ensure_ws_connection` only checks if the socket is `OPEN`. It does not 
verify if the socket's associated `session_id` matches the current 
`self.session_id`. 

Because `switch_agent` triggers a new `start_session` (generating a new ID), 
the existing socket remains connected to the old ID, causing all future 
`chat_stream` calls to use the stale connection.

## Steps to Reproduce
1. Start `vybzd`.
2. Start `vybz-chat` (defaults to `senior-dev`).
3. Run `/agent junior-dev`.
4. Ask "Who are you?".
5. **Expected:** Agent identifies as Junior Dev.
6. **Actual:** Agent identifies as Senior Dev.

## Proposed Fix
1. Modify `VybzApiClient.start_session` to nullify `self._ws` if a new session 
   is started.
2. Update `_ensure_ws_connection` to track the `session_id` it was opened with,
   or simply force a close if the IDs don't match.
