---
status: "Draft"
type: "Bug"
author: "Principal QA Engineer"
last_updated: "2026-02-06"
references: src/vybz/agents/pm.toml, src/vybz/artifact.py
---

# Design Artifacts Misrouted to Output Due to Missing Metadata

## 1. Symptom
When the **PM Lead** agent generates a Design Specification (e.g., `artifact-114959.md`), the file is saved to `.vybz/output/` with a generic timestamp filename, instead of being routed to `.vybz/designs/` with a semantic filename.

## 2. Root Cause Analysis
The issue stems from a conflict between the Agent's specific `task_directive` and the general `vybz-artifact-metadata` skill.

1.  **Primary Defect (Prompt Engineering):**
    In `src/vybz/agents/pm.toml`, the `task_directive` explicitly defines an **Output Format** template that begins with an H1 Header:
    ```markdown
    Output Format (Strict Markdown, Max Line Length: 79 chars):

    # [Project Name] Specification
    ...
    ```
    The Agent follows this template strictly, ignoring the instruction from the `vybz-artifact-metadata` skill to include YAML Frontmatter. Without the `type: Design` frontmatter, the `DocumentHandler` in `artifact.py` fails to recognize the content as a Design.

2.  **Secondary Defect (Code Robustness):**
    When the `ArtifactProcessor` falls back to the "Raw Text Rescue" logic (Step 3), it defaults to generating a filename based on the current timestamp (`artifact-{ts}.md`). It fails to attempt extracting the H1 header (`# Agents and Skills...`) to generate a human-readable filename, which would at least make the misrouted file identifiable.

## 3. Proposed Fixes

### 3.1. Remediation (Agent Configuration)
Update `src/vybz/agents/pm.toml` to include the YAML Frontmatter block in the `task_directive` template.

**Change:**
```toml
# src/vybz/agents/pm.toml

task_directive = """
...
Output Format (Strict Markdown, Max Line Length: 79 chars):

```yaml
---
status: "Draft"
type: "Design"
author: "PM Lead"
last_updated: "{{DATE}}"
references: {{INTENT_FILE}}
---
```

# [Project Name] Specification
...
"""
```

### 3.2. Robustness (Artifact Processor)
Update `src/vybz/artifact.py`'s fallback logic. If no specific handler matches, the fallback should still attempt to run the H1-to-Filename regex on the raw text. This ensures that even if `type` is missing, we get `agents-library-spec.md` instead of `artifact-114959.md`.

## 4. Verification
1.  Apply the change to `pm.toml`.
2.  Run `vybz pm "Design a simple hello world"`.
3.  Verify the output contains `type: Design`.
4.  Run `/save`.
5.  Verify the file appears in `.vybz/designs/` with a proper name.
