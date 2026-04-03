---
name: modern-python-standards
description: "Writes and refactors Python 3.11+ code with modern type hints, dataclasses, pathlib, and guard clauses. Use when writing new Python code, reviewing Python for style or type issues, refactoring legacy Python, or when the user asks for Pythonic, type-safe, or clean Python. Triggers: Python code, type hints, typing, dataclass, pathlib, code style, best practices, PEP 8, mypy, modern Python, refactor python, modernize"
---

# Modern Python Standards

## Workflow

1. **Assess**: Identify legacy patterns (old typing imports, os.path, raw dicts, nested logic)
2. **Apply**: Rewrite using the rules and examples below
3. **Validate**: Run through the checklist at the end before finishing

## Modern Syntax Rules (Python 3.11+)

| Area | DO | DON'T |
|------|-----|-------|
| Type hints | `list[str]`, `str \| None` | `List[str]`, `Union[str, None]` from `typing` |
| Paths | `pathlib.Path` | `os.path.join()`, string concatenation |
| Data objects | `@dataclass` | Raw dicts for structured data |
| Strings | f-strings | `.format()`, `%` formatting |
| Docstrings | Google-style (PEP 257) | Undocumented public APIs |

## Concrete Examples

### Type hints (3.11+ builtins, not typing module)

```python
# DON'T
from typing import List, Dict, Optional, Union
def process(items: List[str], config: Optional[Dict[str, Any]] = None) -> Union[str, None]:
    ...

# DO
def process(items: list[str], config: dict[str, Any] | None = None) -> str | None:
    ...
```

### Guard clauses (flatten nested logic)

```python
# DON'T
def validate(user):
    if user is not None:
        if user.is_active:
            if user.has_permission:
                return do_work(user)
    return None

# DO
def validate(user: User) -> Result | None:
    if user is None:
        return None
    if not user.is_active:
        return None
    if not user.has_permission:
        return None
    return do_work(user)
```

### Dataclass with type hints (not raw dicts)

```python
# DON'T
config = {"host": "localhost", "port": 8080, "debug": True}

# DO
@dataclass
class Config:
    host: str
    port: int
    debug: bool = False
```

### pathlib.Path (not os.path)

```python
# DON'T
import os
full = os.path.join(base_dir, "data", "output.csv")
if os.path.exists(full):
    with open(full) as f: ...

# DO
from pathlib import Path
full = Path(base_dir) / "data" / "output.csv"
if full.exists():
    content = full.read_text()
```

### Google-style docstring template

```python
def fetch_records(query: str, limit: int = 100) -> list[Record]:
    """Fetch records matching the query.

    Args:
        query: SQL-compatible filter expression.
        limit: Maximum records to return.

    Returns:
        Matching records sorted by creation date.

    Raises:
        ConnectionError: If the database is unreachable.
    """
```

## Refactoring Patterns

- Use context managers (`with`) for all resource handling (files, locks, connections)
- Variable names explain "what"; comments explain "why"
- Prefer `match/case` over long `if/elif` chains for 3.10+ pattern matching

## Validation Checklist

Before finishing any Python file:
1. All function signatures have full type annotations (params + return)
2. No `typing.List`, `typing.Dict`, or `typing.Union` imports remain
3. All file paths use `pathlib.Path`
4. All public functions/classes have Google-style docstrings
5. No nested `if/else` deeper than 2 levels (use guard clauses)
