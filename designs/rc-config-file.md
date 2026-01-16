---
status: "Draft"
type: "Design"
last_updated: "2026-01-15"
references: intents/rc-config-file.md
---

# User Configuration Persistence Specification

## 1. High-Level Intent
Implement a robust configuration loading system that persists user preferences
(Theme, Input Mode, Model) across sessions. This system introduces dotfile
support to populate default values for the CLI. This ensures that users can
define their "Flow" environment once, while maintaining the flexibility to
override specific settings via command-line flags for one-off tasks.

## 2. User Stories
* As a User, I want to create a file at `$HOME/.vybzrc` defining `mode = "vi"`
  so that I default to Vi keybindings without typing the flag every time.
* As a User, I want the system to check multiple locations (Home dir, then XDG
  Config) so I can organize my dotfiles according to my OS standards.
* As a User, I want Command Line Arguments to strictly override the config file
  (e.g., `vybz --theme matrix` overrides `theme="dracula"` in config).
* As a User, I want to define `model` and `log_file` paths in the config to
  avoid repetitive typing.

## 3. Acceptance Criteria
- [ ] **Discovery Logic:** The system checks for configuration files in the
      following order (first found wins):
      1. `$HOME/.vybzrc`
      2. `$XDG_CONFIG_HOME/vybz.config` (defaulting XDG to `$HOME/.config` if
         unset).
- [ ] **File Format:** The file is parsed as TOML, despite the `.vybzrc` or
      `.config` extension.
- [ ] **Schema Support:** The loader accepts the following keys:
      `theme`, `mode`, `model`, `log_file`, `agent`, `codebase`.
- [ ] **Precedence Hierarchy:**
      1. **CLI Arguments** (Highest Priority)
      2. **User Configuration File**
      3. **System Hardcoded Defaults** (Lowest Priority)
- [ ] **Integration:** `src/vybz/tools/work.py` utilizes `argparse`'s
      `set_defaults()` method to inject the loaded config, ensuring proper
      override behavior.
- [ ] **Resilience:** Malformed TOML files trigger a styled Warning but do not
      crash the application (Fail Open to defaults).

## 4. Implementation Hints (Technical)
*   **Module:** Create `src/vybz/config.py`.
*   **Path Resolution:**
    ```python
    def get_config_paths() -> List[Path]:
        home = Path.home()
        xdg_root = os.getenv("XDG_CONFIG_HOME", home / ".config")
        return [
            home / ".vybzrc",
            Path(xdg_root) / "vybz.config"
        ]
    ```
*   **Argparse Strategy:**
    Do not manually merge dictionaries. Use `argparse` features:
    ```python
    # 1. Load User Config
    user_defaults = config.load()
    
    # 2. Update Parser Defaults (Config overrides System, CLI overrides Config)
    parser.set_defaults(**user_defaults)
    
    # 3. Parse (CLI args will naturally override defaults)
    args = parser.parse_args()
    ```
*   **Schema Validation:** Since `argparse` expects specific attribute names,
    ensure the TOML keys match the `dest` of `add_argument`.
    *   TOML `log_file` -> matches `parser.add_argument("--log-file")` auto-
        conversion to `log_file`.

## 5. Execution Plan
1.  [ ] **Create Module:** Implement `src/vybz/config.py` containing the
        discovery loop and `tomllib` parsing logic.
2.  [ ] **Refactor CLI:** Update `src/vybz/tools/work.py` to import `config`
        and call `parser.set_defaults()` before `parser.parse_args()`.
3.  [ ] **Add Warning:** Implement `ui.print_warning` call in the config loader
        if TOML parsing fails.
4.  [ ] **Verify:** Create `~/.vybzrc`, run `vybz --help` and verify the
        Defaults listed in the help text match the file.
