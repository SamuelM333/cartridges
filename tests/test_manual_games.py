# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright 2026 samuelm333

"""Test saving, loading, and numbering of manually added games."""

import importlib
import json
import shutil
import sys
import tempfile
import types
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

import gi

gi.require_versions({"Gdk": "4.0", "Gtk": "4.0"})

if TYPE_CHECKING:
    from cartridges.games import Game

# Importing the real `cartridges` package needs the meson-generated `config.py`
# and compiled GSettings schemas, so stub the package with only what
# `games` and `sources.imported` use.
_DATA_DIR = Path(tempfile.mkdtemp())
_package = types.ModuleType("cartridges")
_package.__path__ = [str(Path(__file__).resolve().parents[1] / "cartridges")]
_package.DATA_DIR = _DATA_DIR  # pyright: ignore[reportAttributeAccessIssue]
_package.SETTINGS = None  # pyright: ignore[reportAttributeAccessIssue]
sys.modules["cartridges"] = _package

games = importlib.import_module("cartridges.games")
imported = importlib.import_module("cartridges.sources.imported")

_GAMES_DIR = _DATA_DIR / "games"


def _reset() -> None:
    """Start every check with an empty games directory."""
    shutil.rmtree(_GAMES_DIR, ignore_errors=True)
    _GAMES_DIR.mkdir(parents=True)


def _expect(actual: object, expected: object, what: str) -> None:
    if actual != expected:
        msg = f"Expected {what} to be {expected!r}, got {actual!r}"
        raise AssertionError(msg)


def _expect_raises_oserror(func: Callable[[], object], what: str) -> None:
    try:
        func()
    except OSError:
        return
    msg = f"Expected {what} to raise OSError"
    raise AssertionError(msg)


def _tmp_files() -> list[str]:
    return sorted(p.name for p in _GAMES_DIR.glob("*.tmp"))


def _new_game(
    name: str = "Test One",
    executable: str = "true",
    developer: str = "Dev",
    taken: tuple[str, ...] = (),
) -> "Game":
    game = imported.new(taken)
    game.name, game.executable, game.developer = name, executable, developer
    return game


def check_save_round_trip() -> None:
    """Validate that a saved game loads back with every value it was saved with."""
    _reset()
    game = _new_game()
    game.save()

    loaded = list(imported.get_games())
    _expect(len(loaded), 1, "number of loaded games")
    for prop in ("game_id", "name", "executable", "developer", "source", "added"):
        _expect(getattr(loaded[0], prop), getattr(game, prop), prop)
    _expect(_tmp_files(), [], "temporary files")


def check_save_creates_missing_directory() -> None:
    """Validate that saving works when the games directory does not exist yet."""
    shutil.rmtree(_GAMES_DIR, ignore_errors=True)
    _new_game().save()
    _expect(len(list(imported.get_games())), 1, "number of loaded games")


def check_edit_overwrites_record() -> None:
    """Validate that saving an edited game replaces its record, keeping its identity."""
    _reset()
    game = _new_game()
    game.save()

    game.name, game.executable = "Test Uno", "echo hi"
    game.save()

    loaded = list(imported.get_games())
    _expect(len(loaded), 1, "number of loaded games")
    _expect((loaded[0].name, loaded[0].executable), ("Test Uno", "echo hi"), "values")
    _expect(loaded[0].game_id, game.game_id, "game_id")
    _expect(loaded[0].added, game.added, "added")


def check_removed_state_round_trip() -> None:
    """Validate that removing a game and undoing the removal are both saved."""
    _reset()
    game = _new_game()
    game.save()

    game.removed = True
    game.save()
    _expect(next(imported.get_games()).removed, True, "removed after removal")

    game.removed = False
    game.save()
    _expect(next(imported.get_games()).removed, False, "removed after undo")


def check_next_number_skips_used() -> None:
    """Validate that the lowest unused number is chosen."""
    _expect(imported._next_number([0, 1, 3]), 2, "next number")  # noqa: SLF001
    _expect(imported._next_number([]), 0, "next number when none are used")  # noqa: SLF001
    _expect(imported._next_number([1, 2]), 0, "next number below the used ones")  # noqa: SLF001


def check_ignores_odd_file_names() -> None:
    """Validate that files without a number in their name cannot break numbering."""
    _reset()
    for name in ("imported_old.json", "imported_.json", "imported_1a.json"):
        (_GAMES_DIR / name).write_text("{}", encoding="utf-8")

    _expect(imported.new().game_id, "imported_0", "game_id")


def check_reserves_damaged_and_removed() -> None:
    """Validate that damaged and removed games keep their number and files."""
    _reset()
    damaged = _GAMES_DIR / "imported_4.json"
    damaged.write_bytes(b"not json")
    removed = _new_game()
    removed.game_id, removed.removed = "imported_5", True
    removed.save()

    game = _new_game()
    for number in (0, 1, 2, 3):
        _expect(imported.new().game_id, f"imported_{number}", "game_id")
        (_GAMES_DIR / f"imported_{number}.json").write_text("{}", encoding="utf-8")
    _expect(imported.new().game_id, "imported_6", "game_id after reserved numbers")

    game.save()
    _expect(damaged.read_bytes(), b"not json", "damaged file")


