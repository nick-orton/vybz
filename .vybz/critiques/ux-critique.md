---
status: "Completed"
type: "Critique"
author: "Principal TUI Designer"
last_updated: "2026-01-15"
references: 
---

The current interaction prompt is **functional but aesthetically offensive**. It wastes screen real estate and ignores the very theming system we just architected.

Here is the critique and the required specification for immediate refactoring.

### 1. The Friction Points

*   **Horizontal Sprawl:** You are using `self.active_agent.name`.
    *   *Result:* `[Tactical Python Architect] >> ` (29 chars).
    *   *Critique:* This pushes the user's cursor nearly to the middle of the screen on a split-pane terminal. This breaks the "Flow" state. The user knows who they are talking to; they don't need the full CV in the prompt line.
    *   *Fix:* Use `self.active_agent.id` (e.g., `junior-dev`) instead. It is concise and unique.

*   **Hardcoded Styling:** You used `<style fg='cyan'>`.
    *   *Critique:* We just built a robust `themes.toml` system. Hardcoding 'cyan' here means if I switch to the `[matrix]` theme (Green), the prompt stays Cyan. That is sloppy.
    *   *Fix:* The prompt must derive its color from the active `rich` theme, or at least use `prompt_toolkit` styles that align with our palette.

*   **Invisible State:**
    *   *Critique:* I implemented a `vi` mode toggle, but the prompt gives me zero indication of which mode I am in. In a modal editor, invisible state is a critical failure.
    *   *Fix:* Use `prompt_toolkit`'s `rprompt` (Right Prompt) to display metadata like `[VI]` or `[EMACS]` and `[CTX: Loaded]`.

*   **ASCII Clutter:**
    *   *Critique:* `>>` is generic.
    *   *Fix:* Use `❯` (Unicode U+276F). It is cleaner, directional, and modern.

### 2. The Design Specification

Refactor `src/vybz/repl.py` to implement the following TUI design.

#### Visual Target
```text
junior-dev ❯ print("Hello")                                     VI | CTX
```

#### Implementation Details

**1. Dynamic Prompt Generation**
Replace the static `prompt_text` HTML with a callable that returns tokens.

```python
def get_prompt_tokens():
    # Use ID, not Name
    label = self.active_agent.id if self.active_agent else "vybz"
    return [
        ("class:agent", f"{label} "),
        ("class:separator", "❯ "),
    ]
```

**2. The Right Prompt (Metadata)**
Implement `rprompt` to offload state information.

```python
def get_rprompt_tokens():
    # Input Mode
    mode_indicator = "VI" if self.session.editing_mode == EditingMode.VI else "EMACS"
    
    # Context Indicator
    ctx_indicator = "CTX" if self.codebase else "NO-CTX"
    
    return [
        ("class:meta", f"{mode_indicator} | {ctx_indicator}"),
    ]
```

**3. Style Mapping**
Define a `prompt_toolkit.styles.Style` dictionary that maps to our semantic names.

```python
from prompt_toolkit.styles import Style

# In a perfect world, we bridge Rich -> PTK. 
# For now, define a style dict that matches our 'default' theme.
style = Style.from_dict({
    "agent": "bold cyan",       # Matches 'info'
    "separator": "bold green",  # Matches 'success'
    "meta": "dim white",        # Matches 'timestamp'
})
```

**4. Session Update**
Update the `self.session.prompt` call:

```python
user_input = self.session.prompt(
    get_prompt_tokens, 
    rprompt=get_rprompt_tokens, 
    style=style,
    multiline=True
)
```

### Action Required
Refactor `src/vybz/repl.py` to match this specification. Do not leave hardcoded HTML strings in the loop.
