# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright 2023 Geoffrey Coulaud
# SPDX-FileCopyrightText: Copyright 2022-2026 kramo

import sqlite3
from collections.abc import Generator
from gettext import gettext as _
from pathlib import Path

from cartridges import SETTINGS, cover
from cartridges.games import Game

from . import DATA, FLATPAK, OPEN, location

ID, NAME = "lutris", _("Lutris")

_DATA_PATHS = (
    DATA / "lutris",
    FLATPAK / "net.lutris.Lutris" / "data" / "lutris",
)

_QUERY = """
    SELECT
        games.id,
        games.name,
        games.slug,
        games.runner,
        categories.name = ".hidden" as hidden
    FROM games
    LEFT JOIN games_categories ON games_categories.game_id = games.id
    FULL JOIN categories ON games_categories.category_id = categories.id
    WHERE
        games.name IS NOT NULL
        AND games.slug IS NOT NULL
        AND games.configPath IS NOT NULL
        AND games.installed;"""

# Runners whose games other sources usually import, and the keys to opt in
_OPTIONAL_RUNNERS = {
    "steam": "lutris-import-steam",
    "flatpak": "lutris-import-flatpak",
}


def get_games() -> Generator[Game]:
    """Installed Lutris games."""
    coverart = _data_dir() / "coverart"
    skipped = {
        runner
        for runner, key in _OPTIONAL_RUNNERS.items()
        if not SETTINGS.get_boolean(key)
    }
    with sqlite3.connect(_data_dir() / "pga.db") as conn:
        for row in conn.execute(_QUERY):
            if row[3] in skipped:
                continue

            yield Game(
                executable=f"{OPEN} lutris:rungameid/{row[0]}",
                game_id=f"{ID}_{row[3]}_{row[0]}",
                source=f"{ID}_{row[3]}",
                hidden=row[4],
                name=row[1],
                cover=cover.at_path(coverart / f"{row[2]}.jpg"),
            )


def _data_dir() -> Path:
    return location("lutris-location", _DATA_PATHS)
