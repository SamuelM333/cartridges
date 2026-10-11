# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright 2026 samuelm333

"""Test collections: the dialog helper, persistence, and which games a view lists."""

import importlib
import logging
import os
import sys
import tempfile
import types
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

import gi

gi.require_versions({"Adw": "1", "Gdk": "4.0", "Gtk": "4.0"})
from gi.repository import Gio, GLib, Gtk

if TYPE_CHECKING:
    from cartridges.collections import Collection
    from cartridges.games import Game


class _Settings:
    """Stand-in for the application's `Gio.Settings`, holding only collections."""

    def __init__(self) -> None:
        self.value = GLib.Variant("aa{sv}", [])

    def get_boolean(self, _key: str) -> bool:
        return False

    def get_string(self, _key: str) -> str:
        return ""

    def get_user_value(self, _key: str) -> GLib.Variant | None:
        return None

    def get_value(self, _key: str) -> GLib.Variant:
        return self.value

    def set_value(self, _key: str, value: GLib.Variant) -> None:
        self.value = value


_SETTINGS = _Settings()

# Importing the real `cartridges` package needs the meson-generated `config.py`
# and compiled GSettings schemas, so stub the package with only what
# `collections`, `games`, and the collections UI use.
_package = types.ModuleType("cartridges")
_package.__path__ = [str(Path(__file__).resolve().parents[1] / "cartridges")]
_package.DATA_DIR = Path(tempfile.mkdtemp())  # pyright: ignore[reportAttributeAccessIssue]
_package.SETTINGS = _SETTINGS  # pyright: ignore[reportAttributeAccessIssue]
sys.modules["cartridges"] = _package

# Keep expected warnings out of the test output.
logging.getLogger("cartridges").addHandler(logging.NullHandler())

games = importlib.import_module("cartridges.games")
collections = importlib.import_module("cartridges.collections")
imported = importlib.import_module("cartridges.sources.imported")
ui_collections = importlib.import_module("cartridges.ui.collections")


class _Records(logging.Handler):
    """Collect the log records emitted while it is attached to the root logger."""

    def __init__(self) -> None:
        super().__init__(logging.DEBUG)
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


class _FakeWindow:
    """Stand-in for the main window that records the toasts sent to it."""

    def __init__(self) -> None:
        self.toasts: list[tuple[str, Callable[[], object] | None]] = []

    def send_toast(
        self, title: str, *, undo: Callable[[], object] | None = None
    ) -> None:
        self.toasts.append((title, undo))


def _expect(actual: object, expected: object, what: str) -> None:
    if actual != expected:
        msg = f"Expected {what} to be {expected!r}, got {actual!r}"
        raise AssertionError(msg)


def _game(game_id: str, **props: object) -> "Game":
    game = games.Game(game_id=game_id, source="test", name=game_id, executable="true")
    for name, value in props.items():
        setattr(game, name, value)
    return game


def _logged(call: Callable[[], object]) -> list[logging.LogRecord]:
    """Run `call` and return the records it logged."""
    root = logging.getLogger()
    handler, level = _Records(), root.level
    root.addHandler(handler)
    root.setLevel(logging.DEBUG)
    try:
        call()
    finally:
        root.removeHandler(handler)
        root.setLevel(level)
    return handler.records


def _reset() -> None:
    """Start without collections in memory or in the stored setting."""
    collections.model.remove_all()
    _SETTINGS.value = GLib.Variant("aa{sv}", [])


def _entry(
    name: str,
    *,
    icon: str = "star",
    game_ids: tuple[str, ...] = (),
    removed: bool = False,
) -> dict[str, GLib.Variant]:
    return {
        "name": GLib.Variant("s", name),
        "icon": GLib.Variant("s", icon),
        "game-ids": GLib.Variant("as", game_ids),
        "removed": GLib.Variant("b", removed),
    }


def _store(*entries: dict[str, GLib.Variant]) -> None:
    """Put `entries` in the stored setting, as an earlier run would have."""
    _SETTINGS.value = GLib.Variant("aa{sv}", list(entries))


