# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright 2026 samuelm333

"""Test merging a fresh source scan into the library, and finding source data."""

import importlib
import sys
import tempfile
import types
from pathlib import Path
from typing import TYPE_CHECKING

import gi

gi.require_versions({"Gdk": "4.0", "Gtk": "4.0"})
from gi.repository import Gdk, GLib

if TYPE_CHECKING:
    from cartridges.games import Game


class _Settings:
    """Stand-in for the application's `Gio.Settings`.

    String keys in `user_values` count as set by the user.
    """

    def __init__(self) -> None:
        self.user_values: dict[str, str] = {}

    def get_boolean(self, _key: str) -> bool:
        return False

    def get_string(self, key: str) -> str:
        return self.user_values.get(key, "")

    def get_user_value(self, key: str) -> GLib.Variant | None:
        value = self.user_values.get(key)
        return None if value is None else GLib.Variant("s", value)


_SETTINGS = _Settings()


# Importing the real `cartridges` package needs the meson-generated `config.py`
# and compiled GSettings schemas, so stub the package with only what
# `games`, `importer` and `sources` use.
_package = types.ModuleType("cartridges")
_package.__path__ = [str(Path(__file__).resolve().parents[1] / "cartridges")]
_package.DATA_DIR = Path(tempfile.mkdtemp())  # pyright: ignore[reportAttributeAccessIssue]
_package.SETTINGS = _SETTINGS  # pyright: ignore[reportAttributeAccessIssue]
sys.modules["cartridges"] = _package

games = importlib.import_module("cartridges.games")
importer = importlib.import_module("cartridges.importer")
sources = importlib.import_module("cartridges.sources")


def _game(game_id: str, **props: object) -> "Game":
    game = games.Game(game_id=game_id, source="test", name=game_id, executable="true")
    for name, value in props.items():
        setattr(game, name, value)
    return game


def _ids(items: list["Game"]) -> list[str]:
    return [game.game_id for game in items]


def _expect(actual: object, expected: object, what: str) -> None:
    if actual != expected:
        msg = f"Expected {what} to be {expected!r}, got {actual!r}"
        raise AssertionError(msg)


def check_reconcile_adds_new() -> None:
    """Validate that scanned games missing from the library are added in scan order."""
    result = importer.reconcile([_game("a")], [_game("c"), _game("a"), _game("b")])
    _expect(_ids(result.added), ["c", "b"], "added")


def check_reconcile_removes_missing() -> None:
    """Validate that games no longer in the scan are removed."""
    result = importer.reconcile([_game("a"), _game("b")], [_game("b")])
    _expect(_ids(result.removed), ["a"], "removed")
    _expect(_ids(result.kept), ["b"], "kept")


def check_reconcile_keeps_objects() -> None:
    """Validate that kept games are the original objects, in library order."""
    a, b = _game("a"), _game("b")
    result = importer.reconcile([a, b], [_game("b"), _game("a")])
    _expect(_ids(result.kept), ["a", "b"], "kept order")
    if result.kept[0] is not a or result.kept[1] is not b:
        msg = "Expected kept games to be the original objects"
        raise AssertionError(msg)


def check_reconcile_preserves_user_fields() -> None:
    """Validate that a re-scan does not overwrite fields the user can change."""
    existing = _game(
        "a",
        name="Edited",
        executable="edited",
        developer="Edited Dev",
        hidden=True,
        removed=True,
        added=100,
    )
    scanned = _game("a", developer="Launcher Dev", added=200)

    kept = importer.reconcile([existing], [scanned]).kept[0]
    _expect(kept.name, "Edited", "name")
    _expect(kept.executable, "edited", "executable")
    _expect(kept.developer, "Edited Dev", "developer")
    _expect(kept.hidden, True, "hidden")
    _expect(kept.removed, True, "removed")
    _expect(kept.added, 100, "added")


def check_reconcile_merges_last_played() -> None:
    """Validate that the more recent last-played time wins."""
    newer_scan = importer.reconcile(
        [_game("a", last_played=100)], [_game("a", last_played=200)]
    )
    _expect(newer_scan.kept[0].last_played, 200, "last_played (newer scan)")

    older_scan = importer.reconcile(
        [_game("a", last_played=300)], [_game("a", last_played=200)]
    )
    _expect(older_scan.kept[0].last_played, 300, "last_played (older scan)")


def check_reconcile_fills_missing_cover_only() -> None:
    """Validate that a scanned cover is used only when the game has none."""
    old_cover = Gdk.Paintable.new_empty(1, 1)
    new_cover = Gdk.Paintable.new_empty(2, 2)

    without = importer.reconcile([_game("a")], [_game("a", cover=new_cover)])
    if without.kept[0].cover is not new_cover:
        msg = "Expected a game without a cover to take the scanned cover"
        raise AssertionError(msg)

    with_cover = importer.reconcile(
        [_game("a", cover=old_cover)], [_game("a", cover=new_cover)]
    )
    if with_cover.kept[0].cover is not old_cover:
        msg = "Expected a game with a cover to keep it"
        raise AssertionError(msg)


def check_reconcile_dedupes_scan() -> None:
    """Validate that a scan listing the same game twice adds it once."""
    first, second = _game("a", name="First"), _game("a", name="Second")
    result = importer.reconcile([], [first, second])
    _expect(_ids(result.added), ["a"], "added")
    if result.added[0] is not first:
        msg = "Expected the first duplicate in the scan to win"
        raise AssertionError(msg)


def check_reconcile_idempotent() -> None:
    """Validate that reconciling the same scan twice changes nothing."""
    scan = [_game("a"), _game("b"), _game("c")]
    first = importer.reconcile([_game("b"), _game("d")], scan)
    second = importer.reconcile(first.kept + first.added, scan)
    _expect(_ids(second.added), [], "added on second run")
    _expect(_ids(second.removed), [], "removed on second run")
    _expect(_ids(second.kept), ["b", "a", "c"], "kept on second run")


def check_location_user_set_is_strict() -> None:
    """Validate that a location the user picked is used even if it is missing."""
    existing = Path(tempfile.mkdtemp())
    _SETTINGS.user_values = {"steam-location": "~/missing-steam"}
    result = sources.location("steam-location", (existing,))
    _expect(result, Path.home() / "missing-steam", "location")


def check_location_default_autodetects() -> None:
    """Validate that without a user choice the first existing candidate is used."""
    missing = Path(tempfile.mkdtemp()) / "missing"
    first, second = Path(tempfile.mkdtemp()), Path(tempfile.mkdtemp())
    _SETTINGS.user_values = {}
    result = sources.location("steam-location", (missing, first, second))
    _expect(result, first, "location")


def check_location_none_found() -> None:
    """Validate that a missing location without a user choice raises."""
    _SETTINGS.user_values = {}
    try:
        sources.location("steam-location", (Path(tempfile.mkdtemp()) / "missing",))
    except FileNotFoundError:
        return
    msg = "Expected FileNotFoundError when no candidate exists"
    raise AssertionError(msg)


if __name__ == "__main__":
    check_reconcile_adds_new()
    check_reconcile_removes_missing()
    check_reconcile_keeps_objects()
    check_reconcile_preserves_user_fields()
    check_reconcile_merges_last_played()
    check_reconcile_fills_missing_cover_only()
    check_reconcile_dedupes_scan()
    check_reconcile_idempotent()
    check_location_user_set_is_strict()
    check_location_default_autodetects()
    check_location_none_found()
