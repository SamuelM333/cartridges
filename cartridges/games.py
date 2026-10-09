# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright 2025 Zoey Ahmed
# SPDX-FileCopyrightText: Copyright 2025-2026 kramo
# SPDX-FileCopyrightText: Copyright 2025 Jamie Gravendeel

import json
import logging
import os
import subprocess
import time
from pathlib import Path
from shlex import quote
from types import UnionType
from typing import Any, NamedTuple, Self

from gi.repository import Gdk, Gio, GObject

from . import DATA_DIR, SETTINGS, play_history

GAMES_DIR = DATA_DIR / "games"

_logger = logging.getLogger(__name__)


class _GameProp(NamedTuple):
    name: str
    type_: type | UnionType
    required: bool = False
    editable: bool = False


PROPERTIES: tuple[_GameProp, ...] = (
    _GameProp("added", int),
    _GameProp("executable", str | list[str], required=True, editable=True),
    _GameProp("game_id", str, required=True),
    _GameProp("source", str, required=True),
    _GameProp("hidden", bool),
    _GameProp("last_played", int),
    _GameProp("name", str, required=True, editable=True),
    _GameProp("developer", str, editable=True),
    _GameProp("removed", bool),
    _GameProp("blacklisted", bool),
    _GameProp("version", float),
)

_SPEC_VERSION = 2.0


class Game(Gio.SimpleActionGroup):
    """Game data class."""

    __gtype_name__ = __qualname__

    added = GObject.Property(type=int)
    executable = GObject.Property(type=str)
    game_id = GObject.Property(type=str)
    source = GObject.Property(type=str)
    hidden = GObject.Property(type=bool, default=False)
    last_played = GObject.Property(type=int)
    name = GObject.Property(type=str)
    developer = GObject.Property(type=str)
    removed = GObject.Property(type=bool, default=False)
    blacklisted = GObject.Property(type=bool, default=False)
    version = GObject.Property(type=float, default=_SPEC_VERSION)

    cover = GObject.Property(type=Gdk.Paintable)

    @classmethod
    def from_data(cls, data: dict[str, Any]) -> Self:
        """Create a game from data. Useful for loading from JSON."""
        game = cls()

        for prop in PROPERTIES:
            value = data.get(prop.name)

            if not prop.required and value is None:
                continue

            if not isinstance(value, prop.type_):
                raise TypeError

            match prop.name:
                case "executable" if isinstance(value, list):
                    value = " ".join(value)
                case "version" if value and value > _SPEC_VERSION:
                    raise TypeError
                case "version":
                    continue

            setattr(game, prop.name, value)

        return game

    def play(self):
        """Record the launch time and run the executable command in a shell.

        Recording is best effort and cannot prevent the launch.
        """
        self.last_played = int(time.time())
        play_history.record(self.game_id, self.last_played)

        subprocess.Popen(  # noqa: S602
            format_executable(self.executable),
            cwd=Path.home(),
            shell=True,
            start_new_session=True,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
        )

        if SETTINGS.get_boolean("exit-after-launch"):
            app = Gio.Application.get_default()
            if app:
                app.quit()

    def save(self) -> None:
        """Save the game's properties to disk.

        The file is replaced in one step, so a failure never leaves a damaged or
        partial game file behind.

        Raises `OSError` if the game could not be saved.
        """
        properties = {prop.name: getattr(self, prop.name) for prop in PROPERTIES}

        path = Path(f"{GAMES_DIR / self.game_id}.json")
        tmp = path.with_suffix(".json.tmp")
        try:
            GAMES_DIR.mkdir(parents=True, exist_ok=True)
            with tmp.open("w", encoding="utf-8") as f:
                json.dump(properties, f, indent=4, sort_keys=True)

            tmp.replace(path)
        except OSError:
            try:
                tmp.unlink(missing_ok=True)
            except OSError:
                _logger.debug("Could not remove %s", tmp, exc_info=True)
            raise


def format_executable(executable: str) -> str:
    """Get the correct executable for the user's environment."""
    return (
        f"flatpak-spawn --host /bin/sh -c {quote(executable)}"
        if Path("/.flatpak-info").exists()
        else executable
    )
