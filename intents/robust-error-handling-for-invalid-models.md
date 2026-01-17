---
status: "Draft"
type: "Intent"
author: "Nick Orton"
last_updated: "2026-01-11"
references: 
---

# Robust Error Handling for Invalid Models

Currently, if a user specifies a model ID that does not exist or is not 
accessible via the API (e.g., `vybz junior-dev -m gemini-nonexistent`), the 
system behavior is likely brittle. It may crash with a raw Python stack trace 
or a generic API 400/404 error that is confusing to the user.

I want the system to:
1.  Gracefully catch invalid model selection errors.
2.  Display a styled, human-readable error message (e.g., "Model 'xyz' not 
    found").
3.  Ideally, list the valid available models that the user *can* use, so they 
    can correct their command immediately.
