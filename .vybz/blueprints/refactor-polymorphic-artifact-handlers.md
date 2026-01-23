---
status: "Completed"
type: "Blueprint"
author: "Senior Python Architect"
last_updated: "2026-01-18"
references: critiques/critique-artifact-parser-structural-refactor.md, src/vybz/artifact.py
---

# Refactor: Polymorphic Artifact Handlers

This blueprint details the architectural transformation of the `ArtifactProcessor` from a monolithic conditional block into a **Chain of Responsibility** using the Strategy Pattern.

## 1. Goal
To enable the extraction of **multiple artifacts** from a single LLM response (e.g., a Design Doc + a Diff + a Unit Test) and to decouple directory routing logic from text parsing logic.

## 2. Architecture Specification: `src/vybz/artifact.py`

### 2.1. Abstract Base Class: `ArtifactHandler`
We will introduce an ABC to define the contract for all artifact strategies.

```python
class ArtifactHandler(ABC):
    @abstractmethod
    def can_handle(self, token: Token) -> bool:
        """Returns True if this handler recognizes the token."""
        pass

    @abstractmethod
    def extract(self, token: Token, full_text: str) -> Artifact:
        """Process token and return Artifact domain object."""
        pass
```

### 2.2. Concrete Strategies
We will extract logic from the current `parse` method into three distinct classes:

1.  **`DocumentHandler`**:
    *   **Logic:** Recognizes `---` YAML frontmatter.
    *   **Routing:** Maps `type: Design` -> `designs/`, `type: Bug` -> `intents/`, etc.
    *   **Parsing:** Extracts H1 headers for filenames.

2.  **`DiffHandler`**:
    *   **Logic:** Recognizes `diff` or `patch` tags.
    *   **Routing:** Defaults to `output/`.
    *   **Parsing:** Calls `DiffSanitizer` and extracts filename from `+++ b/`.

3.  **`CodeFileHandler` (New)**:
    *   **Logic:** Recognizes generic code blocks (e.g., `python`) containing a path comment (e.g., `# filename: src/main.py`).
    *   **Routing:** Uses the directory structure from the extracted path.
    *   **Parsing:** Returns raw content, stripping the filename comment if necessary.

### 2.3. Updated Processor: `ArtifactProcessor`
The processor becomes an orchestrator.

*   **Attribute:** `self.handlers: List[ArtifactHandler]`
*   **Method:** `parse(text: str) -> List[Artifact]`
    *   **Change:** Returns a **List** instead of a single object.
    *   **Logic:** Iterates *all* tokens. If a handler says `can_handle`, it extracts the artifact and appends it to the list. It does *not* stop at the first match.

## 3. Consumer Updates: `src/vybz/commands/core.py`

### 3.1. Class `SaveCommand`
The `execute` method must be updated to handle the list return type.

*   **Logic:**
    ```python
    artifacts = processor.parse(session.last_response)
    if not artifacts:
        # Handle fallback or error
        return

    results = []
    for artifact in artifacts:
        msg = processor.save(artifact, root)
        results.append(msg)
        
    # Print summary (e.g., "Saved 3 artifacts: ...")
    ```

## 4. Execution Steps

1.  **Refactor `artifact.py` (Phase 1):** Define `ArtifactHandler` ABC and implement `DocumentHandler` by moving existing YAML logic.
2.  **Refactor `artifact.py` (Phase 2):** Implement `DiffHandler` by moving existing Diff logic.
3.  **Refactor `artifact.py` (Phase 3):** Implement `CodeFileHandler` (New Logic).
4.  **Update Processor:** Rewrite `ArtifactProcessor.parse` to use the handler loop and return `List[Artifact]`.
5.  **Update Command:** Modify `SaveCommand` in `src/vybz/commands/core.py` to iterate the list.
6.  **Update Tests:** Rewrite `tests/vybz/test_artifact.py` to assert against Lists. Add a test case with a Multi-Artifact response.

## 5. Verification Strategy

### 5.1. Unit Test: Multi-Artifact Extraction
*   **Input:** A string containing a Design Doc (YAML) AND a Python code block with `# filename: test.py`.
*   **Expectation:** `parse()` returns a list of length 2.
    *   Item 1: Type="Design", Dir="designs"
    *   Item 2: Type="Code", Dir="." (or derived path)

### 5.2. Manual Test
1.  **Agent:** `vybz junior-dev`
2.  **Prompt:** "Create a python script `hello.py` that prints hello, and a test file `test_hello.py` that tests it."
3.  **Action:** `/save`
4.  **Result:** System reports saving **two** distinct files.

