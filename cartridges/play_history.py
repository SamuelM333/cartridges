# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright 2026 samuelm333

import contextlib
import json
import logging
from json import JSONDecodeError

from . import DATA_DIR

_PATH = DATA_DIR / "last-played.json"

_logger = logging.getLogger(__name__)

_history: dict[str, int] | None = None


def load() -> dict[str, int]:
    """Get the last-played timestamps recorded by Cartridges, keyed by game ID."""
    global _history  # noqa: PLW0603

    if _history is None:
        try:
            with _PATH.open(encoding="utf-8") as f:
                data: object = json.load(f)
        except (OSError, JSONDecodeError, UnicodeDecodeError):
            data = {}

        _history = (
            {
                key: value
                for key, value in data.items()  # pyright: ignore[reportUnknownVariableType]
                if isinstance(key, str)
                and isinstance(value, int)
                and not isinstance(value, bool)
                and value >= 0
            }
            if isinstance(data, dict)
            else {}
        )

    return _history


def record(game_id: str, timestamp: int):
    """Record that the game with `game_id` was launched at `timestamp`.

    The time is always kept in memory. Failing to save it to disk is logged and
    never raised, so it cannot prevent a game from launching.
    """
    history = load()
    history[game_id] = timestamp

    tmp = _PATH.with_suffix(".json.tmp")
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(history, f, indent=4, sort_keys=True)

        tmp.replace(_PATH)
    except OSError as e:
        _logger.warning("Could not save play history to %s: %s", _PATH, e)
        # Nothing more to do if this fails too, the failure is already logged
        with contextlib.suppress(OSError):
            tmp.unlink(missing_ok=True)
