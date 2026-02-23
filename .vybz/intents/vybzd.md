---
status: "Completed"
type: "Intent"
author: "Lead Technical Writer"
last_updated: "2026-02-06"
references: 
---

# ADK Refactor

## Context
Currently, Vybz communicates directly with Google models via the `google-genai`
SDK. While functional, this monolithic approach limits scalability and advanced
agent orchestration capabilities. Google has released the Agent Development Kit
(ADK), which provides a standardized framework for building, deploying, and 
managing AI agents.

## High-Level Intent
I want to perform a **major architectural refactor** of the Vybz codebase to 
migrate the underlying communication layer from the raw `google-genai` SDK to 
the **Google Agent Development Kit (ADK)**.

This is a fundamental shift that will likely involve splitting the application 
into a Client/Server architecture. PMs and Senior Developers must exercise 
"Deep Thinking" to plan this transition carefully.

## References
*   **Python ADK Docs:** [https://github.com/google/adk-python](https://github.com/google/adk-python)
*   **Core ADK Docs:** [https://google.github.io/adk-docs/](https://google.github.io/adk-docs/)

## Requirements & Architectural Thoughts

### 1. Phased Migration
This is too large for a single sprint. The plan must be broken down into 
distinct, safe phases (e.g., Proof of Concept, Core Migration, TUI Separation).

### 2. Client-Server Split
*   **Client:** The existing TUI (REPL, `rich` rendering, `prompt_toolkit` 
    input) should evolve into a lightweight client.
*   **Server:** The ADK runtime should likely operate as a backend service.
*   **Communication:** The Client and Server should communicate via a robust 
    streaming protocol (likely WebSockets) to maintain the real-time 
    "Vibe Coding" feel.

### 3. Agent Architecture
*   **Server Instances:** Investigate if we need a single server instance per 
    Agent Persona, or a unified server managing a squad.  Perhaps we should
    leverage the native server functionality
*   **Management Tools:** We will need CLI utilities to spin up, monitor, and 
    shut down these agent server instances.

### 4. Configuration Compatibility
*   We **must** preserve our existing investment in Agent (`.toml`) and Skill 
    (`SKILL.md`) configuration files.
*   The refactor must include logic to parse these Vybz-specific configurations
    and hydrate the corresponding ADK Agent instances.

