---
status: "Draft"
type: "Design"
last_updated: "2026-01-16"
references: intents/ux-critique.md
---

# REPL Prompt Conciseness Refactor

## 1. High-Level Intent
Address the "Horizontal Sprawl" friction point identified in the UX Critique.
Currently, the REPL prompt utilizes the verbose, human-readable Agent Name
(e.g., `[Tactical Python Architect] >>`), which consumes excessive horizontal
screen real estate. This pushes the user's cursor to the middle of the screen,
breaking the visual flow. We will refactor the prompt to use the concise
Agent ID (e.g., `junior-dev`) and a modern separator.

## 2. User Stories
* As a User, I want the REPL prompt to display `junior-dev` instead of
  `[Tactical Python Architect]`, so that I have more space to type commands on
  split-screen terminals.
* As a User, I want the prompt to be minimal and unobtrusive, removing unnecessary
  brackets and visual noise.

## 3. Acceptance Criteria
- [ ] **Data Source:** The prompt string uses `self.active_agent.id` (the
      filename stem) instead of `self.active_agent.name`.
- [ ] **Visual Noise:** The surrounding brackets `[]` are removed from the
      agent label.
- [ ] **Separator:** The generic `>>` characters are replaced with the cleaner
      Unicode arrow `❯` (U+276F) to save space and improve aesthetics.
- [ ] **Fallback:** If no agent is active (edge case), it defaults to `vybz`.

## 4. Implementation Hints (Technical)
*   **Module:** `src/vybz/repl.py`
*   **Location:** Inside the `ReplSession.start()` loop.
*   **Logic Change:**
    Current:
    ```python
    prompt_text = HTML(f"<b><style fg='cyan'>[{self.active_agent.name}]</style></b> >> ")
    ```
    Target:
    ```python
    # Use ID for brevity
    label = self.active_agent.id if self.active_agent else "vybz"
    prompt_text = HTML(f"<b><style fg='cyan'>{label}</style></b> ❯ ")
    ```
    *(Note: While the critique mentions dynamic styling, this specific design
    focuses strictly on the text content/length aspect of Point 1. Styling is
    a separate concern.)*

## 5. Execution Plan
1. [ ] **Refactor Prompt Logic:** Modify `src/vybz/repl.py` to swap `.name`
       for `.id`.
2. [ ] **Update Separator:** Change the trailing string from `>> ` to `❯ `.
3. [ ] **Verify:** Launch `vybz junior-dev` and ensure the prompt is short.
