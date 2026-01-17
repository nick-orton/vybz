---
status: "Completed" 
type: "Intent" 
author: "Nick Orton"
last_updated: "2026-01-11" 
references: 
---

# Agent Switching

When working in the REPL I want to be able to switch the agents that I am
talking to.
- I should do it with a special command: /agent
- I should be able to either include the agent name or be prompted to choose
  one from a list
- Each agent should have it's own role profile in a unique chat context.  If I'm
  starting a conversation with the PM and then switch to the senior-dev, it
  should have a new history and the pm role shouldn't be in the context.  the
  senior-dev should be.
- If I switch back to a previous agent I was already talking to, it should have
  the memory and context of the previous conversation
