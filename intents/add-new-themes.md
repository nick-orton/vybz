---
status: "Completed"
type: "Intent"
author: "Principal TUI Designer"
last_updated: "2026-01-16"
references: src/vybz/theme.py, themes.toml
---

# Add New Themes

## Context
The current `themes.toml` only provides a handful of defaults. To truly embrace "Vibe Coding," we need a diverse palette that respects different lighting conditions, aesthetic preferences, and nostalgia factors of our users.

## High-Level Intent
I want to inject 10 professionally curated color schemes into the Vybz ecosystem. These themes should range from high-contrast accessibility options to popular community standards (Nord, Gruvbox) and retro aesthetics (Amber CRT).

## Requirements
1.  **Variety:** The pack must include Dark Mode, Light Mode, Retro, and Modern styles.
2.  **Consistency:** All themes must map correctly to the semantic keys (`info`, `warning`, `header.label`, etc.).
3.  **Readability:** Ensure strictly that `content` colors contrast well against standard terminal backgrounds.

```

### designs/theme-pack-v1.md
```md
---
status: "Completed"
type: "Design"
author: "Principal TUI Designer"
last_updated: "2026-01-16"
references: intents/add-new-themes.md
---

# Theme Pack V1 Specification

## 1. High-Level Intent
Expand the visual vocabulary of the Vybz Workbench by implementing 10 new `rich` themes. These themes are designed to reduce eye strain during long coding sessions and allow users to match their CLI tools to their IDE/OS aesthetics.

## 2. Theme Roster

### The Classics
1.  **Monokai:** The high-contrast, vivid standard for coding.
2.  **Solarized:** Precision engineering palette. Low contrast, earthy.
3.  **Gruvbox:** Warm, retro, reddish-brown tones. Easy on the eyes at night.

### The Moderns
4.  **Nord:** Arctic, north-bluish, pastel. Very flat and clean.
5.  **Tokyo Night:** Deep blue/purple storm vibes. Very popular in the Neovim community.
6.  **Catppuccin:** Soft, pastel, low-saturation. "Soothing" vibe.

### The Retros
7.  **Amber:** Monochrome CRT monitor style. Fallout/Mainframe vibes.
8.  **Synthwave:** Neon pinks, purples, and electric cyans. 80s Retrowave.
9.  **DOS:** Classic VGA. Grey text, blue backgrounds (simulated via borders), heavy blockiness.

### The Minimalist
10. **Zen:** High-contrast Greyscale. No colors except for semantic state (Red/Green). Distraction-free.

## 3. Implementation Details
We will append these definitions to `themes.toml`. We use Hex codes to ensure consistency across different terminal emulators, rather than relying on the user's potentially broken ANSI color map.

```

### themes.toml
```toml
# Configuration file for Vybz REPL Themes.
# Keys correspond to rich.style.Style definitions.

# --- EXISTING ---

[default]
info = "cyan"
warning = "bold yellow"
error = "bold red"
success = "bold spring_green1"
"header.label" = "bold cyan"
"header.value" = "spring_green1"
content = "white"
"panel.border" = "blue"
"session.border" = "spring_green1"
timestamp = "dim white"

[matrix]
info = "bold green"
warning = "bold yellow"
error = "bold red"
success = "bold green"
"header.label" = "bold green"
"header.value" = "green"
content = "green"
"panel.border" = "green"
"session.border" = "bold green"
timestamp = "dim green"

[dracula]
info = "#bd93f9"             # Purple
warning = "#ffb86c"          # Orange
error = "#ff5555"            # Red
success = "#50fa7b"          # Green
"header.label" = "#ff79c6"   # Pink
"header.value" = "#8be9fd"   # Cyan
content = "#f8f8f2"          # White
"panel.border" = "#6272a4"   # Comment/Blueish
"session.border" = "#bd93f9" # Purple
timestamp = "#6272a4"        # Comment

# --- THEME PACK V1 ---

[monokai]
# The classic text editor aesthetic. High contrast, vivid colors.
info = "#66d9ef"             # Cyan
warning = "bold #fd971f"     # Orange
error = "bold #f92672"       # Pink/Red
success = "bold #a6e22e"     # Green
"header.label" = "#f92672"   # Pink
"header.value" = "#e6db74"   # Yellow
content = "#f8f8f2"          # White
"panel.border" = "#66d9ef"   # Cyan
"session.border" = "#ae81ff" # Purple
timestamp = "#75715e"        # Grey