def _stored() -> list[dict[str, object]]:
    return _SETTINGS.value.unpack()


def _names(model: Gio.ListModel) -> list[str]:
    return [model.get_item(i).name for i in range(model.get_n_items())]  # pyright: ignore[reportOptionalMemberAccess, reportAttributeAccessIssue]


def check_icons_and_defaults() -> None:
    """Validate the 21 icons and the defaults of a new collection."""
    expected = {
        "collection",
        "star",
        "heart",
        "music",
        "people",
        "skull",
        "private",
        "globe",
        "map",
        "city",
        "car",
        "horse",
        "sprout",
        "step-over",
        "gamepad",
        "ball",
        "puzzle",
        "flashlight",
        "knife",
        "gun",
        "fist",
    }
    _expect(len(collections.ICONS), 21, "number of icons")
    _expect({icon.name for icon in collections.ICONS}, expected, "icon names")
    _expect(all(icon.a11y_label for icon in collections.ICONS), True, "icon labels")

    collection = collections.Collection()
    _expect(collection.icon, "collection", "default icon")
    _expect(collection.icon_name, "collection-symbolic", "default icon name")


def check_editable_validity() -> None:
    """Validate when the dialog allows applying, including a name of spaces."""
    _reset()
    editable = ui_collections.CollectionEditable()
    _expect(editable.valid, False, "valid without a name")

    editable.name = "Co-op"
    _expect(editable.valid, False, "valid without an icon")

    editable.icon = "star"
    _expect(editable.valid, True, "valid with a name and an icon")

    editable.name = "   "
    _expect(editable.valid, True, "valid with a name of only spaces")

    editable.name = ""
    _expect(editable.valid, False, "valid after clearing the name")

    editable.apply()
    _expect(collections.model.get_n_items(), 0, "collections after an invalid apply")


def check_apply_creates_and_edits() -> None:
    """Validate that apply creates a collection, with a game, or edits one."""
    _reset()
    editable = ui_collections.CollectionEditable(name="Co-op", icon="star")
    editable.apply()

    _expect(_names(collections.model), ["Co-op"], "collections after create")
    created = collections.model.get_item(0)
    _expect(created.icon, "star", "icon after create")  # pyright: ignore[reportOptionalMemberAccess]
    _expect(_stored()[0]["name"], "Co-op", "stored name")
    _expect(_stored()[0]["icon"], "star", "stored icon")

    with_game = ui_collections.CollectionEditable(
        name="Mine", icon="heart", game=_game("steam_1")
    )
    with_game.apply()
    _expect("steam_1" in with_game.collection, True, "game in the new collection")

    edit = ui_collections.CollectionEditable(
        collection=created, name="Renamed", icon="music"
    )
    edit.apply()
    _expect(collections.model.get_n_items(), 2, "collections after an edit")
    _expect(created.name, "Renamed", "name after edit")  # pyright: ignore[reportOptionalMemberAccess]
    _expect(created.icon, "music", "icon after edit")  # pyright: ignore[reportOptionalMemberAccess]
    _expect(
        sorted(str(entry["name"]) for entry in _stored()),
        ["Mine", "Renamed"],
        "stored names",
    )


def check_remove_and_undo() -> None:
    """Validate that removing sends an undo toast and undoing restores it."""
    _reset()
    collection = collections.Collection(name="Co-op", icon="star")
    collections.model.append(collection)
    collections.save()

    window = _FakeWindow()
    original = vars(ui_collections)["_window"]
    vars(ui_collections)["_window"] = lambda: window
    try:
        ui_collections.remove(collection)
        _expect(collection.removed, True, "removed after remove")
        _expect(_stored()[0]["removed"], True, "stored removed")
        _expect(window.toasts[0][0], "Co-op removed", "toast title")
        undo = window.toasts[0][1]
        _expect(callable(undo), True, "toast has an undo")

        if undo is not None:
            undo()
        _expect(collection.removed, False, "removed after undo")
        _expect(_stored()[0]["removed"], False, "stored removed after undo")
    finally:
        vars(ui_collections)["_window"] = original


