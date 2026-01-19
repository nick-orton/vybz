---
status: "Draft"
type: "Bug"
author: "Principal QA Engineer"
last_updated: "2026-01-19"
references: src/vybz/theme.py, pyproject.toml
---

# Configuration Drift: `themes.toml` Not Packaged or Resolvable

## 1. Symptom
When `vybz` is installed (e.g., via `pip install .`) and executed from a directory other than the source root, attempting to load any theme other than "default" (e.g., `vybz --theme matrix`) results in a crash or error message indicating the theme is not found.

**Error:**
```text
ValueError: Theme 'matrix' not found. Available: default
```

## 2. Root Cause Analysis
This is a **Packaging & Pathing Error**.

1.  **Pathing Logic:** In `src/vybz/theme.py`, the `ThemeLoader._get_config_path` method uses `Path.cwd() / "themes.toml"`.
    *   *Defect:* This looks for the configuration file in the user's *current working directory*. While this works during development (when running from the project root), it fails for an end-user running the tool globally, as `themes.toml` does not exist in their random working directories.
2.  **Packaging:** The `themes.toml` file resides in the project root.
    *   *Defect:* `pyproject.toml` only configures `[tool.setuptools.package-data]` for files inside the `vybz` package (`agents/*.toml`, `assets/*.txt`). Consequently, `themes.toml` is **excluded** from the build distribution (`wheel`/`sdist`).

## 3. Impact
*   Users cannot use the "Matrix", "Dracula", or "Monokai" themes documented in the release, as these definitions live exclusively in the missing TOML file.
*   The application looks broken immediately upon installation if the user tries to customize it.

## 4. Proposed Fix
We need to treat `themes.toml` as a shipped package asset, similar to `assets/repl_help.txt`.

1.  **Move the File:** Move `themes.toml` from the project root to `src/vybz/themes.toml`.
2.  **Update Packaging:** Modify `pyproject.toml` to include `themes.toml` in `tool.setuptools.package-data`.
3.  **Update Loader Logic:** Modify `src/vybz/theme.py` to resolve the path relative to the module location (`__file__`), not the CWD.

**Code Change (`src/vybz/theme.py`):**
```python
    @staticmethod
    def _get_config_path() -> Path:
        """Returns the path of the packaged themes configuration file."""
        # Fix: Resolve relative to the installed package, not CWD
        return Path(__file__).parent / "themes.toml"
```
