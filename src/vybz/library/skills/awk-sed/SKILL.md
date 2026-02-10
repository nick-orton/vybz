---
name: awk-sed
description: 'Advanced manipulation of text streams using the classic Unix power tools:
  awk and sed.'
---

# Text Processing (Awk & Sed)
_Advanced manipulation of text streams using the classic Unix power tools: awk and sed._

## Knowledge
* #### The Power of Awk (Data Extraction)
      *   **Philosophy:** Awk is a data-driven scripting language. It operates on records (lines) and fields (columns).
      *   **Structure:** `pattern { action }`. If pattern is true, perform action.
      *   **Variables:** `$0` (Whole line), `$1` (First field), `NR` (Line number), `NF` (Field count), `FS` (Input separator), `OFS` (Output separator).
      *   **Efficiency:** Prefer `awk '/pattern/ { print $2 }'` over `grep 'pattern' | cut -f2`. It saves a process fork.
* #### The Power of Sed (Stream Editing)
      *   **Philosophy:** Sed is a stream editor for filtering and transforming text.
      *   **Syntax:** `s/regexp/replacement/flags`.
      *   **Delimiters:** You are not forced to use `/`. If your pattern contains slashes (like paths), use `s|/path/to|/new/path|` to avoid "leaning toothpick syndrome".
      *   **Addressing:** Apply commands only to specific lines: `sed '1,5d'` (delete lines 1-5) or `sed '/^#/d'` (delete comments).
* #### Portability Traps (BSD vs GNU)
      *   **In-Place Editing (`-i`):**
          *   **GNU (Linux):** `sed -i 's/foo/bar/' file` (No extension needed).
          *   **BSD (FreeBSD/macOS):** `sed -i '' 's/foo/bar/' file` (Empty string argument MANDATORY).
          *   **Safe Portable:** Use `sed -i.bak ...` to create a backup, which works on both.
      *   **Regex:** Standard `sed` uses BRE (Basic Regex). Use `sed -E` to enable Extended Regex (capturing groups `()`, `+`, `?`).

## Abilities
* Constructing robust one-liners that eliminate the need for heavier Python/Perl scripts for simple text tasks.
* Refactoring inefficient pipelines (e.g., `cat file | grep | awk`) into single-process invocations.
* Using `awk` `BEGIN` and `END` blocks to perform summation, averaging, or header/footer generation.
* Writing `sed` commands that safely handle delimiters inside the search string.
* Detecting when a text processing task is too complex for sed/awk (e.g., parsing nested JSON/XML) and recommending Python instead.
