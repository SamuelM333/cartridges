# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright 2025-2026 kramo

import itertools
import json
import re
import time
from collections.abc import Generator, Iterable
from gettext import gettext as _
from json import JSONDecodeError
from pathlib import Path

from cartridges import cover
from cartridges.cover import COVERS_DIR
from cartridges.games import GAMES_DIR, Game

ID, NAME = "imported", _("Added")


def get_games() -> Generator[Game]:
    """Manually added games."""
    for path in get_paths():
        try:
            with path.open(encoding="utf-8") as f:
                data = json.load(f)
        except (JSONDecodeError, UnicodeDecodeError):
            continue

        try:
            game = Game.from_data(data)
        except TypeError:
            continue

        base = COVERS_DIR / game.game_id
        game.cover = cover.at_path(f"{base}.gif") or cover.at_path(f"{base}.tiff")
        yield game


def new(taken: Iterable[str] = ()) -> Game:
    """Create a new game for the user to manually set its properties.

    `taken` are the IDs of games that are in the library but may not be on disk yet.
    """
    used = (
        _number(ident)
        for ident in itertools.chain((p.stem for p in get_paths()), taken)
    )
    number = _next_number(n for n in used if n is not None)
    return Game(game_id=f"{ID}_{number}", source=ID, added=int(time.time()))


def _number(ident: str) -> int | None:
    """Get the number in a manually added game's ID, or `None` if it has none."""
    match = re.fullmatch(rf"{ID}_(\d+)", ident)
    return int(match[1]) if match else None


def _next_number(used: Iterable[int]) -> int:
    """Get the lowest number that is not in `used`."""
    numbers = set(used)
    return next(i for i in itertools.count() if i not in numbers)


def get_paths() -> Generator[Path]:
    """Get the paths of all imported games on disk."""
    yield from GAMES_DIR.glob("imported_*.json")
