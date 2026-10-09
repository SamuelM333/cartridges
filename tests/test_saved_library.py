# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright 2026 samuelm333

"""Test saving the launcher games from the last import, and reading them back."""

import asyncio
import importlib
import json
import os
import shutil
import sys
import tempfile
import types
from hashlib import sha256
from pathlib import Path
from typing import TYPE_CHECKING

import gi

gi.require_versions({"Gdk": "4.0", "Graphene": "1.0", "Gtk": "4.0"})
from gi.repository import Gdk, Graphene, Gtk
from PIL import Image

if TYPE_CHECKING:
    from cartridges.games import Game


class _Settings:
    """Stand-in for the application's `Gio.Settings`."""

    def get_boolean(self, _key: str) -> bool:
        return False


# Importing the real `cartridges` package needs the meson-generated `config.py`
# and compiled GSettings schemas, so stub the package with only what
# `games`, `cover` and `saved_library` use.
_DATA_DIR = Path(tempfile.mkdtemp())
_package = types.ModuleType("cartridges")
_package.__path__ = [str(Path(__file__).resolve().parents[1] / "cartridges")]
_package.DATA_DIR = _DATA_DIR  # pyright: ignore[reportAttributeAccessIssue]
_package.SETTINGS = _Settings()  # pyright: ignore[reportAttributeAccessIssue]
sys.modules["cartridges"] = _package

games = importlib.import_module("cartridges.games")
cover = importlib.import_module("cartridges.cover")
hidden_games = importlib.import_module("cartridges.hidden_games")
play_history = importlib.import_module("cartridges.play_history")
saved_library = importlib.import_module("cartridges.saved_library")

_LIBRARY = _DATA_DIR / "library.json"
_COVERS = _DATA_DIR / "library-covers"


def _reset(contents: str | bytes | None = None) -> None:
    """Start from an empty data directory and empty caches."""
    for path in (_LIBRARY, _COVERS):
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink(missing_ok=True)

    module_vars = vars(saved_library)
    module_vars["_PATH"], module_vars["_COVERS_DIR"] = _LIBRARY, _COVERS
    module_vars["_library"] = None
    vars(hidden_games)["_hidden"] = {}
    vars(play_history)["_history"] = {}

    if isinstance(contents, bytes):
        _LIBRARY.write_bytes(contents)
    elif contents is not None:
        _LIBRARY.write_text(contents, encoding="utf-8")


def _game(game_id: str, source: str = "steam", **props: object) -> "Game":
    game = games.Game(game_id=game_id, source=source, name=game_id, executable="true")
    for name, value in props.items():
        setattr(game, name, value)
    return game


def _write(*written: "Game") -> None:
    asyncio.run(saved_library.write(written))
    vars(saved_library)["_library"] = None


def _expect(actual: object, expected: object, what: str) -> None:
    if actual != expected:
        msg = f"Expected {what} to be {expected!r}, got {actual!r}"
        raise AssertionError(msg)


def _cover_file(game_id: str) -> Path:
    return _COVERS / f"{sha256(game_id.encode()).hexdigest()}.png"


def _png() -> Path:
    path = Path(tempfile.mkdtemp()) / "cover.png"
    Image.new("RGB", (20, 30), "red").save(path)
    return path


def _entry(**props: object) -> dict[str, object]:
    return {
        "game_id": "steam_1",
        "source": "steam",
        "name": "One",
        "executable": "true",
    } | props


def check_missing_file() -> None:
    """Validate that a missing library file reads as empty."""
    _reset()
    _expect(saved_library.read(), {}, "library")


def check_round_trip() -> None:
    """Validate that saved games read back grouped by source with their values."""
    _reset()
    _write(
        _game("steam_1", developer="Dev", added=100, last_played=200, hidden=True),
        _game("steam_2"),
        _game("heroic_1", source="heroic", executable="run heroic"),
    )

    library = saved_library.read()
    _expect(sorted(library), ["heroic", "steam"], "sources")
    _expect([g.game_id for g in library["steam"]], ["steam_1", "steam_2"], "steam")
    first = library["steam"][0]
    _expect(
        (first.name, first.developer, first.added, first.last_played, first.hidden),
        ("steam_1", "Dev", 100, 200, True),
        "saved values",
    )
    _expect(library["heroic"][0].executable, "run heroic", "heroic executable")


def check_removed_and_added_games_are_not_written() -> None:
    """Validate that removed and manually added games stay out of the library."""
    _reset()
    _write(
        _game("steam_1"),
        _game("steam_2", removed=True),
        _game("imported_0", source="imported"),
    )
    _expect(
        [g.game_id for g in saved_library.read()["steam"]], ["steam_1"], "saved games"
    )
    _expect("imported" in saved_library.read(), False, "manually added source")


