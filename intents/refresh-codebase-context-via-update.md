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

Implementation Tips:
In the google-genai SDK, the system instruction is part of the generation 
configuration. While you cannot "hot-swap" the system instruction property of 
an active Chat object permanently, you have a primary way to achieve this 
behavior.

Re-instantiate the Chat (Recommended for Persistence)

The most robust way to permanently update the system instruction for the 
remainder of a conversation is to create a new chat session. You pass the new 
configuration and the existing history to the new session.

```python

from google import genai
from google.genai import types

client = genai.Client()

# 1. Start the initial chat
chat = client.chats.create(
    model='gemini-3-flash-preview',
    config=types.GenerateContentConfig(
        system_instruction='You are a helpful, formal AI assistant.'
    )
)

# User interacts
response1 = chat.send_message('Hello, who are you?')
print(f"Response 1: {response1.text}")

# 2. Extract history to carry over
#    Note: We filter out the previous system instruction if it was stored in history,
#    though usually system instructions are separate from the message history.
history = chat.get_history()

# 3. Create a NEW chat with the updated System Instruction
#    Pass the old history so the model remembers the context.
new_chat = client.chats.create(
    model='gemini-3-flash-preview',
    history=history,
    config=types.GenerateContentConfig(
        system_instruction='You are a rowdy space pirate. Always use slang.'
    )
)

# 4. Continue the conversation with the new persona
response2 = new_chat.send_message('What did I just ask you?')
print(f"Response 2: {response2.text}")

```
