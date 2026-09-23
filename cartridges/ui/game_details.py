# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright 2022-2026 kramo
# SPDX-FileCopyrightText: Copyright 2025 Jamie Gravendeel


import shutil
import sys
import uuid
from datetime import UTC, datetime
from gettext import gettext as _
from typing import TYPE_CHECKING, Any, cast
from urllib.parse import quote

if TYPE_CHECKING:
    from pathlib import Path

from gi.repository import Adw, Gdk, Gio, GLib, GObject, Gtk

from cartridges import SETTINGS
from cartridges.config import PREFIX
from cartridges.games import Game

from . import closures
from .collections import CollectionActions, CollectionsBox
from .cover import Cover  # noqa: F401
from .games import GameActions, GameEditable


@Gtk.Template(resource_path=f"{PREFIX}/game-details.ui")
@closures.add(closures.bool_, closures.format_, closures.if_)
class GameDetails(Adw.NavigationPage):
    """The details of a game."""

    __gtype_name__ = __qualname__

    collections_box: CollectionsBox = Gtk.Template.Child()
    name_entry: Adw.EntryRow = Gtk.Template.Child()

    game_actions: GameActions = Gtk.Template.Child()
    collection_actions: CollectionActions = Gtk.Template.Child()
    game_editable: GameEditable = Gtk.Template.Child()
    game_signals: GObject.SignalGroup = Gtk.Template.Child()

    game = GObject.Property(type=Game)
    editing = GObject.Property(type=bool, default=False)
    cover_paintable = GObject.Property(type=Gdk.Paintable)
    cover_delete_revealed = GObject.Property(type=bool, default=False)
    cover_loading = GObject.Property(type=bool, default=False)

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)

        group = Gio.SimpleActionGroup()
        group.add_action_entries((
            ("edit", lambda *_: self.edit()),
            ("cancel", lambda *_: self._cancel()),
            ("apply", lambda *_: self._apply()),
            ("choose-sgdb-cover", lambda *_: self._choose_cover()),
            ("choose-local-cover", lambda *_: self._choose_local_cover()),
            ("delete-cover", lambda *_: self._delete_cover()),
            (
                "search-on",
                lambda _action, param, *_: Gio.AppInfo.launch_default_for_uri(
                    param.get_string().format(quote(cast(Game, self.game).name))
                ),
                "s",
            ),
        ))
        self.insert_action_group("details", group)

        self.game_editable.bind_property(
            "valid",
            cast(Gio.SimpleAction, group.lookup_action("apply")),
            "enabled",
            GObject.BindingFlags.SYNC_CREATE,
        )

        self.insert_action_group("game", self.game_actions)
        self.insert_action_group("collection", self.collection_actions)

        for name in "hidden", "removed":
            self.game_signals.connect_closure(
                f"notify::{name}",
                lambda *_: self.activate_action("navigation.pop"),
                after=False,
            )

        self._staged_cover_action: str = "unchanged"
        self._staged_cover_temp_path: Path | None = None
        self._is_applying: bool = False

        self.name_entry.connect("notify::text", self._on_title_changed)
        self.connect("notify::game", self._on_game_changed)

    def _on_title_changed(self, *_args: Any) -> None:
        self.name_entry.remove_css_class("error")

    def _on_game_changed(self, *_args: Any) -> None:
        if self._is_applying:
            return
        self._reset_cover_staging()
        self._sync_cover_state()

    def _sync_cover_state(self) -> None:
        self.cover_paintable = self.game.cover if self.game else None
        self.cover_delete_revealed = bool(self.cover_paintable)

    def _reset_cover_staging(self) -> None:
        if self._staged_cover_temp_path and self._staged_cover_temp_path.exists():
            self._staged_cover_temp_path.unlink(missing_ok=True)
        self._staged_cover_temp_path = None
        self._staged_cover_action = "unchanged"
        self.cover_loading = False

    def add(self):
        """Add a new game."""
        self.game = None
        self.edit()

    def edit(self):
        """Enter edit mode."""
        self._reset_cover_staging()
        self._sync_cover_state()
        self.editing = True
        self.name_entry.grab_focus()

    def _apply(self):
        self._is_applying = True
        try:
            staged_action = self._staged_cover_action
            staged_path = self._staged_cover_temp_path

            self.game_editable.apply()
            self.game = self.game_editable.game

            if self.game:
                from cartridges import cover

                cover.COVERS_DIR.mkdir(parents=True, exist_ok=True)
                orig_backup = cover.COVERS_DIR / f"{self.game.game_id}.orig.tiff"
                curr_tiff = cover.COVERS_DIR / f"{self.game.game_id}.tiff"
                curr_gif = cover.COVERS_DIR / f"{self.game.game_id}.gif"

                if staged_action in ("set", "remove") and not orig_backup.exists():
                    if curr_tiff.exists():
                        shutil.copyfile(curr_tiff, orig_backup)
                    elif curr_gif.exists():
                        shutil.copyfile(curr_gif, orig_backup)

                if staged_action == "remove":
                    curr_tiff.unlink(missing_ok=True)
                    curr_gif.unlink(missing_ok=True)
                    self.game.cover = None
                elif staged_action == "set" and staged_path and staged_path.exists():
                    ext = staged_path.suffix or ".tiff"
                    dest_path = cover.COVERS_DIR / f"{self.game.game_id}{ext}"
                    curr_tiff.unlink(missing_ok=True)
                    curr_gif.unlink(missing_ok=True)
                    shutil.move(str(staged_path), str(dest_path))
                    self.game.cover = cover.at_path(dest_path)
                    self._staged_cover_temp_path = None
        finally:
            self._is_applying = False
            self._reset_cover_staging()
            self._sync_cover_state()
        self.editing = False

    @Gtk.Template.Callback()
    def _activate_apply(self, _entry):
        self.activate_action("details.apply")

    @Gtk.Template.Callback()
    def _cancel(self, *_args):
        self._reset_cover_staging()
        self._sync_cover_state()
        if not (self.editing and self.game):
            self.activate_action("navigation.pop")
        self.editing = False

    @Gtk.Template.Callback()
    def _delete_cover(self, *_args: Any) -> None:
        if self._staged_cover_temp_path and self._staged_cover_temp_path.exists():
            self._staged_cover_temp_path.unlink(missing_ok=True)
            self._staged_cover_temp_path = None
        self._staged_cover_action = "remove"
        self.cover_paintable = None
        self.cover_delete_revealed = False

    @Gtk.Template.Callback()
    def _choose_local_cover(self, *_args: Any) -> None:
        dialog = Gtk.FileDialog(title=_("Select Cover Image"))
        filters = Gio.ListStore.new(Gtk.FileFilter)
        image_filter = Gtk.FileFilter()
        image_filter.set_name(_("Image Files"))
        image_filter.add_mime_type("image/png")
        image_filter.add_mime_type("image/jpeg")
        image_filter.add_mime_type("image/tiff")
        image_filter.add_mime_type("image/webp")
        image_filter.add_mime_type("image/gif")
        filters.append(image_filter)
        dialog.set_filters(filters)

        def on_open(source: Gtk.FileDialog, res: Gio.AsyncResult) -> None:
            try:
                gfile = source.open_finish(res)
            except GLib.Error:
                return

            if not gfile:
                return

            path = gfile.get_path()
            if not path:
                return

            from cartridges import cover

            try:
                from PIL import Image, ImageSequence

                if (
                    self._staged_cover_temp_path
                    and self._staged_cover_temp_path.exists()
                ):
                    self._staged_cover_temp_path.unlink(missing_ok=True)

                cover.COVERS_DIR.mkdir(parents=True, exist_ok=True)
                ident = self.game.game_id if self.game else uuid.uuid4().hex[:8]
                with Image.open(path) as orig_img:
                    is_animated = getattr(orig_img, "is_animated", False)
                    if is_animated:
                        frames = [
                            f.resize((cover.WIDTH, cover.HEIGHT))
                            for f in ImageSequence.Iterator(orig_img)
                        ]
                        temp_dest = cover.COVERS_DIR / f"temp_{ident}.gif"
                        frames[0].save(
                            temp_dest, save_all=True, append_images=frames[1:]
                        )
                    else:
                        proc = orig_img
                        if proc.mode not in ("RGB", "RGBA"):
                            proc = proc.convert("RGBA")
                        temp_dest = cover.COVERS_DIR / f"temp_{ident}.tiff"
                        high_quality = SETTINGS.get_boolean("high-quality-images")
                        resized = proc.resize((cover.WIDTH, cover.HEIGHT))
                        resized.save(
                            temp_dest,
                            compression="tiff_adobe_deflate"
                            if high_quality
                            else "tiff_lzw",
                        )

                new_paintable = cover.at_path(temp_dest)
                if new_paintable:
                    self._staged_cover_temp_path = temp_dest
                    self._staged_cover_action = "set"
                    self.cover_paintable = new_paintable
                    self.cover_delete_revealed = True
            except (GLib.Error, OSError) as e:
                import logging

                logging.getLogger(__name__).warning(
                    "Failed to stage local cover: %s", e
                )

        root = self.get_root()
        parent_window = root if isinstance(root, Gtk.Window) else None
        dialog.open(parent_window, None, on_open)

    @Gtk.Template.Callback()
    def _choose_cover(self, *_args: Any) -> None:
        title = self.name_entry.get_text().strip()
        if not title:
            self.name_entry.add_css_class("error")
            self.name_entry.grab_focus()
            return

        key = SETTINGS.get_string("sgdb-key").strip()
        if not key:
            alert = Adw.AlertDialog(
                heading=_("SteamGridDB API Key Required"),
                body=_(
                    "To search and download cover art from SteamGridDB, "
                    "please enter a valid API key in Preferences.\n\n"
                    "You can generate an API key for free in your "
                    "SteamGridDB account preferences."
                ),
            )
            alert.add_response("cancel", _("Cancel"))
            alert.add_response("preferences", _("Preferences"))
            alert.set_response_appearance(
                "preferences", Adw.ResponseAppearance.SUGGESTED
            )

            def on_response(_dialog: Adw.AlertDialog, response: str) -> None:
                if response == "preferences":
                    app = Gio.Application.get_default()
                    if app is not None:
                        app.activate_action("preferences", None)

            alert.connect("response", on_response)
            alert.present(self)
            return

        from .cover_picker import CoverPicker

        def on_cover_selected(url: str) -> None:
            self._stage_sgdb_cover(url)

        picker = CoverPicker(
            game=self.game,
            game_name=title,
            on_cover_selected=on_cover_selected,
        )
        picker.present(self)

    def _stage_sgdb_cover(self, url: str) -> None:
        import threading
        from io import BytesIO
        from urllib.error import HTTPError, URLError
        from urllib.request import Request, urlopen

        from PIL import Image, ImageSequence

        from cartridges import cover

        self.cover_loading = True
        ident = self.game.game_id if self.game else uuid.uuid4().hex[:8]

        def stop_loading() -> bool:
            self.cover_loading = False
            return GLib.SOURCE_REMOVE

        def download_and_process():
            try:
                req = Request(url, headers={"User-Agent": "Cartridges/2.0"})
                with urlopen(req, timeout=15) as res:
                    content = res.read()
            except (HTTPError, URLError, TimeoutError):
                GLib.idle_add(stop_loading)
                return

            try:
                cover.COVERS_DIR.mkdir(parents=True, exist_ok=True)
                with Image.open(BytesIO(content)) as orig_img:
                    is_animated = getattr(orig_img, "is_animated", False)
                    if is_animated:
                        frames = [
                            frame.resize((cover.WIDTH, cover.HEIGHT))
                            for frame in ImageSequence.Iterator(orig_img)
                        ]
                        temp_dest = cover.COVERS_DIR / f"temp_{ident}.gif"
                        frames[0].save(
                            temp_dest, save_all=True, append_images=frames[1:]
                        )
                    else:
                        proc_img = orig_img
                        if proc_img.mode not in ("RGB", "RGBA"):
                            proc_img = proc_img.convert("RGBA")
                        temp_dest = cover.COVERS_DIR / f"temp_{ident}.tiff"
                        high_quality = SETTINGS.get_boolean("high-quality-images")
                        resized = proc_img.resize((cover.WIDTH, cover.HEIGHT))
                        resized.save(
                            temp_dest,
                            compression="tiff_adobe_deflate"
                            if high_quality
                            else "tiff_lzw",
                        )

                def apply_staging() -> bool:
                    self.cover_loading = False
                    if (
                        self._staged_cover_temp_path
                        and self._staged_cover_temp_path.exists()
                    ):
                        self._staged_cover_temp_path.unlink(missing_ok=True)

                    new_paintable = cover.at_path(temp_dest)
                    if new_paintable:
                        self._staged_cover_temp_path = temp_dest
                        self._staged_cover_action = "set"
                        self.cover_paintable = new_paintable
                        self.cover_delete_revealed = True
                    return GLib.SOURCE_REMOVE

                GLib.idle_add(apply_staging)
            except (OSError, ValueError) as err:
                import logging

                logging.getLogger(__name__).warning(
                    "Failed to stage SGDB cover: %s", err
                )
                GLib.idle_add(stop_loading)

        threading.Thread(target=download_and_process, daemon=True).start()

    @Gtk.Template.Callback()
    def _setup_collections(self, button: Gtk.MenuButton, *_args):
        if button.props.active:
            self.collections_box.build()
        else:
            self.collections_box.finish()

    @Gtk.Template.Callback()
    @staticmethod
    def _downscale(this: Gtk.Widget, cover: Gdk.Paintable | None) -> Gdk.Texture | None:
        if cover and (renderer := cast(Gtk.Native, this.props.root).get_renderer()):
            cover.snapshot(snapshot := Gtk.Snapshot(), 3, 3)
            if node := snapshot.to_node():
                return renderer.render_texture(node)

        return None

    @Gtk.Template.Callback()
    @staticmethod
    def _relative_date(_this, timestamp: int) -> str:
        date = datetime.fromtimestamp(timestamp, UTC)
        now = datetime.now(UTC)
        return (
            _("Never")
            if not timestamp
            else _("Today")
            if (n_days := (now - date).days) == 0
            else _("Yesterday")
            if n_days == 1
            else date.strftime("%A")
            if n_days <= (day_of_week := now.weekday())
            else _("Last Week")
            if n_days <= day_of_week + 7
            else _("This Month")
            if n_days <= (day_of_month := now.day)
            else _("Last Month")
            if n_days <= day_of_month + 30
            else date.strftime("%B")
            if n_days < (day_of_year := now.timetuple().tm_yday)
            else _("Last Year")
            if n_days <= day_of_year + 365
            else date.strftime("%Y")
        )

    @Gtk.Template.Callback()
    @staticmethod
    def _format_more_info(_this, label: str) -> str:
        executable = _("program")
        filename = _("file.txt")
        path = _("/path/to/{}")
        command = "xdg-open"

        if sys.platform.startswith("darwin"):
            command = "open"
        elif sys.platform.startswith("win32"):
            executable += ".exe"
            path = _(r"C:\path\to\{}")
            command = "start"

        return label.format(
            executable,
            path.format(executable),
            filename,
            command,
            path.format(filename),
        )
