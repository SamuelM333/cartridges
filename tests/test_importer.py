# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright 2026 samuelm333

"""Test merging a fresh source scan into the library, and finding source data."""

import asyncio
import importlib
import sqlite3
import sys
import tempfile
import types
from pathlib import Path
from typing import TYPE_CHECKING

import gi

gi.require_versions({"Gdk": "4.0", "Gtk": "4.0"})
from gi.repository import Gdk, GLib

if TYPE_CHECKING:
    from collections.abc import Generator

    from cartridges.games import Game
    from cartridges.sources import Source


class _Settings:
    """Stand-in for the application's `Gio.Settings`.

    String keys in `user_values` count as set by the user.
    """

    def __init__(self) -> None:
        self.user_values: dict[str, str] = {}
        self.booleans: dict[str, bool] = {}

    def get_boolean(self, key: str) -> bool:
        return self.booleans.get(key, False)

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
hidden_games = importlib.import_module("cartridges.hidden_games")
importer = importlib.import_module("cartridges.importer")
saved_library = importlib.import_module("cartridges.saved_library")
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
        added=100,
    )
    scanned = _game("a", developer="Launcher Dev", added=200)

    kept = importer.reconcile([existing], [scanned]).kept[0]
    _expect(kept.name, "Edited", "name")
    _expect(kept.executable, "edited", "executable")
    _expect(kept.developer, "Edited Dev", "developer")
    _expect(kept.hidden, True, "hidden")
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


def check_reconcile_removed_returns_as_added() -> None:
    """Validate that a game the user removed is replaced by the scanned game."""
    removed = _game("a", removed=True)
    scanned = _game("a")
    result = importer.reconcile([removed], [scanned])
    _expect(_ids(result.kept), [], "kept")
    _expect(_ids(result.removed), ["a"], "removed")
    _expect(_ids(result.added), ["a"], "added")
    if result.added[0] is not scanned or result.removed[0] is not removed:
        msg = "Expected the scanned game to replace the removed one"
        raise AssertionError(msg)


def check_reconcile_removed_uninstalled() -> None:
    """Validate that a removed game missing from the scan is only removed."""
    result = importer.reconcile([_game("a", removed=True)], [])
    _expect(_ids(result.removed), ["a"], "removed")
    _expect(_ids(result.added), [], "added")


def check_reconcile_removed_idempotent() -> None:
    """Validate that once a removed game is replaced, the next scan changes nothing."""
    scan = [_game("a")]
    first = importer.reconcile([_game("a", removed=True)], scan)
    second = importer.reconcile(first.kept + first.added, scan)
    _expect(_ids(second.added), [], "added on second run")
    _expect(_ids(second.removed), [], "removed on second run")


def check_reconcile_other_games_unaffected() -> None:
    """Validate that games the user did not remove are still kept as they are."""
    gone, normal = _game("a", removed=True), _game("b")
    result = importer.reconcile([gone, normal], [_game("a"), _game("b")])
    _expect(_ids(result.kept), ["b"], "kept")
    if result.kept[0] is not normal:
        msg = "Expected the game that was not removed to be kept"
        raise AssertionError(msg)


def _source(ident: str, *scanned: "Game", startup: bool = True) -> "Source":
    module = types.SimpleNamespace(
        ID=ident, NAME=ident, get_games=lambda: (game for game in scanned)
    )
    return _build(module, startup=startup)


def _build(module: types.SimpleNamespace, *, startup: bool = True) -> "Source":
    _SETTINGS.booleans = {"import-on-startup": startup, module.ID: True}
    return sources.Source(module, 0)  # pyright: ignore[reportArgumentType]


def _failing(ident: str, error: Exception) -> types.SimpleNamespace:
    def get_games() -> "Generator[Game]":
        raise error
        yield  # pyright: ignore[reportUnreachable]

    return types.SimpleNamespace(ID=ident, NAME=ident, get_games=get_games)


def _forbidden(ident: str) -> types.SimpleNamespace:
    def get_games() -> "Generator[Game]":
        msg = "Expected the launcher not to be read"
        raise AssertionError(msg)
        yield  # pyright: ignore[reportUnreachable]

    return types.SimpleNamespace(ID=ident, NAME=ident, get_games=get_games)


def _save_library(**by_source: list["Game"]) -> None:
    vars(saved_library)["_library"] = dict(by_source)


def _games_of(source: "Source") -> list[str]:
    return [
        source.do_get_item(i).game_id  # pyright: ignore[reportOptionalMemberAccess]
        for i in range(source.do_get_n_items())
    ]


def _reset_hidden(stored: dict[str, bool]) -> None:
    vars(hidden_games)["_hidden"] = dict(stored)


def check_scan_applies_stored_hidden() -> None:
    """Validate that a choice the user made overrides what the launcher reports."""
    _reset_hidden({"a": True, "b": False})
    source = _source(
        "fake", _game("a"), _game("b", hidden=True), _game("c", hidden=True)
    )
    _expect(
        [source.do_get_item(i).hidden for i in range(3)],  # pyright: ignore[reportOptionalMemberAccess]
        [True, False, True],
        "hidden",
    )


