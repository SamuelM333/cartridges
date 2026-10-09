# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright 2026 samuelm333

import contextlib
import json
import logging
from json import JSONDecodeError

from . import DATA_DIR

_PATH = DATA_DIR / "hidden.json"

_logger = logging.getLogger(__name__)

_hidden: dict[str, bool] | None = None


def load() -> dict[str, bool]:
    """Get whether the user last hid (`True`) or unhid (`False`) a game, by game ID.

    Games the user never hid or unhid are not included.
    """
    global _hidden  # noqa: PLW0603

    if _hidden is None:
        try:
            with _PATH.open(encoding="utf-8") as f:
                data: object = json.load(f)
        except (OSError, JSONDecodeError, UnicodeDecodeError):
            data = {}

        _hidden = (
            {
                key: value
                for key, value in data.items()  # pyright: ignore[reportUnknownVariableType]
                if isinstance(key, str) and isinstance(value, bool)
            }
            if isinstance(data, dict)
            else {}
        )

    return _hidden


def record(game_id: str, hidden: bool):
    """Record that the user hid (`True`) or unhid (`False`) the game with `game_id`.

    The choice is always kept in memory. Failing to save it to disk is logged and
    never raised, so it cannot prevent a game from being hidden.
    """
    state = load()
    state[game_id] = hidden

    tmp = _PATH.with_suffix(".json.tmp")
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(state, f, indent=4, sort_keys=True)

        tmp.replace(_PATH)
    except OSError as e:
        _logger.warning("Could not save hidden games to %s: %s", _PATH, e)
        # Nothing more to do if this fails too, the failure is already logged
        with contextlib.suppress(OSError):
            tmp.unlink(missing_ok=True)
