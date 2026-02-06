---
name: vybz-artifact-metadata
description: The standards used to tag vybz design artifacts
---

# Vybz Artifact Metadata
_The standards used to tag vybz design artifacts_

## Knowledge
* ### Vybz Design Organization
  - The .vybz/intents/ folder contains human-created user intents.  These are
    instructions for agents to intepret and further specify. 
    - Bug reports belong in the .vybz/bugs/ folder
    - Critiques belong in the .vybz/critiques/ folder
  - .vybz/designs/ folder contains feature specs and high-level designs created
    by the PM for devs to implement
  - .vybz/blueprints/ folder contains high level architecture designs created
    by developers
  
  ## Metadata Standard: YAML Frontmatter
  You must inject or update YAML Frontmatter at the very top of Markdown files.
  Use this strict schema:
  
  ```yaml
  ---
  status: "Draft"        # Options: [Draft, In Progress, Blocked, 
                                     Completed, Deprecated]
  type: "Design"         # Options: [Design, Intent, Blueprint, Bug, Critique]
  author: "{{Your Agent Name}}" # Your full Identity Name (e.g. "PM Lead")
  last_updated: "YYYY-MM-DD" # Use current date if known, otherwise Today
  references: designs/foo.md, designs/bar.md  # Any other spec artifacts that 
                                                this design references
  ---
  ```
* Critiques are reviews which can be created by ux-designers, pms or developers (or anyone really) that
  evaluate the current design and implementation of the system and offer remedies.  A PM can take a critique
  and turn the remediation into a design.
* **Path Awareness:** You know that: 
  - design docs live in `.vybz/designs/` 
  - user intents live in `.vybz/intents/` 
  - bugs live in `.vybz/bugs/` 
  - blueprints live in `.vybz/blueprints/` 
  - critiques live in `.vybz/critiques/`
* The `.vybz` folder in the project workspace contains the vybz artifacts
* New artifacts: (Designs, Blueprints, Intents) should always be in 'Draft' state
  when first created

## Abilities
* metadata organization and tagging of documents.
* YAML Frontmatter specification
* metadata organization and tagging of documents.
* YAML Frontmatter specification
* Always populate the `author` field with your Agent Name (e.g., 'PM Lead', 'Senior Python Architect') when creating new artifacts.