def check_sidebar_order() -> None:
    """Validate the alphabetical order, and that removed collections leave."""
    _reset()
    for name in ("b", "A", "c"):
        collections.model.append(collections.Collection(name=name))
    _expect(_names(ui_collections.model), ["A", "b", "c"], "sidebar order")

    collections.model.get_item(0).removed = True  # pyright: ignore[reportOptionalMemberAccess]
    _expect(_names(ui_collections.model), ["A", "c"], "sidebar after removing b")
    _expect(collections.model.get_n_items(), 3, "collections kept in memory")


def check_collection_membership() -> None:
    """Validate adding, discarding, and the change signal of a collection."""
    collection = collections.Collection(game_ids=["a", "b"])
    _expect("a" in collection, True, "contains a")
    _expect(sorted(collection), ["a", "b"], "iteration")

    changes: list[int] = []
    collection.connect("items-changed", lambda *_: changes.append(1))

    collection.add("c")
    _expect(len(changes), 1, "changes after adding c")
    collection.add("c")
    _expect(len(changes), 1, "changes after adding c again")
    collection.discard("a")
    _expect(len(changes), 2, "changes after discarding a")
    collection.discard("zzz")
    _expect(len(changes), 2, "changes after discarding an absent game")
    _expect(sorted(collection), ["b", "c"], "members")


def check_collection_filter() -> None:
    """Validate that a collection limits the games and follows its changes."""
    store = Gio.ListStore(item_type=games.Game)
    for ident in ("a", "b", "c"):
        store.append(_game(ident))

    collection_filter = ui_collections.CollectionFilter()
    # The window sets this when it is created, so match that.
    collection_filter.collection = None
    model = Gtk.FilterListModel(model=store, filter=collection_filter)

    def listed() -> list[str]:
        return [model.get_item(i).game_id for i in range(model.get_n_items())]  # pyright: ignore[reportOptionalMemberAccess, reportAttributeAccessIssue]

    _expect(listed(), ["a", "b", "c"], "games without a collection")

    collection = collections.Collection(game_ids=["a", "c"])
    collection_filter.collection = collection
    _expect(listed(), ["a", "c"], "games in the collection")

    collection.add("b")
    _expect(listed(), ["a", "b", "c"], "games after adding b")
    collection.discard("a")
    _expect(listed(), ["b", "c"], "games after discarding a")

    collection_filter.collection = None
    _expect(listed(), ["a", "b", "c"], "games after closing the collection")


def check_save_load_round_trip() -> None:
    """Validate that collections survive saving and loading."""
    _reset()
    collections.model.append(
        collections.Collection(name="Co-op", icon="star", game_ids=["x", "y"])
    )
    collections.model.append(collections.Collection(name="Solo", icon="heart"))
    collections.save()

    _expect(_SETTINGS.value.get_type_string(), "aa{sv}", "stored type")
    for entry in _stored():
        _expect(
            set(entry), {"name", "icon", "game-ids", "removed"}, "stored entry keys"
        )

    collections.model.remove_all()
    collections.load()
    loaded = {
        collection.name: (collection.icon, sorted(collection))
        for collection in collections.model
    }
    _expect(
        loaded,
        {"Co-op": ("star", ["x", "y"]), "Solo": ("heart", [])},
        "loaded collections",
    )


def check_removed_collections_do_not_return() -> None:
    """Validate that a removed collection is purged, unless undone first."""
    _reset()
    _store(_entry("keep"), _entry("gone", removed=True))
    collections.load()
    _expect(_names(collections.model), ["keep"], "loaded collections")
    _expect([entry["name"] for entry in _stored()], ["keep"], "stored after load")

    collection = collections.model.get_item(0)
    collection.removed = True  # pyright: ignore[reportOptionalMemberAccess]
    collections.save()
    collection.removed = False  # pyright: ignore[reportOptionalMemberAccess]
    collections.save()
    collections.model.remove_all()
    collections.load()
    _expect(_names(collections.model), ["keep"], "collections after an undo")


