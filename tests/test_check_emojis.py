# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright 2026 samuelm333

"""Test that the emoji check sees untracked, unstaged, and staged changes."""

import subprocess
import sys
import tempfile
from pathlib import Path

_SCRIPT = (
    Path(__file__).resolve().parents[1] / ".specify" / "scripts" / "bash"
) / "check-emojis.py"
_EMOJI = "\U0001f600"


def _git(repo: Path, *args: str) -> None:
    subprocess.run(  # noqa: S603
        [  # noqa: S607
            "git",
            "-c",
            "user.name=test",
            "-c",
            "user.email=test@example.com",
            "-c",
            "commit.gpgsign=false",
            *args,
        ],
        cwd=repo,
        check=True,
        capture_output=True,
    )


def _repo() -> Path:
    """Create a repository with one committed text file."""
    repo = Path(tempfile.mkdtemp())
    _git(repo, "init", "-q")
    (repo / "tracked.txt").write_text("plain text\n", encoding="utf-8")
    _git(repo, "add", "tracked.txt")
    _git(repo, "commit", "-q", "-m", "initial")
    return repo


def _check(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603
        [sys.executable, str(_SCRIPT), *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )


def _expect(actual: object, expected: object, what: str) -> None:
    if actual != expected:
        msg = f"Expected {what} to be {expected!r}, got {actual!r}"
        raise AssertionError(msg)


def check_clean_tree_passes() -> None:
    """Validate that a tree without emoji passes."""
    _expect(_check(_repo()).returncode, 0, "exit status of a clean tree")


def check_untracked_file_is_checked() -> None:
    """Validate that an untracked file with an emoji fails and is named."""
    repo = _repo()
    (repo / "new.txt").write_text(f"hello {_EMOJI}\n", encoding="utf-8")
    result = _check(repo)
    _expect(result.returncode, 1, "exit status with an untracked emoji")
    _expect("new.txt" in result.stderr, True, "file name in the report")


def check_unstaged_edit_is_checked() -> None:
    """Validate that an emoji added to a tracked file fails."""
    repo = _repo()
    (repo / "tracked.txt").write_text(f"plain text {_EMOJI}\n", encoding="utf-8")
    result = _check(repo)
    _expect(result.returncode, 1, "exit status with an unstaged emoji")
    _expect("tracked.txt" in result.stderr, True, "file name in the report")


def check_staged_changes_need_cached() -> None:
    """Validate that `--cached` checks staged changes and passes them on."""
    repo = _repo()
    (repo / "tracked.txt").write_text(f"plain text {_EMOJI}\n", encoding="utf-8")
    _git(repo, "add", "tracked.txt")
    _expect(_check(repo, "--cached").returncode, 1, "exit status with --cached")
    _expect(_check(repo).returncode, 0, "exit status without --cached once staged")


def check_removing_an_emoji_passes() -> None:
    """Validate that deleting an emoji is not a finding."""
    repo = _repo()
    (repo / "tracked.txt").write_text(f"plain text {_EMOJI}\n", encoding="utf-8")
    _git(repo, "commit", "-q", "-am", "add emoji")
    (repo / "tracked.txt").write_text("plain text\n", encoding="utf-8")
    _expect(_check(repo).returncode, 0, "exit status after removing an emoji")


def check_binary_untracked_file_is_skipped() -> None:
    """Validate that an untracked binary file does not crash the check."""
    repo = _repo()
    (repo / "data.bin").write_bytes(b"\xff\xfe\x00\x80")
    _expect(_check(repo).returncode, 0, "exit status with a binary file")


if __name__ == "__main__":
    check_clean_tree_passes()
    check_untracked_file_is_checked()
    check_unstaged_edit_is_checked()
    check_staged_changes_need_cached()
    check_removing_an_emoji_passes()
    check_binary_untracked_file_is_skipped()
