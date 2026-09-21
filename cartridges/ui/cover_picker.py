# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright 2026 kramo

import asyncio
import urllib.request
from typing import Any

from gi.repository import Adw, Gio, GLib, GObject, Gtk

from cartridges import cover
from cartridges.config import PREFIX
from cartridges.games import Game
from cartridges.utils import steamgriddb


@Gtk.Template(resource_path=f"{PREFIX}/cover_picker.ui")
class CoverPicker(Adw.Dialog):
    """Dialog to choose a cover from SteamGridDB."""

    __gtype_name__ = "CoverPicker"

    flowbox: Gtk.FlowBox = Gtk.Template.Child()

    def __init__(self, game: Game, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.game = game
        self._load_covers()

    def _load_covers(self) -> None:
        app = Gio.Application.get_default()
        if app is not None:
            app.create_asyncio_task(self._fetch_covers())

    async def _fetch_covers(self) -> None:
        try:
            sgdb_id = await asyncio.to_thread(steamgriddb.get_game_id, self.game.name)
            urls = []
            try:
                animated_url = await asyncio.to_thread(
                    steamgriddb.get_image_url, sgdb_id, True
                )
                urls.append((animated_url, True))
            except Exception:
                pass
            try:
                static_url = await asyncio.to_thread(
                    steamgriddb.get_image_url, sgdb_id, False
                )
                urls.append((static_url, False))
            except Exception:
                pass

            for url, is_animated in urls:
                preview_data = await asyncio.to_thread(self._download_preview, url)
                if preview_data:
                    GLib.idle_add(self._add_preview, url, preview_data, is_animated)
        except Exception:
            pass

    def _download_preview(self, url: str) -> bytes | None:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Cartridges/2.0"})
            with urllib.request.urlopen(req, timeout=5) as res:
                return bytes(res.read())
        except Exception:
            return None

    def _add_preview(self, url: str, data: bytes, is_animated: bool) -> None:
        try:
            btn = Gtk.Button()
            btn.set_label(_("Use Animated") if is_animated else _("Use Static"))
            btn.connect("clicked", self._on_preview_clicked, url)
            self.flowbox.append(btn)
        except Exception:
            pass

    def _on_preview_clicked(self, _btn: Gtk.Button, url: str) -> None:
        app = Gio.Application.get_default()
        if app is not None:
            app.create_asyncio_task(self._apply_cover(url))

    async def _apply_cover(self, url: str) -> None:
        success = await asyncio.to_thread(
            steamgriddb.save_cover_from_url, self.game.game_id, url
        )
        if success:
            base = cover.COVERS_DIR / self.game.game_id
            new_cover = cover.at_path(f"{base}.gif") or cover.at_path(f"{base}.tiff")
            if new_cover:
                GLib.idle_add(setattr, self.game, "cover", new_cover)
        GLib.idle_add(self.close)

