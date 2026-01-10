#!/usr/bin/env python3
"""
Markdown Formatter (CLI Utility)

Formats a markdown file to ensure that lines are no longer than 80 characters
"""

import argparse
import re
import sys
import textwrap
from pathlib import Path
from typing import Final, List, Optional

# Configuration
DEFAULT_WIDTH: Final[int] = 80
# Heuristic for detecting the start of a list or blockquote
LIST_PATTERN: Final[re.Pattern] = re.compile(r'^(\s*(?:\d+\.|[*+->])\s+)(.*)')

def format_markdown_content(content: str, width: int) -> str:
    lines = content.splitlines()
    output: List[str] = []
    text_buffer: List[str] = []
    current_indent_prefix: str = ""

    def flush_buffer():
        if text_buffer:
            paragraph = " ".join(text_buffer)
            # If we started with a list marker, we want subsequent lines
            # to indent to match the space after the marker.
            sub_indent = " " * len(current_indent_prefix)

            wrapped = textwrap.fill(
                paragraph,
                width=width,
                initial_indent=current_indent_prefix,
                subsequent_indent=sub_indent,
                break_long_words=False
            )
            output.append(wrapped)
            text_buffer.clear()

    for line in lines:
        stripped = line.strip()

        # 1. Handle Empty Lines
        if not stripped:
            flush_buffer()
            current_indent_prefix = ""
            output.append("")
            continue

        # 2. Handle Headers or Code Blocks (Strictly Protected)
        if stripped.startswith(('#', '```')):
            flush_buffer()
            current_indent_prefix = ""
            output.append(line)
            continue

        # 3. Detect List Markers (1., *, -, etc.)
        match = LIST_PATTERN.match(line)
        if match:
            flush_buffer()
            # Capture the prefix (e.g., "1. ") and the content
            current_indent_prefix = match.group(1)
            text_buffer.append(match.group(2))
        else:
            # 4. Standard paragraph text or continuation of a list item
            text_buffer.append(stripped)

    flush_buffer()
    return "\n".join(output)

def main() -> None:
    parser = argparse.ArgumentParser(description="Reformat Markdown including lists.")
    parser.add_argument("file", type=Path, help="Path to the Markdown file.")
    parser.add_argument("-w", "--width", type=int, default=DEFAULT_WIDTH, help="Max width.")

    args = parser.parse_args()

    if not args.file.is_file():
        print(f"Error: '{args.file}' not found.", file=sys.stderr)
        sys.exit(1)

    try:
        raw_content = args.file.read_text(encoding="utf-8-sig")
        formatted_output = format_markdown_content(raw_content, args.width)
        sys.stdout.write(formatted_output + '\n')
    except Exception as e:
        print(f"Runtime Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