def check_unsaved_games_get_distinct_ids() -> None:
    """Validate that games that are not on disk yet are still counted."""
    _reset()
    first = imported.new()
    second = imported.new((first.game_id,))
    third = imported.new((first.game_id, second.game_id))
    _expect(
        [first.game_id, second.game_id, third.game_id],
        ["imported_0", "imported_1", "imported_2"],
        "game IDs",
    )


def _failing(name: str) -> Callable[..., object]:
    def fail(*_args: object, **_kwargs: object) -> object:
        msg = f"{name} failed"
        raise OSError(msg)

    return fail


def check_save_raises_on_replace_failure() -> None:
    """Validate that a failure to replace the file is raised and cleaned up."""
    _reset()
    game = _new_game()
    original = Path.replace
    Path.replace = _failing("replace")  # pyright: ignore[reportAttributeAccessIssue]
    try:
        _expect_raises_oserror(game.save, "save")
    finally:
        Path.replace = original  # pyright: ignore[reportAttributeAccessIssue]
    _expect(_tmp_files(), [], "temporary files")
    _expect(list(imported.get_games()), [], "loaded games")


def check_save_raises_on_mkdir_failure() -> None:
    """Validate that a failure to create the directory is raised."""
    shutil.rmtree(_GAMES_DIR, ignore_errors=True)
    game = _new_game()
    original = Path.mkdir
    Path.mkdir = _failing("mkdir")  # pyright: ignore[reportAttributeAccessIssue]
    try:
        _expect_raises_oserror(game.save, "save")
    finally:
        Path.mkdir = original  # pyright: ignore[reportAttributeAccessIssue]
    _expect(list(imported.get_games()), [], "loaded games")


def check_failed_save_keeps_previous_record() -> None:
    """Validate that a failed save leaves the earlier record unchanged."""
    _reset()
    game = _new_game()
    game.save()
    path = _GAMES_DIR / f"{game.game_id}.json"
    before = path.read_bytes()

    game.name = "Changed"
    original = Path.replace
    Path.replace = _failing("replace")  # pyright: ignore[reportAttributeAccessIssue]
    try:
        _expect_raises_oserror(game.save, "save")
    finally:
        Path.replace = original  # pyright: ignore[reportAttributeAccessIssue]
    _expect(path.read_bytes(), before, "record")
    _expect(_tmp_files(), [], "temporary files")


def check_failed_save_leaves_no_tmp_when_cleanup_fails() -> None:
    """Validate that the original error is raised even if cleanup also fails."""
    _reset()
    game = _new_game()
    original_replace, original_unlink = Path.replace, Path.unlink
    Path.replace = _failing("replace")  # pyright: ignore[reportAttributeAccessIssue]
    Path.unlink = _failing("unlink")  # pyright: ignore[reportAttributeAccessIssue]
    try:
        try:
            game.save()
        except OSError as e:
            _expect(str(e), "replace failed", "error")
        else:
            msg = "Expected save to raise OSError"
            raise AssertionError(msg)
    finally:
        Path.replace, Path.unlink = original_replace, original_unlink  # pyright: ignore[reportAttributeAccessIssue]
        for tmp in _GAMES_DIR.glob("*.tmp"):
            tmp.unlink()


def check_later_save_writes_full_state() -> None:
    """Validate that a save after a failed one writes the latest values."""
    _reset()
    game = _new_game()
    original = Path.replace
    Path.replace = _failing("replace")  # pyright: ignore[reportAttributeAccessIssue]
    try:
        _expect_raises_oserror(game.save, "save")
    finally:
        Path.replace = original  # pyright: ignore[reportAttributeAccessIssue]

    game.name = "Latest"
    game.save()
    loaded = list(imported.get_games())
    _expect([g.name for g in loaded], ["Latest"], "loaded names")


def check_damaged_file_untouched_by_other_saves() -> None:
    """Validate that saving one game never changes another game's damaged file."""
    _reset()
    damaged = _GAMES_DIR / "imported_7.json"
    damaged.write_bytes(b"not json")
    future = _GAMES_DIR / "imported_8.json"
    future.write_text(json.dumps({"version": 99.0}), encoding="utf-8")
    before = future.read_bytes()

    _new_game().save()

    _expect(damaged.read_bytes(), b"not json", "damaged file")
    _expect(future.read_bytes(), before, "newer-format file")
    _expect(len(list(imported.get_games())), 1, "number of loaded games")


if __name__ == "__main__":
    check_save_round_trip()
    check_save_creates_missing_directory()
    check_edit_overwrites_record()
    check_removed_state_round_trip()
    check_next_number_skips_used()
    check_ignores_odd_file_names()
    check_reserves_damaged_and_removed()
    check_unsaved_games_get_distinct_ids()
    check_save_raises_on_replace_failure()
    check_save_raises_on_mkdir_failure()
    check_failed_save_keeps_previous_record()
    check_failed_save_leaves_no_tmp_when_cleanup_fails()
    check_later_save_writes_full_state()
    check_damaged_file_untouched_by_other_saves()
