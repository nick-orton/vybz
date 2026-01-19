---
status: "Completed"
type: "Intent"
author: "Lead Technical Writer"
last_updated: "2026-01-16"
references: src/vybz/agents/skills/vybz-metadata.toml
---

# Agents Sign Their Design Docs

## Context
Currently, Vybz artifacts (Designs, Blueprints, Intents) track `status` and
`type`, but they lack attribution. It is difficult to distinguish at a glance
whether a document was authored by a specific Agent (e.g., "PM Lead") or a
Human User.

## High-Level Intent
I want to update the Vybz Metadata Standard to include an `author` field.

## Requirements
1.  **Schema Update:** The YAML Frontmatter standard must include an `author`
    key.
2.  **Agent Behavior:** When an Agent (PM, Dev, Tech Writer, etc.) drafts a
    new document (Bug, Design, Intent, Critique), they must populate the
    `author` field with their own Name/Identity.
3.  **Human Behavior:** Humans should sign their Intents similarly.

## Desired Outcome
The metadata block for all future artifacts should look like this:

```yaml
---
status: "Draft"
type: "Blueprint"
author: "Senior Python Architect"
last_updated: "2026-01-16"
references: ...
---
```
