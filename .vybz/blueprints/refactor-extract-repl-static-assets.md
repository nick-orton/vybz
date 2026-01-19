---
status: "Completed"
type: "Blueprint"
author: "Senior Python Architect"
last_updated: "2026-01-17"
references: src/vybz/repl.py
---

# Refactor: Extract REPL Static Assets

This blueprint details the extraction of hardcoded string literals (specifically the Help Menu) from `src/vybz/repl.py` into dedicated static asset files.

## 1. Goal
To decouple presentation content from application logic by moving static text into `src/vybz/assets/`. This improves code readability and allows for easier content updates.

## 2. File Structure Changes

### 2.1 New Directory: `src/vybz/assets/`
We will create a package to hold static text files.
*   `src/vybz/assets/__init__.py` (Empty, marks as package)
*   `src/vybz/assets/repl_help.txt` (The help content)

## 3. Module Specification: `src/vybz/repl.py`

### 3.1 Class `ReplSession` Updates

#### New Method: `_load_asset(self, filename: str) -> str`
*   **Purpose:** Robustly loads text content from the assets directory.
*   **Logic:**
    1.  Resolve path: `Path(__file__).parent / "assets" / filename`.
    2.  Check existence.
    3.  Read text (UTF-8).
    4.  Return content or a fallback error string if missing.

#### Update: `_handle_command` (/help case)
*   **Current:** Series of `ui.print_system("...")` calls.
*   **New:**
    1.  Call `content = self._load_asset("repl_help.txt")`.
    2.  Pass content to `ui.print_panel(content)` (New UI method) 

## 4. Module Specification: `src/vybz/ui.py`

### 4.1 New Method: `print_panel(content: str, title: str = "")`
*   **Purpose:** Renders a generic block of text inside a styled Rich Panel.
*   **Style:** Use `box.ROUNDED`, border style `blue` (or theme compliant).

## 5. Execution Steps

1.  **Create Assets:**
    *   `mkdir -p src/vybz/assets`
    *   Create `src/vybz/assets/repl_help.txt` with the content currently in `repl.py`.
2.  **Update UI:** Add `print_panel` to `src/vybz/ui.py`.
3.  **Refactor REPL:** Implement `_load_asset` and update the `/help` command logic.
4.  **Verify:** Run `vybz junior-dev` and type `/help`.

## 6. Verification Script

```python
if __name__ == "__main__":
    from pathlib import Path
    
    # Simulate the path resolution logic
    # Assuming this script runs from project root
    base_path = Path("src/vybz/repl.py").parent
    asset_path = base_path / "assets" / "repl_help.txt"
    
    print(f"Resolving asset at: {asset_path.resolve()}")
    
    if asset_path.exists():
        print("[OK] Asset file found.")
        print("-" * 20)
        print(asset_path.read_text())
    else:
        print("[FAIL] Asset file missing (Run execution steps first).")
```
```

### Senior Dev Peer Review

*   **Critique:** The plan introduces a dependency on the file system structure relative to `repl.py`. This is standard for Python packages (`package_data`), but we must ensure `setuptools` (in `pyproject.toml`) knows to include `*.txt` files in the build, otherwise, the installed version of `vybz` will crash when looking for assets.
*   **Addendum:** I will add a note to check `pyproject.toml` `[tool.setuptools.package-data]` to include `vybz.assets = ["*.txt"]`.

### Verification Script

This script verifies the path resolution logic before we write the code.

```python
if __name__ == "__main__":
    from pathlib import Path
    import sys

    # Mocking the location of repl.py
    # In a real run, __file__ would be inside src/vybz/
    # We simulate looking for assets relative to src/vybz
    
    project_root = Path.cwd()
    src_vybz = project_root / "src" / "vybz"
    assets_dir = src_vybz / "assets"
    
    print(f"Target Assets Dir: {assets_dir}")
    
    # Check if we need to create it for the test
    if not assets_dir.exists():
        print("Note: Directory does not exist yet (Expected before implementation).")
        print(f"Plan: Create {assets_dir}")
        print(f"Plan: Create {assets_dir / 'repl_help.txt'}")
    else:
        print("Directory exists.")
