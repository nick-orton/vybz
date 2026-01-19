---
status: "Draft"
type: "Intent"
author: "Lead Technical Writer"
last_updated: "2026-01-19"
references: 
---

# Restructure Vybz Artifacts

## Context
Currently, Vybz design artifacts (intents, designs, blueprints) and output files are generated in the root or loose directories of the codebase. This "pollutes" the active workspace, mixing meta-documentation with actual source code.

## Objective
Encapsulate all Vybz-related metadata, configuration, and generated artifacts into a single hidden directory (`.vybz/`) to maintain a clean workspace root.

## Requirements

### 1. Root Directory
- Create a hidden directory named `.vybz` at the root of the project.

### 2. Directory Structure
All artifact types must be moved to specific subdirectories within `.vybz`:

| Artifact Type | Old Location (Implicit) | New Location |
| :--- | :--- | :--- |
| **Intents** | `intents/` | `.vybz/intents/` |
| **Designs** | `designs/` | `.vybz/designs/` |
| **Blueprints** | `blueprints/` | `.vybz/blueprints/` |
| **Output** | `output/` | `.vybz/output/` |
| **Bugs** | `intents/` (mixed) | `.vybz/bugs/` |
| **Critiques** | `intents/` (mixed) | `.vybz/critiques/` |

### 3. Implementation Details
- The system must check for the existence of `.vybz/` and create it if missing.
- `bugs` and `critiques` are promoted to top-level citizens within the `.vybz` namespace, rather than being treated as generic intents.
- `.gitignore` should be updated to ignore `.vybz/output/` while potentially preserving the design artifacts (intents/designs/blueprints) if they are intended to be version controlled.

## Acceptance Criteria
- [ ] A `.vybz/` directory exists.
- [ ] No Vybz artifacts appear in the project root.
- [ ] New artifacts are automatically routed to their respective folders inside `.vybz/`.
