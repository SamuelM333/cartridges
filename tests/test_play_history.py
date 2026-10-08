# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright 2026 samuelm333

"""Test loading and recording of Cartridges-recorded last-played times."""

import importlib
import json
import logging
import shutil
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
_TMP = _PATH.with_suffix(".json.tmp")


def _clear_cache() -> None:
    vars(play_history)["_history"] = None


def _remove(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink(missing_ok=True)


def _reset(contents: str | None = None) -> None:
    _clear_cache()
    _remove(_PATH)
    _remove(_TMP)
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


class _Collector(logging.Handler):
    """Collect the records logged by `play_history`."""

    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


def _record_failing_replace(collector: _Collector | None = None) -> None:
    """Record a launch while an empty directory blocks replacing the history file."""
    _PATH.mkdir()
    logger = logging.getLogger("cartridges.play_history")
    if collector:
        logger.addHandler(collector)
    try:
        play_history.record("steam_620", 1791489600)
    finally:
        if collector:
            logger.removeHandler(collector)


def _check_no_leftovers() -> None:
    if leftovers := list(_DATA_DIR.glob("*.tmp")):
        msg = f"Temporary files left behind: {leftovers}"
        raise AssertionError(msg)


def check_record_survives_replace_failure() -> None:
    """Validate that a failed replace does not raise and keeps the time in memory."""
    _reset()
    _record_failing_replace()

    if (history := play_history.load()) != {"steam_620": 1791489600}:
        msg = f"Expected the time to be kept in memory, got {history}"
        raise AssertionError(msg)

    _check_no_leftovers()
    _remove(_PATH)


def check_record_survives_mkdir_failure() -> None:
    """Validate that a data directory that cannot be created does not raise."""
    _reset()
    blocker = _DATA_DIR / "blocker"
    blocker.write_text("", encoding="utf-8")
    module_vars = vars(play_history)
    original = module_vars["DATA_DIR"], module_vars["_PATH"]
    module_vars["DATA_DIR"] = blocker / "data"
    module_vars["_PATH"] = blocker / "data" / "last-played.json"

    try:
        play_history.record("steam_620", 1791489600)
    finally:
        module_vars["DATA_DIR"], module_vars["_PATH"] = original
        blocker.unlink()

    if (history := play_history.load()) != {"steam_620": 1791489600}:
        msg = f"Expected the time to be kept in memory, got {history}"
        raise AssertionError(msg)


def check_previous_history_kept_on_failure() -> None:
    """Validate that a failed save leaves the saved history file unchanged."""
    _reset('{"steam_730": 5}')
    play_history.load()
    _TMP.mkdir()  # Opening the temporary file for writing now fails

    try:
        play_history.record("steam_620", 1791489600)
    finally:
        _TMP.rmdir()

    if (saved := json.loads(_PATH.read_text(encoding="utf-8"))) != {"steam_730": 5}:
        msg = f"Saved history was modified: {saved}"
        raise AssertionError(msg)


def check_failed_save_logs_one_warning() -> None:
    """Validate that a failed save logs exactly one warning and a good save none."""
    _reset()
    collector = _Collector()
    _record_failing_replace(collector)
    _remove(_PATH)

    if len(collector.records) != 1:
        msg = f"Expected one log record, got {len(collector.records)}"
        raise AssertionError(msg)

    entry = collector.records[0]
    if entry.levelno != logging.WARNING or "last-played.json" not in entry.getMessage():
        msg = f"Unexpected log record: {entry.levelname} {entry.getMessage()}"
        raise AssertionError(msg)

    collector.records.clear()
    logger = logging.getLogger("cartridges.play_history")
    logger.addHandler(collector)
    try:
        play_history.record("steam_730", 1791489700)
    finally:
        logger.removeHandler(collector)

    if collector.records:
        msg = f"Expected no log records after a good save, got {collector.records}"
        raise AssertionError(msg)


def check_later_save_includes_failed_time() -> None:
    """Validate that a later successful save also persists the time of a failed one."""
    _reset()
    _record_failing_replace()
    _remove(_PATH)
    play_history.record("steam_730", 1791489700)
    _clear_cache()

    expected = {"steam_620": 1791489600, "steam_730": 1791489700}
    if (history := play_history.load()) != expected:
        msg = f"Expected {expected}, got {history}"
        raise AssertionError(msg)


if __name__ == "__main__":
    check_missing_file()
    check_record_round_trip()
    check_invalid_json()
    check_invalid_entries()
    check_record_survives_replace_failure()
    check_record_survives_mkdir_failure()
    check_previous_history_kept_on_failure()
    check_failed_save_logs_one_warning()
    check_later_save_includes_failed_time()
