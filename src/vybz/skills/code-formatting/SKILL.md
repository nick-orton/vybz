---
name: code-formatting
description: Ensuring that code is well formatted
---

# Code Formatting
_Ensuring that code is well formatted_

### Marking filenames for saving to file systems

**Filenames:**
*   Getting filenames correct is critical for ensuring that it will be saved
    into the right location in the codebase.  Files that are saved to the
    codebase should have the full path relative to the project root.
*   **Filename Metadata:** You MUST include the full filename as a comment on 
    the FIRST LINE inside the code block.
    Format: `# filename: path/to/file.ext`
*   **Shebangs:** For scripts requiring a shebang (e.g., `#!/bin/sh`), place 
    the filename comment on Line 1 and the shebang on Line 2. The system will 
    automatically strip the comment line upon saving, ensuring the shebang 
    becomes valid.

