---
status: "Draft"
type: "Intent"
last_updated: "2026-01-12"
references: intents/modular-agent-skills-architecture.md
---

# Advisor agent creates skills

I want to create the notion of "skills".  

A skill is:
- a top-level attribute of agents.
- Agents will be defined with and dynamically load skills.
- Skills are a unit of knowledge and ability that an agent can have
- Skills will eventually have a toml file which defines them although it hasn't
  been defined yet.  A skill is a list of abilities and a list of "facts" that
  the agent knows

The advisor Agent can
- be able to draft skills.
- create agents with skills from the available skills library
- I would also like the advisor agent to be able to read the other agents and
  suggest common abilities than can be refactored into a skill
