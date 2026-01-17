---
status: "Completed"
type: "Intent"
author: "Nick Orton"
last_updated: "2026-01-11"
references: 
---

# Multi-Round Chatting with the Kartel

Currently the application takes a single user intent in from the command line 
using a mandatory argument.  I would like to have a multi-round conversation 
with the selected agent.  This should leverage the "chats.create" functionality
of the gemini client.  The chat should be configured with the 
system_instructions that give the selected agent it's personality and 
abilitites.  

I should be able to enter multiple lines of instructions to a 
chat.  There should be a key combination such as Ctl-D that Ctl-Enter that sends
the intent to the model.  The user interface should be a pretty-printed TUI


