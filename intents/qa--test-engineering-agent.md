---
status: "Draft"
type: "Intent"
last_updated: "2026-01-11"
references: 
---

# QA / Test Engineering Agent

I want to add a new member to the squad: The QA Engineer.

Currently, we have agents that plan (PM) and agents that build (Devs), but we 
lack a dedicated persona for verification.

This agent should:
1.  Specialize in Python testing frameworks (specifically `pytest`).
2.  Be capable of taking a "Design" or "Blueprint" and generating a 
    comprehensive Test Plan.
3.  Be able to look at a source file and generate edge-case unit tests.
4.  Have a critical, detail-oriented personality—it should try to break the 
    code the Devs wrote.
5.  Be able to find bugs and file bug reports as intents