[nord]
# An arctic, north-bluish color palette. Flat and pastel.
info = "bold #88c0d0"        # Frost Blue
warning = "bold #ebcb8b"     # Yellow
error = "bold #bf616a"       # Red
success = "bold #a3be8c"     # Green
"header.label" = "#81a1c1"   # Blue
"header.value" = "#d8dee9"   # Snow Storm
content = "#eceff4"          # White
"panel.border" = "#5e81ac"   # Dark Blue
"session.border" = "#88c0d0" # Frost Blue
timestamp = "#4c566a"        # Polar Night

[amber]
# Retro monochrome CRT monitor style.
info = "bold #ffd54f"        # Lighter Amber
warning = "bold #ff6f00"     # Dark Orange
error = "bold #d50000"       # Red (High contrast against amber)
success = "bold #ffca28"     # Amber
"header.label" = "#ffca28"   # Amber
"header.value" = "#fff8e1"   # Off-white/Yellow
content = "#ffb300"          # Standard Amber
"panel.border" = "#ff6f00"   # Dark Orange
"session.border" = "#ffca28" # Amber
timestamp = "dim #ff6f00"    # Dim Orange

[synthwave]
# 80s Retro-futurism. Neon pinks, cyans, and purples.
info = "bold #00ffff"        # Electric Cyan
warning = "bold #ffbd44"     # Sunny
error = "bold #ff5555"       # Red
success = "bold #50fa7b"     # Neon Green
"header.label" = "#ff79c6"   # Neon Pink
"header.value" = "#bd93f9"   # Purple
content = "#f8f8f2"          # White
"panel.border" = "#ff79c6"   # Pink
"session.border" = "#8be9fd" # Cyan
timestamp = "#6272a4"        # Blue Grey

[solarized]
# Precision engineering palette. Low contrast, earthy tones.
info = "bold #268bd2"        # Blue
warning = "bold #b58900"     # Yellow
error = "bold #dc322f"       # Red
success = "bold #859900"     # Green
"header.label" = "#2aa198"   # Cyan
"header.value" = "#839496"   # Base0
content = "#93a1a1"          # Base1
"panel.border" = "#586e75"   # Base01
"session.border" = "#268bd2" # Blue
timestamp = "#586e75"        # Base01

[gruvbox]
# Warm, retro groove. Reddish-browns and greens.
info = "bold #83a598"        # Blue/Grey
warning = "bold #fabd2f"     # Yellow
error = "bold #fb4934"       # Red
success = "bold #b8bb26"     # Green
"header.label" = "#fe8019"   # Orange
"header.value" = "#ebdbb2"   # Light
content = "#ebdbb2"          # Light
"panel.border" = "#d3869b"   # Purple
"session.border" = "#fabd2f" # Yellow
timestamp = "#928374"        # Grey

[tokyonight]
# A clean, dark theme that celebrates the lights of downtown Tokyo.
info = "bold #7aa2f7"        # Blue
warning = "bold #e0af68"     # Orange
error = "bold #f7768e"       # Red
success = "bold #9ece6a"     # Green
"header.label" = "#bb9af7"   # Purple
"header.value" = "#c0caf5"   # Storm White
content = "#a9b1d6"          # Storm Grey
"panel.border" = "#7aa2f7"   # Blue
"session.border" = "#bb9af7" # Purple
timestamp = "#565f89"        # Dark Grey

[catppuccin]
# Soothing pastel theme (Mocha variant).
info = "bold #89b4fa"        # Blue
warning = "bold #f9e2af"     # Yellow
error = "bold #f38ba8"       # Red
success = "bold #a6e3a1"     # Green
"header.label" = "#cba6f7"   # Mauve
"header.value" = "#cdd6f4"   # Text
content = "#bac2de"          # Subtext
"panel.border" = "#89b4fa"   # Blue
"session.border" = "#f5c2e7" # Pink
timestamp = "#6c7086"        # Overlay

[dos]
# Classic VGA / Command Prompt. Utilitarian.
info = "bold white on blue"
warning = "black on yellow"
error = "white on red"
success = "black on green"
"header.label" = "white"
"header.value" = "bold white"
content = "white"
"panel.border" = "white"
"session.border" = "white"
timestamp = "dim white"

[zen]
# Distraction free. Greyscale with minimal semantic color.
info = "bold white"
warning = "bold underline white"
error = "bold white on red"
success = "bold white"
"header.label" = "dim white"
"header.value" = "white"
content = "white"
"panel.border" = "dim white"
"session.border" = "white"
timestamp = "dim white"
