#!/usr/bin/env python3
"""
Markdown Formatter (CLI Utility)

Formats a markdown file to ensure that lines are no longer than 80 characters
"""

import argparse
import sys
from pathlib import Path
from typing import Final
from vybz.tools.md_utils import format_markdown_content

# Configuration
DEFAULT_WIDTH: Final[int] = 80

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
