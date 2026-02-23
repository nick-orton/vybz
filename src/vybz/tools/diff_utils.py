"""
diff_utils.py

Stateless utility for sanitizing and repairing Unified Diff strings generated
by LLMs. Handles common hallucinations like missing context spaces and
incorrect hunk header arithmetic.
"""

import re
from typing import List, Tuple, Optional
from vybz.client import ui

class DiffSanitizer:
    """
    Provides methods to repair malformed Unified Diffs.
    """

    @classmethod
    def sanitize(cls, raw_diff: str) -> str:
        """
        Attempts to repair a raw diff string.

        Pipeline:
        1. Heuristic repair of missing context spaces.
        2. Manual recalculation of hunk headers (counting lines).
        3. Failsafe: Returns original text if catastrophic failure occurs.

        Args:
            raw_diff: The raw string output from the LLM.

        Returns:
            The sanitized diff string.
        """
        try:
            return cls._repair_and_recalculate(raw_diff)
        except Exception as e:
            ui.print_warning(f"Diff sanitization failed: {e}. Saving raw output.")
            return raw_diff

    @staticmethod
    def _repair_and_recalculate(text: str) -> str:
        """
        Parses the diff line-by-line to:
        1. Inject missing spaces for context lines.
        2. Count actual lines in each hunk.
        3. Rewrite hunk headers with correct counts.
        """
        lines = text.splitlines()
        output_lines: List[str] = []

        # State tracking
        in_hunk = False
        current_hunk_lines: List[str] = []
        hunk_start_old = 0
        hunk_start_new = 0
        hunk_suffix = ""

        # Regex to parse headers: @@ -1,5 +1,5 @@ optional suffix
        header_pattern = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)")

        def flush_hunk():
            """Analyzes the buffered hunk lines and appends the corrected hunk to output."""
            nonlocal current_hunk_lines, output_lines
            if not current_hunk_lines:
                return

            # Count lines for the header
            old_count = 0
            new_count = 0

            for line in current_hunk_lines:
                # Ignore '\ No newline...' markers for counting
                if line.startswith("\\"):
                    continue

                # Context line: exists in both
                if line.startswith(" "):
                    old_count += 1
                    new_count += 1
                # Removal: exists in old only
                elif line.startswith("-"):
                    old_count += 1
                # Addition: exists in new only
                elif line.startswith("+"):
                    new_count += 1
                # Fallback: treat unknown/empty as context if inside hunk (should be handled by repair logic)
                else:
                    old_count += 1
                    new_count += 1

            # Construct new header
            new_header = f"@@ -{hunk_start_old},{old_count} +{hunk_start_new},{new_count} @@{hunk_suffix}"
            output_lines.append(new_header)
            output_lines.extend(current_hunk_lines)
            current_hunk_lines = []

        for line in lines:
            # 1. Detect Header
            match = header_pattern.match(line)
            if match:
                if in_hunk:
                    flush_hunk()

                in_hunk = True
                # Parse start lines (groups 1 and 3). Groups 2 and 4 are lengths (ignored).
                hunk_start_old = int(match.group(1))
                hunk_start_new = int(match.group(3))
                hunk_suffix = match.group(5)
                continue

            # 2. Handle File Headers or Preamble
            if not in_hunk:
                output_lines.append(line)
                continue

            # 3. Inside Hunk: Space Repair
            repaired_line = line
            if not line:
                # Empty line in hunk -> usually context
                # Standard diffs use " ", but "empty" is often accepted.
                # To be safe for counting, we can treat it as context.
                pass
            else:
                first_char = line[0]
                if first_char in ('+', '-', '\\', ' '):
                    pass
                else:
                    # Heuristic: Missing space
                    # Check for double-space indentation hallucination
                    if line.startswith("  "):
                        repaired_line = " " + line
                    else:
                        repaired_line = " " + line

            current_hunk_lines.append(repaired_line)

        # Flush the final hunk
        if in_hunk:
            flush_hunk()

        # Combine
        result = "\n".join(output_lines)

        # Ensure final newline (POSIX) if content exists
        if result and not result.endswith("\n"):
            result += "\n"

        return result
