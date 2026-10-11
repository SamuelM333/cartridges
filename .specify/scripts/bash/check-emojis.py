#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright 2026 samuelm333

"""Check changes for unicode emoji characters.

Usage:
    check-emojis.py            Unstaged changes and untracked files.
    check-emojis.py --cached   Staged changes (any arguments go to `git diff`).

Only added lines are checked, so removing an emoji never fails the check.
"""

import re
import subprocess
import sys
from pathlib import Path

_EMOJI = re.compile("[\U00010000-\U0010ffff\u2600-\u26ff\u2700-\u27bf]")


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True)  # noqa: S603, S607


def _added_lines(diff: str) -> dict[str, list[str]]:
    """Group the added lines of a diff by file."""
    added: dict[str, list[str]] = {}
    current = ""
    for line in diff.splitlines():
        if line.startswith("+++ "):
            current = line.removeprefix("+++ b/").removeprefix("+++ ")
        elif line.startswith("+"):
            added.setdefault(current, []).append(line[1:])
    return added


def _untracked_lines() -> dict[str, list[str]]:
    """Read the untracked files that are not ignored."""
    names = _git("ls-files", "--others", "--exclude-standard", "-z").split("\0")
    lines: dict[str, list[str]] = {}
    for name in filter(None, names):
        try:
            lines[name] = Path(name).read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            continue  # Not a text file.
    return lines


def main() -> int:
    """Scan changes for emojis and return non-zero if any are found."""
    args = sys.argv[1:]
    files = _added_lines(_git("diff", *args))
    if not args:
        files.update(_untracked_lines())

    found = {
        name: sorted({char for line in lines for char in _EMOJI.findall(line)})
        for name, lines in files.items()
    }
    found = {name: chars for name, chars in found.items() if chars}
    if found:
        for name, chars in found.items():
            sys.stderr.write(f"Found emojis in {name}: {chars}\n")
        return 1

    sys.stdout.write("Zero emojis found in changes!\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
