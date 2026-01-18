---
status: "Completed"
type: "Critique"
author: ["Senior Python Architect", "Lead Technical Writer"]
last_updated: "2026-01-18"
references: src/vybz/artifact.py
---

# Critique: Artifact Parser Structural Refactor

## 1. Executive Summary
The current `ArtifactProcessor` implementation in `src/vybz/artifact.py` has
evolved into a monolithic "God Method" (`parse`) that suffers from high
cyclomatic complexity and rigid coupling. It utilizes a "First Match Wins" logic
that actively discards secondary artifacts—such as a Diff following a Design
Doc—leading to data loss and user frustration.

To support the evolving capabilities of Vybz agents—specifically the ability to
generate multiple related files in a single turn—we must refactor this into a
**Polymorphic Handler Chain**. This approach applies the **Strategy Pattern** to
delegate recognition, parsing, and routing to specialized domain objects,
treating the LLM response as a stream of potential artifacts rather than a
single block of text.

## 2. Architectural Analysis

### 2.1. The "Single-Winner" Anti-Pattern
The current `parse` method iterates through tokens and returns immediately upon
finding a high-priority block (like a Design Doc).
*   **The Defect:** If an Agent outputs a Design Doc *and* a prototype Diff, the
    Diff is ignored.
*   **The Defect:** If an Agent outputs two Diffs (for two different files), only
    the first one is captured.
*   **The Fix:** The parser must treat the LLM response as a *stream*, returning
    a `List[Artifact]` rather than a single object.

### 2.2. Violation of Single Responsibility Principle (SRP)
The `parse` method currently handles:
1.  Markdown Tokenization.
2.  YAML Extraction & Parsing.
3.  Diff Heuristics & Sanitization.
4.  Filename Generation.
5.  Directory Routing (via a hardcoded `DIR_MAP`).

Adding a new artifact type (e.g., "SQL Migration" or "Mermaid Diagram") requires
invasive changes to this central method, violating the **Open/Closed Principle**.

### 2.3. Hardcoded Routing Logic
The directory mapping (`if type == 'Design': dir = 'designs'`) is hardcoded
within the processor. This couples the parsing logic to the filesystem structure.
Moving this logic into specific handler classes makes the system extensible.

## 3. Proposed Architecture: The Handler Chain

We will refactor the system to use a **Chain of Responsibility** or **Strategy
Pattern**.

### 3.1. The `ArtifactHandler` Interface
We define an abstract base class that encapsulates the lifecycle of a specific
artifact type.

```python
from abc import ABC, abstractmethod
from markdown_it.token import Token

class ArtifactHandler(ABC):
    @abstractmethod
    def can_handle(self, token: Token) -> bool:
        """
        Boolean predicate: Does this Markdown token belong to this handler?
        e.g., Is it a fence block with 'type: Design' YAML?
        """
        pass

    @abstractmethod
    def extract(self, token: Token, full_text: str) -> Artifact:
        """
        Parses the token content, sanitizes it (e.g., Diff repair),
        generates a filename, and returns the domain object.
        """
        pass
```

### 3.2. Concrete Strategies
We will extract logic from the current `parse` method into three distinct
classes:

1.  **`DocumentHandler`**:
    *   **Logic:** Recognizes `---` YAML frontmatter.
    *   **Routing:** Maps `type: Design` -> `designs/`, `type: Bug` ->
        `intents/`.
    *   **Parsing:** Extracts H1 headers for filenames.

2.  **`DiffHandler`**:
    *   **Logic:** Recognizes `diff` or `patch` tags.
    *   **Routing:** Defaults to `output/`.
    *   **Parsing:** Calls `DiffSanitizer` and extracts filenames from `+++ b/`
        headers.

3.  **`CodeFileHandler` (New Capability)**:
    *   **Logic:** Recognizes generic code blocks (e.g., `python`) containing a
        path comment (e.g., `# filename: src/main.py`).
    *   **Routing:** Uses the directory structure from the extracted path.
    *   **Parsing:** Returns raw content.

## 4. The Pipeline Processor

The `ArtifactProcessor` becomes an orchestrator rather than a parser.

### 4.1. Generator-Based Logic
*   **Signature:** `parse(text: str) -> List[Artifact]`
*   **Logic:**
    1.  Initialize `artifacts = []`.
    2.  Iterate through *all* tokens.
    3.  For each token, check registered handlers (`can_handle`).
    4.  If a match is found, `extract` the artifact and append to list.
    5.  **Do not break** the loop; continue scanning for more artifacts.

### 4.2. Filename Collision Management
When parsing multiple artifacts, we must ensure unique filenames. The Processor
should maintain a registry of filenames generated *during the current parse
session*. If `main.py` is extracted twice, the second one becomes `main_1.py`
automatically.

## 5. Implementation Strategy

1.  **Refactor `parse`:** Deprecate the greedy `if/elif` logic. Implement the
    handler loop.
2.  **Update `ReplSession` (The Consumer):**
    *   The `/save` command currently expects a single object.
    *   **New UX:** Loop through the returned list. Save each artifact. Print a
        summary: "Saved 3 artifacts: [design.md, script.py, test.py]".
3.  **Refactor Tests:** Update `tests/vybz/test_artifact.py` to assert against
    lists and verify multi-artifact extraction.

## 6. Benefits
*   **Multi-File Support:** Agents can generate a full feature (Implementation +
    Test + Docs) in one turn, and `/save` persists all of it.
*   **Testability:** Each handler (`_extract_diff`, etc.) can be unit tested in
    isolation.
*   **Extensibility:** Adding support for new types becomes as simple as adding
    a new handler class.