def check_hidden_changes_are_recorded() -> None:
    """Validate that hiding and unhiding is remembered, and loading is not."""
    _reset_hidden({})
    source = _source("fake", _game("a", hidden=True), _game("b"))
    _expect(hidden_games.load(), {}, "hidden games after loading")

    a, b = source.do_get_item(0), source.do_get_item(1)
    a.hidden = False  # pyright: ignore[reportOptionalMemberAccess]
    b.hidden = True  # pyright: ignore[reportOptionalMemberAccess]
    _expect(hidden_games.load(), {"a": False, "b": True}, "hidden games")

    added = _game("c")
    source.append(added)
    added.hidden = True
    _expect(hidden_games.load().get("c"), True, "hidden game added later")


def check_removed_is_saved_for_added_games_only() -> None:
    """Validate that only manually added games remember being removed."""
    saved = games.GAMES_DIR / "imported_0.json"
    saved.unlink(missing_ok=True)

    launcher = _source("fake", _game("fake_1"))
    launcher.do_get_item(0).removed = True  # pyright: ignore[reportOptionalMemberAccess]
    _expect(list(games.GAMES_DIR.glob("fake_*.json")), [], "launcher game files")

    manual = _source("imported", _game("imported_0", source="imported"))
    manual.do_get_item(0).removed = True  # pyright: ignore[reportOptionalMemberAccess]
    _expect(saved.exists(), True, "manually added game file")
    _expect('"removed": true' in saved.read_text(encoding="utf-8"), True, "removed")


def check_startup_off_uses_saved_library() -> None:
    """Validate that the saved games are shown without reading the launcher."""
    _save_library(fake=[_game("fake_1"), _game("fake_2")])
    source = _build(_forbidden("fake"), startup=False)
    _expect(_games_of(source), ["fake_1", "fake_2"], "games")


def check_startup_off_without_saved_library() -> None:
    """Validate that a source with nothing saved starts empty."""
    _save_library()
    source = _build(_forbidden("fake"), startup=False)
    _expect(_games_of(source), [], "games")


def check_startup_on_scan_wins() -> None:
    """Validate that a working scan is used instead of the saved games."""
    _save_library(fake=[_game("old")])
    source = _source("fake", _game("new"), startup=True)
    _expect(_games_of(source), ["new"], "games")


def check_startup_on_failure_uses_saved_library() -> None:
    """Validate that a source that cannot be read keeps its saved games."""
    for error in (OSError(), sqlite3.Error()):
        _save_library(fake=[_game("old")])
        source = _build(_failing("fake", error), startup=True)
        _expect(_games_of(source), ["old"], f"games after {type(error).__name__}")


def check_added_games_ignore_saved_library() -> None:
    """Validate that manually added games are always scanned."""
    _save_library(imported=[_game("saved")])
    source = _source("imported", _game("imported_0", source="imported"), startup=False)
    _expect(_games_of(source), ["imported_0"], "games")


def _count_saves() -> list[int]:
    calls: list[int] = []
    vars(saved_library)["request_save"] = lambda: calls.append(1)
    return calls


def check_launcher_changes_request_a_save() -> None:
    """Validate that removing a game or changing its cover asks for a save."""
    _save_library()
    calls = _count_saves()
    launcher = _source("fake", _game("fake_1"))
    game = launcher.do_get_item(0)

    game.removed = True  # pyright: ignore[reportOptionalMemberAccess]
    _expect(len(calls), 1, "saves after removing a launcher game")
    game.cover = Gdk.Paintable.new_empty(1, 1)  # pyright: ignore[reportOptionalMemberAccess]
    _expect(len(calls), 2, "saves after changing its cover")

    manual = _source("imported", _game("imported_1", source="imported"))
    manual.do_get_item(0).removed = True  # pyright: ignore[reportOptionalMemberAccess]
    _expect(len(calls), 2, "saves after removing a manually added game")


def check_import_requests_a_save() -> None:
    """Validate that an import asks for the library to be saved once."""
    _save_library()
    calls = _count_saves()
    sources.model.remove_all()
    sources.model.append(_source("fake", _game("fake_1")))
    asyncio.run(importer.import_games())
    sources.model.remove_all()
    _expect(len(calls), 1, "saves after an import")


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
    check_reconcile_removed_returns_as_added()
    check_reconcile_removed_uninstalled()
    check_reconcile_removed_idempotent()
    check_reconcile_other_games_unaffected()
    check_startup_off_uses_saved_library()
    check_startup_off_without_saved_library()
    check_startup_on_scan_wins()
    check_startup_on_failure_uses_saved_library()
    check_added_games_ignore_saved_library()
    check_launcher_changes_request_a_save()
    check_import_requests_a_save()
    check_scan_applies_stored_hidden()
    check_hidden_changes_are_recorded()
    check_removed_is_saved_for_added_games_only()
    check_location_user_set_is_strict()
    check_location_default_autodetects()
    check_location_none_found()
