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

    stack: Gtk.Stack = Gtk.Template.Child()
    search_entry: Gtk.SearchEntry = Gtk.Template.Child()
    initial_spinner: Adw.Spinner = Gtk.Template.Child()
    status_page: Adw.StatusPage = Gtk.Template.Child()
    flowbox: Gtk.FlowBox = Gtk.Template.Child()
    bottom_spinner: Adw.Spinner = Gtk.Template.Child()

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
        self._search_generation: int = 0
        self._fetch_task: asyncio.Task[None] | None = None
        self._last_searched_query: str = self.game_name
        self.search_entry.set_text(self.game_name)
        self.connect("closed", lambda *_: self._cancel_in_flight())
        self._load_covers()

    def _cancel_in_flight(self) -> None:
        if self._fetch_task is not None and not self._fetch_task.done():
            self._fetch_task.cancel()
            self._fetch_task = None

    @Gtk.Template.Callback()
    def _on_search_activated(self, entry: Gtk.SearchEntry) -> None:
        query = entry.get_text().strip()
        if not query:
            return
        if (
            query == self._last_searched_query
            and self.stack.get_visible_child_name() == "results"
        ):
            return
        self.game_name = query
        self._last_searched_query = query
        self._load_covers()

    @Gtk.Template.Callback()
    def _on_search_changed(self, _entry: Gtk.SearchEntry) -> None:
        pass

    def _load_covers(self) -> None:
        self._search_generation += 1
        generation = self._search_generation
        self._cancel_in_flight()
        self.flowbox.remove_all()
        self.stack.set_visible_child_name("loading")
        self.bottom_spinner.set_visible(False)
        app = Gio.Application.get_default()
        if app is not None:
            self._fetch_task = app.create_asyncio_task(
                self._fetch_covers(generation, self.game_name)
            )

    async def _fetch_covers(self, generation: int, query: str) -> None:
        if not query:
            GLib.idle_add(self._show_empty, generation)
            return
        try:
            sgdb_id = await asyncio.to_thread(steamgriddb.get_game_id, query)
            if generation != self._search_generation:
                return
            grids = await asyncio.to_thread(steamgriddb.get_grid_covers, sgdb_id)
            if generation != self._search_generation:
                return

            candidates: list[tuple[str, str, bool]] = []
            if grids:
                for item in grids[:20]:
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
                    if generation != self._search_generation:
                        return
                    candidates.append((anim_url, anim_url, True))
                except steamgriddb.SgdbError:
                    pass
                try:
                    static_url = await asyncio.to_thread(
                        steamgriddb.get_image_url, sgdb_id, False
                    )
                    if generation != self._search_generation:
                        return
                    candidates.append((static_url, static_url, False))
                except steamgriddb.SgdbError:
                    pass

            if generation != self._search_generation:
                return

            if not candidates:
                GLib.idle_add(self._show_empty, generation)
                return

            # Batch 1: first 6 items loaded while initial spinner is active
            batch_size = 6
            first_batch = candidates[:batch_size]
            remaining_batches = candidates[batch_size:]

            first_previews: list[tuple[str, bytes]] = []
            for full_url, thumb_url, _is_animated in first_batch:
                preview_data = await asyncio.to_thread(
                    self._get_or_download_preview, thumb_url
                )
                if generation != self._search_generation:
                    return
                if preview_data:
                    first_previews.append((full_url, preview_data))

            if generation != self._search_generation:
                return

            if not first_previews and not remaining_batches:
                GLib.idle_add(self._show_empty, generation)
                return

            GLib.idle_add(
                self._render_initial_batch,
                generation,
                first_previews,
                bool(remaining_batches),
            )

            # Subsequent batches progressively loaded with bottom spinner
            if remaining_batches:
                for full_url, thumb_url, _is_animated in remaining_batches:
                    preview_data = await asyncio.to_thread(
                        self._get_or_download_preview, thumb_url
                    )
                    if generation != self._search_generation:
                        return
                    if preview_data:
                        GLib.idle_add(
                            self._add_preview, generation, full_url, preview_data
                        )
                GLib.idle_add(self._hide_bottom_spinner, generation)
        except asyncio.CancelledError:
            return
        except (steamgriddb.SgdbError, urllib.error.URLError, TimeoutError, OSError):
            if generation == self._search_generation:
                GLib.idle_add(self._show_empty, generation)

    def _get_or_download_preview(self, url: str) -> bytes | None:
        cached = steamgriddb.get_cached_preview(url)
        if cached is not None:
            return cached

        data = self._download_preview(url)
        if data is not None:
            steamgriddb.save_cached_preview(url, data)
        return data

    def _download_preview(self, url: str) -> bytes | None:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Cartridges/2.0"})
            with urllib.request.urlopen(req, timeout=5) as res:
                return bytes(res.read())
        except (urllib.error.URLError, TimeoutError, OSError):
            return None

    def _show_empty(self, generation: int) -> None:
        if generation != self._search_generation:
            return
        self.stack.set_visible_child_name("empty")
        self.bottom_spinner.set_visible(False)

    def _hide_bottom_spinner(self, generation: int) -> None:
        if generation == self._search_generation:
            self.bottom_spinner.set_visible(False)

    def _render_initial_batch(
        self, generation: int, previews: list[tuple[str, bytes]], has_more: bool
    ) -> None:
        if generation != self._search_generation:
            return
        for full_url, data in previews:
            self._add_preview(generation, full_url, data)
        self.stack.set_visible_child_name("results")
        self.bottom_spinner.set_visible(has_more)

    def _add_preview(self, generation: int, url: str, data: bytes) -> None:
        if generation != self._search_generation:
            return
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
