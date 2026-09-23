# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright 2026 kramo

import asyncio
import urllib.error
import urllib.request
from collections.abc import Callable
from gettext import gettext as _
from typing import Any

from gi.repository import Adw, Gdk, Gio, GLib, Gtk

from cartridges import cover
from cartridges.config import PREFIX
from cartridges.games import Game
from cartridges.utils import steamgriddb


@Gtk.Template(resource_path=f"{PREFIX}/cover_picker.ui")
class CoverPicker(Adw.Dialog):
    """Dialog to choose a cover from SteamGridDB."""

    __gtype_name__ = "CoverPicker"

    flowbox: Gtk.FlowBox = Gtk.Template.Child()

    def __init__(
        self,
        game: Game | None = None,
        game_name: str = "",
        on_cover_selected: Callable[[str], None] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.game = game
        self.game_name = game_name or (game.name if game else "")
        self.on_cover_selected = on_cover_selected
        self._load_covers()

    def _load_covers(self) -> None:
        app = Gio.Application.get_default()
        if app is not None:
            app.create_asyncio_task(self._fetch_covers())

    async def _fetch_covers(self) -> None:
        try:
            sgdb_id = await asyncio.to_thread(steamgriddb.get_game_id, self.game_name)
            grids = await asyncio.to_thread(steamgriddb.get_grid_covers, sgdb_id)

            candidates: list[tuple[str, str, bool]] = []
            if grids:
                for item in grids[:10]:
                    full_url = str(item.get("url", ""))
                    thumb_url = str(item.get("thumb") or full_url)
                    is_animated = bool(item.get("animated", False))
                    if full_url:
                        candidates.append((full_url, thumb_url, is_animated))
            else:
                try:
                    anim_url = await asyncio.to_thread(
                        steamgriddb.get_image_url, sgdb_id, True
                    )
                    candidates.append((anim_url, anim_url, True))
                except steamgriddb.SgdbError:
                    pass
                try:
                    static_url = await asyncio.to_thread(
                        steamgriddb.get_image_url, sgdb_id, False
                    )
                    candidates.append((static_url, static_url, False))
                except steamgriddb.SgdbError:
                    pass

            for full_url, thumb_url, _is_animated in candidates:
                preview_data = await asyncio.to_thread(
                    self._download_preview, thumb_url
                )
                if preview_data:
                    GLib.idle_add(self._add_preview, full_url, preview_data)
        except steamgriddb.SgdbError:
            pass

    def _download_preview(self, url: str) -> bytes | None:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Cartridges/2.0"})
            with urllib.request.urlopen(req, timeout=5) as res:
                return bytes(res.read())
        except (urllib.error.URLError, TimeoutError, OSError):
            return None

    def _add_preview(self, url: str, data: bytes) -> None:
        try:
            btn = Gtk.Button()
            btn.add_css_class("card")
            btn.add_css_class("cover-picker-button")
            btn.set_tooltip_text(_("Select this cover"))

            texture = Gdk.Texture.new_from_bytes(GLib.Bytes.new(data))

            picture = Gtk.Picture.new_for_paintable(texture)
            picture.set_size_request(140, 210)
            picture.set_content_fit(Gtk.ContentFit.CONTAIN)

            btn.set_child(picture)
            btn.connect("clicked", self._on_preview_clicked, url)
            self.flowbox.append(btn)
        except (GLib.Error, TypeError):
            pass

    def _on_preview_clicked(self, _btn: Gtk.Button, url: str) -> None:
        if self.on_cover_selected is not None:
            self.on_cover_selected(url)
            self.close()
            return
        app = Gio.Application.get_default()
        if app is not None:
            app.create_asyncio_task(self._apply_cover(url))

    async def _apply_cover(self, url: str) -> None:
        if self.game is None:
            GLib.idle_add(self.close)
            return
        success = await asyncio.to_thread(
            steamgriddb.save_cover_from_url, self.game.game_id, url
        )
        if success:
            base = cover.COVERS_DIR / self.game.game_id
            new_cover = cover.at_path(f"{base}.gif") or cover.at_path(f"{base}.tiff")
            if new_cover:
                GLib.idle_add(setattr, self.game, "cover", new_cover)
        GLib.idle_add(self.close)
