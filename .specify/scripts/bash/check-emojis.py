#!/usr/bin/env python3
"""Check git diff for unicode emoji characters."""

import re
import subprocess
import sys


def main() -> int:
    """Scan git diff for emojis and return non-zero if found."""
    args = sys.argv[1:]
    cmd = ["git", "diff", *args]
    diff = subprocess.check_output(cmd, text=True)  # noqa: S603
    emoji_pattern = re.compile(r"[\U00010000-\U0010ffff\u2600-\u26ff\u2700-\u27bf]")
    matches = emoji_pattern.findall(diff)
    if matches:
        sys.stderr.write(f"Found emojis: {set(matches)}\n")
        return 1
    sys.stdout.write("Zero emojis found in diff!\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
