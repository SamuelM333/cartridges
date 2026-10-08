# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright 2026 samuelm333

"""Test loading and recording of Cartridges-recorded last-played times."""

import importlib
import sys
import tempfile
import types
from pathlib import Path

# Importing the real `cartridges` package needs the meson-generated `config.py`
# and compiled GSettings schemas, so stub the package with only what
# `play_history` uses.
_DATA_DIR = Path(tempfile.mkdtemp())
_package = types.ModuleType("cartridges")
_package.__path__ = [str(Path(__file__).resolve().parents[1] / "cartridges")]
_package.DATA_DIR = _DATA_DIR  # pyright: ignore[reportAttributeAccessIssue]
sys.modules["cartridges"] = _package

play_history = importlib.import_module("cartridges.play_history")
_PATH = _DATA_DIR / "last-played.json"


def _clear_cache() -> None:
    vars(play_history)["_history"] = None


def _reset(contents: str | None = None) -> None:
    _clear_cache()
    _PATH.unlink(missing_ok=True)
    if contents is not None:
        _PATH.write_text(contents, encoding="utf-8")


def check_missing_file() -> None:
    """Validate that a missing history file loads as empty."""
    _reset()
    if (history := play_history.load()) != {}:
        msg = f"Expected empty history, got {history}"
        raise AssertionError(msg)


def check_record_round_trip() -> None:
    """Validate that a recorded time survives reloading from disk."""
    _reset()
    play_history.record("steam_620", 1791489600)
    _clear_cache()

    if (history := play_history.load()) != {"steam_620": 1791489600}:
        msg = f"Unexpected history after reload: {history}"
        raise AssertionError(msg)

    if leftovers := list(_DATA_DIR.glob("*.tmp")):
        msg = f"Temporary files left behind: {leftovers}"
        raise AssertionError(msg)


def check_invalid_json() -> None:
    """Validate that an invalid history file loads as empty without raising."""
    _reset("not json")
    if (history := play_history.load()) != {}:
        msg = f"Expected empty history, got {history}"
        raise AssertionError(msg)


def check_invalid_entries() -> None:
    """Validate that entries that are not non-negative integers are skipped."""
    _reset('{"a": 5, "b": "x", "c": -1, "d": true}')
    if (history := play_history.load()) != {"a": 5}:
        msg = f"Expected only valid entries, got {history}"
        raise AssertionError(msg)


if __name__ == "__main__":
    check_missing_file()
    check_record_round_trip()
    check_invalid_json()
    check_invalid_entries()
