# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright 2025 Zoey Ahmed
# SPDX-FileCopyrightText: Copyright 2025-2026 kramo

from gettext import gettext as _
from typing import override

from gi.repository import Adw

from . import collections, sources
from .config import APP_ID, PREFIX
from .ui import PRIMARY_KEY
from .ui.window import Window


class Application(Adw.Application):
    """The main application."""

    __gtype_name__ = __qualname__

    @override
    def do_startup(self):
        Adw.Application.do_startup(self)
        self.props.style_manager.props.color_scheme = Adw.ColorScheme.PREFER_DARK

        self.add_action_entries((
            ("preferences", lambda *_: self._present_preferences_dialog()),
            ("about", lambda *_: self._present_about_dialog()),
            ("quit", lambda *_: self.quit()),
        ))
        self.set_accels_for_action("app.preferences", (f"{PRIMARY_KEY}comma",))
        self.set_accels_for_action("app.quit", (f"{PRIMARY_KEY}q",))

        sources.load()
        collections.load()
        self._check_auto_fetch_sgdb_covers()

    @override
    def do_activate(self):
        window = self.props.active_window or Window(application=self)
        window.present()

    def _present_about_dialog(self):
        about = Adw.AboutDialog(appdata_resource_path=f"{PREFIX}/{APP_ID}.metainfo.xml")
        about.props.developers = ["kramo", "samuelm333"]
        # Translators: Replace "translator-credits" with your name/username,
        # and optionally a URL or an email in <user@example.org> format.
        about.props.translator_credits = _("translator-credits")
        about.present(self.props.active_window)

    def _present_preferences_dialog(self):
        from .ui.preferences import CartridgesPreferences

        CartridgesPreferences().present(self.props.active_window)

    def _check_auto_fetch_sgdb_covers(self) -> None:
        from . import SETTINGS

        if not SETTINGS.get_boolean("sgdb"):
            return
        key = SETTINGS.get_string("sgdb-key").strip()
        if not key:
            return

        self.create_asyncio_task(self._auto_fetch_sgdb_covers())

    async def _auto_fetch_sgdb_covers(self) -> None:
        import asyncio

        from gi.repository import GLib

        from . import SETTINGS, cover
        from .utils import steamgriddb

        prefer_sgdb = SETTINGS.get_boolean("sgdb-prefer")
        animated = SETTINGS.get_boolean("sgdb-animated")

        for source in sources.model:
            for i in range(source.get_n_items()):
                game = source.get_item(i)
                if game is None:
                    continue
                if not prefer_sgdb and game.cover is not None:
                    continue

                try:
                    sgdb_id = await asyncio.to_thread(
                        steamgriddb.get_game_id, game.name
                    )
                    url = await asyncio.to_thread(
                        steamgriddb.get_image_url, sgdb_id, animated
                    )
                    success = await asyncio.to_thread(
                        steamgriddb.save_cover_from_url, game.game_id, url
                    )
                    if success:
                        base = cover.COVERS_DIR / game.game_id
                        new_cover = cover.at_path(f"{base}.gif") or cover.at_path(
                            f"{base}.tiff"
                        )
                        if new_cover:
                            GLib.idle_add(setattr, game, "cover", new_cover)
                except steamgriddb.SgdbAuthError:
                    return
                except (steamgriddb.SgdbError, OSError, TimeoutError):
                    continue