def check_invalid_files() -> None:
    """Validate that damaged or unknown files read as empty without raising."""
    for contents in (
        "not json",
        b"\xff\xfe\x00",
        "[1, 2]",
        '"text"',
        json.dumps({"version": 2, "games": [_entry()]}),
        json.dumps({"games": [_entry()]}),
        json.dumps({"version": 1, "games": "no"}),
    ):
        _reset(contents)
        _expect(saved_library.read(), {}, f"library for {contents!r}")


def check_invalid_entries_are_skipped() -> None:
    """Validate that bad entries are skipped and the rest are kept."""
    entries = [
        _entry(),
        {"game_id": "steam_2", "source": "steam", "name": "No executable"},
        _entry(game_id="steam_3", added="yesterday"),
        "not an object",
        _entry(game_id="steam_4"),
    ]
    _reset(json.dumps({"version": 1, "games": entries}))
    _expect(
        [g.game_id for g in saved_library.read()["steam"]],
        ["steam_1", "steam_4"],
        "valid entries",
    )


def check_stored_choices_apply_on_read() -> None:
    """Validate that the user's hide choice and play history are applied."""
    _reset(
        json.dumps({
            "version": 1,
            "games": [
                _entry(hidden=True, last_played=100),
                _entry(game_id="steam_2", hidden=False, last_played=100),
            ],
        })
    )
    vars(hidden_games)["_hidden"] = {"steam_1": False, "steam_2": True}
    vars(play_history)["_history"] = {"steam_1": 500}

    first, second = saved_library.read()["steam"]
    _expect((first.hidden, first.last_played), (False, 500), "first game")
    _expect((second.hidden, second.last_played), (True, 100), "second game")


def check_cover_round_trip() -> None:
    """Validate that a cover is saved as an image and read back."""
    _reset()
    with_cover = _game("steam_1", cover=cover.at_path(_png()))
    _write(with_cover, _game("steam_2"))

    _expect(_cover_file("steam_1").is_file(), True, "cover file")
    first, second = saved_library.read()["steam"]
    _expect(first.cover is not None, True, "cover of the first game")
    _expect(second.cover, None, "cover of the second game")

    _cover_file("steam_1").unlink()
    vars(saved_library)["_library"] = None
    _expect(saved_library.read()["steam"][0].cover, None, "cover without its file")


def check_icon_cover_is_rendered() -> None:
    """Validate that a cover that is not an image file is drawn and saved."""
    _reset()
    path = _DATA_DIR / "icon.png"
    snapshot = Gtk.Snapshot()
    snapshot.append_color(Gdk.RGBA(red=1, alpha=1), Graphene.Rect().init(0, 0, 10, 10))
    icon = snapshot.to_paintable(Graphene.Size().init(10, 10))
    _expect(cover.save(icon, path), True, "save result")
    with Image.open(path) as im:
        _expect(im.size, (cover.WIDTH, cover.HEIGHT), "image size")


def check_cover_not_rewritten() -> None:
    """Validate that unchanged covers are not encoded again."""
    _reset()
    game = _game("steam_1", cover=cover.at_path(_png()))
    _write(game)
    path = _cover_file("steam_1")
    path.touch()
    marker = path.stat().st_mtime_ns - 10_000_000_000
    os.utime(path, ns=(marker, marker))

    _write(game)
    _expect(path.stat().st_mtime_ns, marker, "cover modification time")

    saved_library.forget_cover("steam_1")
    _expect(path.exists(), False, "forgotten cover file")
    _write(game)
    _expect(path.is_file(), True, "cover file after writing again")


def check_orphan_covers_are_pruned() -> None:
    """Validate that covers of games that are no longer saved are deleted."""
    _reset()
    _write(
        _game("steam_1", cover=cover.at_path(_png())),
        _game("steam_2", cover=cover.at_path(_png())),
    )
    _write(_game("steam_1", cover=cover.at_path(_png())))
    _expect(_cover_file("steam_1").is_file(), True, "kept cover")
    _expect(_cover_file("steam_2").exists(), False, "pruned cover")


def check_write_survives_failure() -> None:
    """Validate that a data directory that cannot be written does not raise."""
    _reset()
    blocker = _DATA_DIR / "blocker"
    blocker.write_text("", encoding="utf-8")
    module_vars = vars(saved_library)
    module_vars["_PATH"] = blocker / "library.json"
    module_vars["_COVERS_DIR"] = blocker / "library-covers"

    asyncio.run(saved_library.write([_game("steam_1", cover=cover.at_path(_png()))]))
    blocker.unlink()


if __name__ == "__main__":
    check_missing_file()
    check_round_trip()
    check_removed_and_added_games_are_not_written()
    check_invalid_files()
    check_invalid_entries_are_skipped()
    check_stored_choices_apply_on_read()
    check_cover_round_trip()
    check_icon_cover_is_rendered()
    check_cover_not_rewritten()
    check_orphan_covers_are_pruned()
    check_write_survives_failure()
