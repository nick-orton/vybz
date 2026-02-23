"""
md_utils.py

Core text processing logic for Markdown formatting.
Ensures hard wrapping while preserving list structures and code blocks.
"""

import re
import textwrap
from typing import Final, List

# Heuristic for detecting the start of a list or blockquote
LIST_PATTERN: Final[re.Pattern] = re.compile(r'^(\s*(?:\d+\.|[*+->])\s+)(.*)')


def format_markdown_content(content: str, width: int) -> str:
    """
    Reflows Markdown text to a specific width, preserving structural elements.

    Args:
        content: The raw markdown string.
        width: The maximum line length.

    Returns:
        The formatted markdown string.
    """
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
