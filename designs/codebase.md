---
status: "Completed"
type: "Design"
last_updated: "2026-01-10"
references: 
---

# CodeBase Object Specification

## 1. High-Level Intent
Develop a Python class `CodeBase` that acts as a read-only snapshot of a local
source directory. Its primary function is to ingest a directory path, traverse
it while respecting `.gitignore` rules, and serialize the entire valid source
tree into a formatted Markdown string. This object serves as the ground-truth
context provider for LLM agents.

## 2. User Stories
* As an Orchestrator, I want to instantiate `CodeBase` with a root path so that
  I can capture the current state of the project files.
* As a Developer Agent, I want to receive a Markdown representation that
  includes both a visual tree structure and the file contents, so that I can
  navigate the codebase and modify files accurately.
* As a System, I want to automatically exclude `.git` and ignored files, so
  that the context window is not wasted on metadata or build artifacts.

## 3. Acceptance Criteria
- [ ] Class `CodeBase` accepts `root_path` in constructor.
- [ ] `root_path` is resolved to an absolute POSIX path (FreeBSD compliant).
- [ ] The `.git` directory is unconditionally ignored.
- [ ] If `.gitignore` exists at root, its patterns are parsed and applied to
      file traversal.
- [ ] Non-text files (binary) are detected and excluded or represented as
      "[Binary File]" to prevent decoding errors.
- [ ] Method `render() -> str` returns a string starting with `# CodeBase`.
- [ ] Rendered output contains an ASCII-style directory tree visualization.
- [ ] Rendered output contains file contents inside Markdown code blocks (e.g.,
      ` ```python\n# src/main.py\n... `).
- [ ] Files listed in the tree match exactly the files rendered in code blocks.

## 4. Implementation Hints (Technical)
*   **Path Handling**: Use Python's `pathlib.Path`. Ensure compatibility with
    FreeBSD file systems.
*   **Gitignore**: Strongly suggest using the `pathspec` library (`pip install
    pathspec`) for robust gitignore pattern matching. 
*   **Binary Detection**: Use `mimetypes` or attempt to read the first 1024
    bytes as utf-8; on `UnicodeDecodeError`, treat as binary.
*   **Tree View**: Implement a recursive function to generate a string similar
    to the Unix `tree` command.
*   **Markdown Format**:
    ```markdown
    # CodeBase

    ## Structure
    .
    ├── src
    │   └── main.py
    └── requirements.txt

    ## Files
    ### src/main.py
    ```python
    print("Hello")
    ```
    ```

## 5. Execution Plan
1.  [ ] specify which pip dependencies need to be added to requirements.txt 
        including `pathspec`.
2.  [ ] **Filter Logic**: Implement `FileFilter` class to handle `.gitignore`
        parsing and `.git` exclusion.
3.  [ ] **Traversal**: Implement recursive directory walker collecting valid
        `Path` objects.
4.  [ ] **Rendering**: Implement `CodeBase.render()` (Tree generation +
        Content concatenation).
5.  [ ] **Testing**: Verify against a dummy directory with mixed binary,
        ignored, and nested text files.
