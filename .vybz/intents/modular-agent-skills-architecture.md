---
status: "In Progress"
type: "Intent"
last_updated: "2026-01-12"
references: 
---

# Modular Agent Skills Architecture

## Context
Currently, `vybz` agents are defined as monolithic TOML files. Information
such as "How to use the Google GenAI SDK" or "How to format Markdown" is
duplicated across multiple agents (`junior-dev`, `senior-dev`, `pm`). This
violates the DRY (Don't Repeat Yourself) principle and makes updating shared
knowledge brittle and tedious.

## High-Level Intent
I want to refactor the Agent domain model to support **Skills**. A "Skill" is a
modular, reusable unit of context or capability that can be attached to one or
more agents.

## Core Requirements

### 1. File Structure
*   Skills should be defined in a new directory: `src/vybz/agents/skills/`.
*   Like Agents, Skills should be defined in TOML (or Markdown) files containing
    their specific instructions and context.

### 2. Domain Model Separation
*   The `Agent` class should no longer hold all context text directly.
*   Introduce a `Skill` class/object in the domain model.
*   The `Agent` TOML definition should support a list of references, e.g.:
    ```toml
    skills = ["python-sdk-v1-57", "git-operations", "freebsd-sysadmin"]
    ```
*   The toml schema for a skill should consist of two lists: "knowledge" and 
    "abilities".  Each list is a list of string.  These are expected to be 
    multi-line strings

### 3. Dynamic Composition
*   When an Agent is initialized (via `Squad`), it should dynamically load the
    referenced skills.
*   The `construct_agent_role_profile()` method must iterate through the
    attached skills and append their `instructions` to the final System Prompt.
*   There should be the ability to add a skill via a special command from the 
    user input.  /upskill <agent> <skill>.  This feature should be implemented 
    towards the end.

### 4. Shareability
*   Multiple agents must be able to reference the same skill file. For example,
    both `junior-dev` and `senior-dev` should import the `google-genai-sdk`
    skill, ensuring they both use the exact same API syntax standards.

## Desired Outcome
This refactor will allow us to update the "Stack" definitions (OS, SDK versions,
Coding Standards) in a single location and have those updates instantly propagate
to every agent in the Squad.
