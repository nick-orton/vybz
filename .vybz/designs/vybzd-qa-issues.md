---
status: "Completed"
type: "Bug"
author: "Principal QA Engineer"
last_updated: "2026-02-18"
references: 
  - designs/vybzd.md
  - blueprints/vybzd/vybzd-step-3-engine-implementation.md
---

## 1. WebSocket Stream Exhaustion (One-Shot per Connection)
The current WebSocket implementation in `src/vybz/server/main.py` is designed 
as a "one-shot" interaction. It receives one JSON message, consumes the 
generator, and then the function terminates (or wait for a disconnect).

**The Symptom:**
The REPL will successfully send the first message, but subsequent messages in 
the same session may fail or require a complete WebSocket reconnect, which is 
inefficient and not idiomatic for long-running chat sessions.

**Root Cause:**
```python
# src/vybz/server/main.py
@app.websocket("/session/{session_id}/chat")
async def chat_endpoint(websocket: WebSocket, session_id: str):
    ...
    try:
        data = await websocket.receive_json() # <--- Only called once
        ...
        for event in events:
            await websocket.send_text(...)
    except WebSocketDisconnect:
        pass
    # Function ends here, closing the socket.
```

## 2. Inconsistent Event Property Access (Runtime AttributeErrors)
In `src/vybz/server/main.py`, the code accesses `event.content.parts` without 
verifying that `event.content` exists on the specific event object yielded by 
the ADK Runner. ADK `Runner.run()` can yield various event types (status 
updates, tool calls, etc.) that may not have a `content` attribute.

**The Symptom:**
The server will crash with an `AttributeError: 'NoneType' object has no 
attribute 'parts'` or similar during specific model behaviors (like tool 
calling or "Thinking" transitions), causing the REPL to show a generic 
"Generation Error".

**Root Cause:**
```python
for event in events:
    if event.content and event.content.parts: # <--- Vulnerable if event has no 'content'
```

## 3. Tool Execution Isolation (Path Injection Risk)
The `FileSystemTools` implemented in `src/vybz/server/tools/fs.py` uses 
`rel_path` directly. While there is a check for `startswith(str(self.root))`, 
the `rel_path` is joined to `self.root` before normalization in some cases, 
and the security check relies on string prefixing which can be bypassed with 
symlinks if the OS allows.

**The Symptom:**
An agent could potentially be tricked into reading files outside the project 
root if symlinks are present, or if the `rel_path` is maliciously crafted 
(though `resolve()` mitigates some of this).

## 4. Race Condition in Instruction Hot-Reloading
When `/load` or `/uplevel` is called, 
`ServerState._refresh_session_instructions` updates the 
`runner.agent.instruction` string. However, if a chat is currently in progress 
on the WebSocket thread, the ADK Runner may have already snapshotted the 
instructions for the current turn.

**The Symptom:**
The user runs `/load file.py`, then immediately asks a question about 
`file.py`. The agent might reply "I don't see that file" because the runner 
was initialized with the old instruction set just milliseconds before the update.

## 5. REPL ANSI Leakage in Logs
The server sends "Thinking" parts with ANSI color codes 
(e.g., `\033[36m💭 ...`) directly over the WebSocket. The REPL's 
`InteractionLogger` in `src/vybz/repl.py` captures the `full_response` which 
includes these raw ANSI strings.

**The Symptom:**
The session log files (`/tmp/vybz.log`) will be cluttered with raw escape 
sequences, making them difficult to read with standard text editors or use 
for further processing.

## 6. Model ID Mismatch (Hardcoded vs Config)
`ServerState` initializes with a hardcoded `gemini-3-flash-preview`, but 
`ConfigLoader` might provide a different one. The `AdkHydrator.hydrate_agent` 
takes a `model` string, but the `ServerState` doesn't seem to propagate updates 
to existing runners if the config changes during runtime.

## Recommended Remediation
1.  **Wrap the WebSocket handler in a `while True:` loop** to allow multiple 
    turns over a single connection.
2.  **Use `getattr(event, 'content', None)`** or proper type-checking against 
    ADK event classes.
3.  **Sanitize ANSI codes** in the `InteractionLogger` before writing to disk.
4.  **Implement a Lock or Semaphore** in `ServerState` to ensure instruction 
    updates don't happen during an active `runner.run()` execution.