def check_invalid_entries_warn() -> None:
    """Validate that an unreadable entry is skipped with one warning each."""
    _reset()
    missing_ids = _entry("no ids")
    del missing_ids["game-ids"]
    wrong_type = _entry("wrong games")
    wrong_type["game-ids"] = GLib.Variant("i", 5)
    _store(_entry("valid"), missing_ids, wrong_type)

    records = _logged(collections.load)
    warnings = [r for r in records if r.levelno == logging.WARNING]
    _expect(len(warnings), 2, "warnings for two bad entries")
    _expect(
        all(r.getMessage().startswith("Ignored invalid collection") for r in warnings),
        True,
        "warning text",
    )
    _expect(_names(collections.model), ["valid"], "collections that loaded")


def check_membership_pruning() -> None:
    """Validate that only missing manually added games leave a collection."""
    _reset()
    _store(
        _entry(
            "Mixed",
            game_ids=("imported_1", "imported_2", "steam_620", "lutris_9"),
        )
    )
    original = vars(imported)["get_paths"]
    vars(imported)["get_paths"] = lambda: iter([Path("imported_1.json")])
    try:
        collections.load()
    finally:
        vars(imported)["get_paths"] = original

    collection: Collection = collections.model.get_item(0)  # pyright: ignore[reportAssignmentType]
    _expect(
        sorted(collection),
        ["imported_1", "lutris_9", "steam_620"],
        "games after pruning",
    )


def check_hidden_filter_unit() -> None:
    """Validate when the extra filter matches, its strictness, and its signal."""
    extra = ui_collections.HiddenInCollectionFilter()
    item = _game("x")
    _expect(extra.enabled, False, "default of enabled")
    _expect(extra.hidden_only, False, "default of hidden_only")
    _expect(extra.collection, None, "default of collection")
    _expect(extra.match(item), False, "match with nothing set")
    _expect(extra.get_strictness(), Gtk.FilterMatch.NONE, "strictness with nothing")

    changes: list[int] = []
    extra.connect("changed", lambda *_: changes.append(1))

    extra.collection = collections.Collection(name="c")
    _expect(len(changes), 1, "changes after setting the collection")
    _expect(extra.match(item), False, "match without the preference")
    _expect(extra.get_strictness(), Gtk.FilterMatch.NONE, "strictness without it")

    extra.enabled = True
    _expect(len(changes), 2, "changes after enabling")
    _expect(extra.match(item), True, "match with both")
    _expect(extra.get_strictness(), Gtk.FilterMatch.ALL, "strictness with both")

    extra.hidden_only = True
    _expect(len(changes), 3, "changes after listing only hidden games")
    _expect(extra.match(item), False, "match while listing only hidden games")
    _expect(extra.get_strictness(), Gtk.FilterMatch.NONE, "strictness then")
    extra.hidden_only = False

    extra.collection = None
    _expect(extra.match(item), False, "match with the preference only")

    extra.collection = collections.Collection(name="c")
    extra.enabled = False
    _expect(extra.match(item), False, "match after disabling")


# Freeing an `EveryFilter` that holds a `CollectionFilter` crashes GTK. The
# window never frees its filters, so keep these alive to match.
_KEPT: list[object] = []


