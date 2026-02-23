---
status: "Complete"
type: "Intent"
author: "Nick Orton"
last_updated: "2026-01-12"
references: intents/refresh-codebase-context-via-update.md
---

# Save Code from Agent Interactions

## Context
Currently, the `vybz` REPL allows for immediate saving of the most recent
artifact via the `/save` command. However, there is no easy way to extract code
or artifacts when multiple files are created.  

## Problem
When a developer implements a blueprint, they may write code for one or more
modules.  I want to be able to save these modules.  I also want to be able to
save diff patches when they are generated.

## Desired Outcome
- when /save is chosen for a response, the modules are saved in their correct
  location in the code base.  
- if a diff patch is created, save it in a /patches directory
- if there are multiple modules in a response prompt the user to save y/n for
  each module.
  - indicate if the save will overwrite an existing file
- the codebase is updated for all the agents when a new file is saved
