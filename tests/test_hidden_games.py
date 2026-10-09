# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright 2026 samuelm333

"""Test loading and recording of the games the user hid or unhid."""

import importlib
import sys
import tempfile
import types
from pathlib import Path

# Importing the real `cartridges` package needs the meson-generated `config.py`
# and compiled GSettings schemas, so stub the package with only what
# `hidden_games` uses.
_DATA_DIR = Path(tempfile.mkdtemp())
_package = types.ModuleType("cartridges")
_package.__path__ = [str(Path(__file__).resolve().parents[1] / "cartridges")]
_package.DATA_DIR = _DATA_DIR  # pyright: ignore[reportAttributeAccessIssue]
sys.modules["cartridges"] = _package

hidden_games = importlib.import_module("cartridges.hidden_games")
_PATH = _DATA_DIR / "hidden.json"


def _clear_cache() -> None:
    vars(hidden_games)["_hidden"] = None


def _reset(contents: str | bytes | None = None) -> None:
    _clear_cache()
    if _PATH.is_dir():
        _PATH.rmdir()
    _PATH.unlink(missing_ok=True)
    if isinstance(contents, bytes):
        _PATH.write_bytes(contents)
    elif contents is not None:
        _PATH.write_text(contents, encoding="utf-8")


def _expect(actual: object, expected: object, what: str) -> None:
    if actual != expected:
        msg = f"Expected {what} to be {expected!r}, got {actual!r}"
        raise AssertionError(msg)


def check_missing_file() -> None:
    """Validate that a missing file loads as empty."""
    _reset()
    _expect(hidden_games.load(), {}, "hidden games")


def check_record_round_trip() -> None:
    """Validate that hidden and unhidden choices survive reloading from disk."""
    _reset()
    hidden_games.record("steam_620", True)
    hidden_games.record("heroic_a", False)
    _clear_cache()

    _expect(
        hidden_games.load(),
        {"steam_620": True, "heroic_a": False},
        "hidden games after reload",
    )
    _expect(list(_DATA_DIR.glob("*.tmp")), [], "leftover temporary files")


def check_invalid_files() -> None:
    """Validate that damaged files load as empty without raising."""
    for contents in ("not json", b"\xff\xfe\x00", "[1, 2]", '"text"'):
        _reset(contents)
        _expect(hidden_games.load(), {}, f"hidden games for {contents!r}")


def check_invalid_entries() -> None:
    """Validate that entries whose value is not a boolean are skipped."""
    _reset('{"a": true, "b": 1, "c": "true", "d": null, "e": false}')
    _expect(hidden_games.load(), {"a": True, "e": False}, "valid entries")


def check_record_survives_save_failure() -> None:
    """Validate that a failed save does not raise and keeps the choice in memory."""
    _reset()
    _PATH.mkdir()  # An empty directory blocks replacing the file.

    hidden_games.record("steam_620", True)

    _expect(hidden_games.load(), {"steam_620": True}, "hidden games in memory")
    _expect(list(_DATA_DIR.glob("*.tmp")), [], "leftover temporary files")
    _reset()


if __name__ == "__main__":
    check_missing_file()
    check_record_round_trip()
    check_invalid_files()
    check_invalid_entries()
    check_record_survives_save_failure()
