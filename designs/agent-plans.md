---
status: "Completed"
type: "Design"
last_updated: "2026-01-11"
references: 
---

# Create an agent object.  

The agent should have the following fields

- Name - this is a short name "junior dev". "senior dev", etc
- Version - alphanumeric version.  Simple
- Role specification - long text specifying the role of that the agent will be playing
- Operating context - long text specifing the context that the agent is operating in .  This will be a high-level task.
- Task - long text which prepends any intent and gives common instructions that will be generally applied to any task

The agent should be definable in a text file. You should decide on the format toml, yaml, other. 

The agent should be have a method which when given an "intent" string will combine with role and context to create a full prompt string.
- this can then be provided to gemini by the caller.

The agent should have a log function which will return it's name and version such that a logger can log which agent it used for some conversation
