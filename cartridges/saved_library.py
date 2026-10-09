# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright 2026 samuelm333

"""Keep the games from the last import on disk, so they can be shown without a scan."""

import asyncio
import contextlib
import json
import logging
from collections.abc import Iterable
from hashlib import sha256
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from gi.repository import Gio

from . import DATA_DIR, cover, hidden_games, play_history
from .games import PROPERTIES, Game

_PATH = DATA_DIR / "library.json"
_COVERS_DIR = DATA_DIR / "library-covers"

_VERSION = 1

# Number of covers written before letting the main loop run.
_BATCH_SIZE = 25

_logger = logging.getLogger(__name__)

_library: dict[str, list[Game]] | None = None

_dirty = False
_saving = False


def read() -> dict[str, list[Game]]:
    """Get the games from the last import, by the ID of their source.

    Return no games if the library is missing or damaged.
    """
    global _library  # noqa: PLW0603

    if _library is None:
        _library = _read_file()

    return _library


def forget_cover(game_id: str) -> None:
    """Delete the saved cover of the game with `game_id`, so it is saved again."""
    try:
        _cover_path(game_id).unlink(missing_ok=True)
    except OSError as e:
        _logger.warning("Could not delete saved cover of %s: %s", game_id, e)


def request_save() -> None:
    """Save the library soon. Several requests in a row cause one save."""
    global _dirty, _saving  # noqa: PLW0603

    _dirty = True
    if _saving or not (app := Gio.Application.get_default()):
        return

    _saving = True
    app.create_asyncio_task(_save_when_requested())


async def write(games: Iterable[Game]) -> None:
    """Save `games`, and their covers, as the library.

    Games the user removed and manually added games are not saved. Failing to
    write is logged and never raised.
    """
    global _library  # noqa: PLW0603

    saved = [g for g in games if not g.removed and g.source != "imported"]

    entries = [_entry(game) for game in saved]
    tmp = _PATH.with_suffix(".json.tmp")
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(
                {"version": _VERSION, "games": entries}, f, indent=4, sort_keys=True
            )

        tmp.replace(_PATH)
    except OSError as e:
        _logger.warning("Could not save library to %s: %s", _PATH, e)
        # Nothing more to do if this fails too, the failure is already logged
        with contextlib.suppress(OSError):
            tmp.unlink(missing_ok=True)
        return

    _library = {}
    for game in saved:
        _library.setdefault(game.source, []).append(game)

    await _write_covers(saved)


async def _write_covers(games: list[Game]) -> None:
    for number, game in enumerate(games, 1):
        if game.cover is not None and not (path := _cover_path(game.game_id)).exists():
            cover.save(game.cover, path)

        if not number % _BATCH_SIZE:
            await asyncio.sleep(0)

    keep = {_cover_path(game.game_id) for game in games if game.cover is not None}
    try:
        for path in _COVERS_DIR.glob("*.png"):
            if path not in keep:
                path.unlink(missing_ok=True)
    except OSError as e:
        _logger.warning("Could not clean up saved covers in %s: %s", _COVERS_DIR, e)


async def _save_when_requested() -> None:
    global _dirty, _saving  # noqa: PLW0603

    from cartridges import sources

    try:
        while _dirty:
            _dirty = False
            games = [
                game
                for source in sources.model
                if source.id != "imported"
                for game in (source.get_item(i) for i in range(source.get_n_items()))
                if game is not None
            ]
            await write(games)
    finally:
        _saving = False


def _cover_path(game_id: str) -> Path:
    return _COVERS_DIR / f"{sha256(game_id.encode()).hexdigest()}.png"


def _entry(game: Game) -> dict[str, Any]:  # JSON values of different types
    entry = {
        prop.name: getattr(game, prop.name)
        for prop in PROPERTIES
        if prop.name != "removed"
    }
    if game.cover is not None:
        entry["cover"] = _cover_path(game.game_id).name

    return entry


def _read_file() -> dict[str, list[Game]]:
    try:
        with _PATH.open(encoding="utf-8") as f:
            data: object = json.load(f)
    except (OSError, JSONDecodeError, UnicodeDecodeError):
        return {}

    if not isinstance(data, dict) or data.get("version") != _VERSION:  # pyright: ignore[reportUnknownMemberType]
        return {}

    entries: object = data.get("games")  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    if not isinstance(entries, list):
        return {}

    library: dict[str, list[Game]] = {}
    for entry in entries:  # pyright: ignore[reportUnknownVariableType]
        if (game := _read_game(entry)) is not None:  # pyright: ignore[reportUnknownArgumentType]
            library.setdefault(game.source, []).append(game)

    return library


def _read_game(entry: object) -> Game | None:
    if not isinstance(entry, dict):
        return None

    try:
        game = Game.from_data(entry)  # pyright: ignore[reportUnknownArgumentType]
    except TypeError:
        return None

    if (name := entry.get("cover")) and isinstance(name, str):  # pyright: ignore[reportUnknownMemberType]
        game.cover = cover.at_path(_COVERS_DIR / Path(name).name)

    if (hidden := hidden_games.load().get(game.game_id)) is not None:
        game.hidden = hidden

    game.last_played = max(game.last_played, play_history.load().get(game.game_id, 0))
    return game
