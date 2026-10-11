# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright 2026 samuelm333

"""Re-scan game sources on demand and merge the results into the library."""

import asyncio
import logging
import sqlite3
import time
from collections.abc import Iterable, Sequence
from typing import NamedTuple

from gi.repository import GObject

from cartridges import saved_library
from cartridges.games import Game

_logger = logging.getLogger(__name__)

# Number of games read from a source before letting the main loop run.
_BATCH_SIZE = 25


class ImportState(GObject.Object):
    """Whether an import is running."""

    __gtype_name__ = __qualname__

    running = GObject.Property(type=bool, default=False)


class Reconciliation(NamedTuple):
    """The result of merging a scan into the games already in a source."""

    kept: list[Game]
    added: list[Game]
    removed: list[Game]


state = ImportState()


def reconcile(
    existing: Sequence[Game],
    scanned: Iterable[Game],
    *,
    refresh_covers: bool = False,
) -> Reconciliation:
    """Merge `scanned` into `existing`, matching games by ID.

    Games found in both keep their existing object, so values the user changed
    are not overwritten. Only the last-played time and a missing cover are
    taken from the scan. With `refresh_covers`, the scanned cover replaces the
    existing one, for sources whose covers are cheap to make again.

    A game the user removed is not kept. The scanned game replaces it, so the
    game comes back as a new one.
    """
    new: dict[str, Game] = {}
    for game in scanned:
        new.setdefault(game.game_id, game)

    kept: list[Game] = []
    removed: list[Game] = []
    for game in existing:
        found = None if game.removed else new.pop(game.game_id, None)
        if found is None:
            removed.append(game)
            continue

        game.last_played = max(game.last_played, found.last_played)
        if found.cover is not None and (refresh_covers or game.cover is None):
            game.cover = found.cover
        kept.append(game)

    return Reconciliation(kept, list(new.values()), removed)


async def import_games() -> list[Game]:
    """Re-scan every source except manually added games.

    Return the games that were not in the library before.
    """
    from cartridges import sources

    state.running = True
    added = int(time.time())
    started = time.monotonic()
    new_games: list[Game] = []
    _logger.debug("Import started")

    try:
        for source in tuple(sources.model):
            if source.id == "imported":
                continue

            scanned: list[Game] = []
            try:
                for game in source.scan(added):
                    scanned.append(game)
                    if not len(scanned) % _BATCH_SIZE:
                        await asyncio.sleep(0)
            except FileNotFoundError:
                _logger.debug("Skipped %s: not found", source.id)
                continue
            except (OSError, sqlite3.Error):
                _logger.warning("Could not scan %s", source.id, exc_info=True)
                continue

            new = source.replace_games(scanned)
            _logger.debug("Scanned %s: %d new games", source.id, len(new))
            new_games.extend(new)
            await asyncio.sleep(0)

        saved_library.request_save()
    finally:
        state.running = False
        _logger.debug(
            "Import finished: %d new games in %.2f s",
            len(new_games),
            time.monotonic() - started,
        )

    return new_games
