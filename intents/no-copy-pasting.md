---
status: "Draft"
type: "Intent"
last_updated: "2026-01-11"
references: 
---

# End of the Copy and Pasting

I'm tired of copying and pasting things from the log file.  Let's start with 
designs.  If a PM creates a design or a Senior Dev creates a blueprint, I should
have a /save command that will persist those markdown files to disk in the 
appropriate directory.

Features 
- It's codebase aware.  Designs go in /designs and blueprints in /blueprints
  - in the root of the specified codebase
  - if no codebase is specified and we're in greenfield mode, it assumes the
    working directory is the codebase.
  - if no directories exist it creates them.
- It will save the latest version if I have asked it to iterate on the blueprint
  in the chat.