class _Grid:
    """The filter tree of the main grid, as built in `window.blp`."""

    def __init__(self) -> None:
        _KEPT.append(self)
        self.visible = _game("visible")
        self.hidden_in = _game("hidden_in", hidden=True)
        self.hidden_out = _game("hidden_out", hidden=True)
        store = Gio.ListStore(item_type=games.Game)
        for game in (self.visible, self.hidden_in, self.hidden_out):
            store.append(game)

        self.collection = collections.Collection(
            name="Launchers", game_ids=["visible", "hidden_in"]
        )
        self.collection_filter = ui_collections.CollectionFilter()
        self.collection_filter.collection = None
        self.hidden_filter = Gtk.BoolFilter(
            expression=Gtk.PropertyExpression.new(games.Game, None, "hidden"),
            invert=True,
        )
        self.extra = ui_collections.HiddenInCollectionFilter()
        self.extra.collection = None

        hidden_rule = Gtk.AnyFilter()
        hidden_rule.append(self.hidden_filter)
        hidden_rule.append(self.extra)
        every = Gtk.EveryFilter()
        every.append(self.collection_filter)
        every.append(hidden_rule)
        self.model = Gtk.FilterListModel(model=store, filter=every, watch_items=True)

    def open(self, collection: "Collection | None") -> None:
        self.collection_filter.collection = collection
        self.extra.collection = collection

    def set_show_hidden(self, *, on: bool) -> None:
        self.hidden_filter.props.invert = not on
        self.extra.hidden_only = on

    def set_preference(self, *, on: bool) -> None:
        self.extra.enabled = on

    def listed(self) -> list[str]:
        return sorted(
            self.model.get_item(i).game_id  # pyright: ignore[reportOptionalMemberAccess, reportAttributeAccessIssue]
            for i in range(self.model.get_n_items())
        )


def check_hidden_rule_table() -> None:
    """Validate every row of the table in contracts/visibility-rules.md."""
    rows = [
        # (open the collection, show hidden games, preference, expected games)
        (False, False, False, ["visible"]),
        (False, False, True, ["visible"]),
        (False, True, False, ["hidden_in", "hidden_out"]),
        (False, True, True, ["hidden_in", "hidden_out"]),
        (True, False, False, ["visible"]),
        (True, False, True, ["hidden_in", "visible"]),
        (True, True, False, ["hidden_in"]),
        (True, True, True, ["hidden_in"]),
    ]
    for in_collection, show_hidden, preference, expected in rows:
        grid = _Grid()
        grid.open(grid.collection if in_collection else None)
        grid.set_show_hidden(on=show_hidden)
        grid.set_preference(on=preference)
        _expect(
            grid.listed(),
            expected,
            f"games for collection={in_collection} show={show_hidden} "
            f"preference={preference}",
        )


def check_hidden_rule_live() -> None:
    """Validate that the grid follows hiding, unhiding, and the preference."""
    grid = _Grid()
    grid.open(grid.collection)
    _expect(grid.listed(), ["visible"], "start, preference off")

    grid.visible.hidden = True
    _expect(grid.listed(), [], "hiding a member, preference off")
    grid.visible.hidden = False
    _expect(grid.listed(), ["visible"], "unhiding it, preference off")

    grid.set_preference(on=True)
    _expect(grid.listed(), ["hidden_in", "visible"], "turning the preference on")

    grid.visible.hidden = True
    _expect(grid.listed(), ["hidden_in", "visible"], "hiding a member, preference on")
    grid.visible.hidden = False
    _expect(grid.listed(), ["hidden_in", "visible"], "unhiding it, preference on")
    _expect("visible" in grid.collection, True, "hiding never changes membership")

    grid.set_show_hidden(on=True)
    _expect(grid.listed(), ["hidden_in"], "Show Hidden Games on, preference on")
    grid.set_show_hidden(on=False)
    _expect(grid.listed(), ["hidden_in", "visible"], "Show Hidden Games off again")

    grid.open(None)
    _expect(grid.listed(), ["visible"], "closing the collection, preference on")

    grid.open(grid.collection)
    grid.set_preference(on=False)
    _expect(grid.listed(), ["visible"], "turning the preference off")


if __name__ == "__main__":
    check_icons_and_defaults()
    check_editable_validity()
    check_apply_creates_and_edits()
    check_remove_and_undo()
    check_sidebar_order()
    check_collection_membership()
    check_collection_filter()
    check_save_load_round_trip()
    check_removed_collections_do_not_return()
    check_invalid_entries_warn()
    check_membership_pruning()
    check_hidden_filter_unit()
    check_hidden_rule_table()
    check_hidden_rule_live()

    # Freeing the main grid's filter tree (a `FilterListModel` that watches its
    # items, with a `CollectionFilter` and a property filter) crashes GTK. The
    # window never frees it, so leave without tearing the objects down.
    sys.stdout.flush()
    os._exit(0)
