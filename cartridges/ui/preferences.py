# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright 2025 Zoey Ahmed
# SPDX-FileCopyrightText: Copyright 2022-2026 kramo

import os
import re
import sys
from collections.abc import Generator
from gettext import gettext as _
from pathlib import Path
from typing import Any

from gi.repository import Adw, Gio, GLib, Gtk

from cartridges import SETTINGS, STATE_SETTINGS
from cartridges.config import PREFIX, PROFILE


# Validation rules mapping: schema_key -> (list of (subpath, is_directory), error_subtitle)
_LOCATION_VALIDATION = {
    "steam-location": (
        [
            ("steamapps/libraryfolders.vdf", False),
            ("appcache/librarycache", True),
        ],
        _("Select the Steam data directory."),
    ),
    "lutris-location": (
        [
            ("pga.db", False),
        ],
        _("Select the Lutris data directory."),
    ),
    "heroic-location": (
        [
            ("config.json", False),
            ("store/config.json", False),
        ],
        _("Select the Heroic configuration directory."),
    ),
    "itch-location": (
        [
            ("db/butler.db", False),
        ],
        _("Select the itch configuration directory."),
    ),
    "legendary-location": (
        [
            ("installed.json", False),
            ("metadata", True),
        ],
        _("Select the Legendary configuration directory."),
    ),
    "flatpak-system-location": (
        [
            ("exports/share/applications", True),
            ("exports/share/icons", True),
        ],
        _("Select the Flatpak data directory."),
    ),
    "flatpak-user-location": (
        [
            ("exports/share/applications", True),
            ("exports/share/icons", True),
        ],
        _("Select the Flatpak data directory."),
    ),
}


@Gtk.Template(resource_path=f"{PREFIX}/preferences.ui")
class CartridgesPreferences(Adw.PreferencesDialog):
    """Controller for the Preferences dialog."""

    __gtype_name__ = "CartridgesPreferences"

    # Behavior & Images
    exit_after_launch_switch: Adw.SwitchRow = Gtk.Template.Child()
    cover_launches_game_switch: Adw.SwitchRow = Gtk.Template.Child()
    high_quality_images_switch: Adw.SwitchRow = Gtk.Template.Child()

    # Import Behavior
    auto_import_switch: Adw.SwitchRow = Gtk.Template.Child()
    remove_missing_switch: Adw.SwitchRow = Gtk.Template.Child()

    # Steam
    steam_expander_row: Adw.ExpanderRow = Gtk.Template.Child()
    steam_data_action_row: Adw.ActionRow = Gtk.Template.Child()
    steam_data_file_chooser_button: Gtk.Button = Gtk.Template.Child()

    # Lutris
    lutris_expander_row: Adw.ExpanderRow = Gtk.Template.Child()
    lutris_data_action_row: Adw.ActionRow = Gtk.Template.Child()
    lutris_data_file_chooser_button: Gtk.Button = Gtk.Template.Child()
    lutris_import_steam_switch: Adw.SwitchRow = Gtk.Template.Child()
    lutris_import_flatpak_switch: Adw.SwitchRow = Gtk.Template.Child()

    # Heroic
    heroic_expander_row: Adw.ExpanderRow = Gtk.Template.Child()
    heroic_config_action_row: Adw.ActionRow = Gtk.Template.Child()
    heroic_config_file_chooser_button: Gtk.Button = Gtk.Template.Child()
    heroic_import_epic_switch: Adw.SwitchRow = Gtk.Template.Child()
    heroic_import_gog_switch: Adw.SwitchRow = Gtk.Template.Child()
    heroic_import_amazon_switch: Adw.SwitchRow = Gtk.Template.Child()
    heroic_import_sideload_switch: Adw.SwitchRow = Gtk.Template.Child()

    # Itch
    itch_expander_row: Adw.ExpanderRow = Gtk.Template.Child()
    itch_config_action_row: Adw.ActionRow = Gtk.Template.Child()
    itch_config_file_chooser_button: Gtk.Button = Gtk.Template.Child()

    # Legendary
    legendary_expander_row: Adw.ExpanderRow = Gtk.Template.Child()
    legendary_config_action_row: Adw.ActionRow = Gtk.Template.Child()
    legendary_config_file_chooser_button: Gtk.Button = Gtk.Template.Child()

    # Flatpak
    flatpak_expander_row: Adw.ExpanderRow = Gtk.Template.Child()
    flatpak_system_data_action_row: Adw.ActionRow = Gtk.Template.Child()
    flatpak_system_data_file_chooser_button: Gtk.Button = Gtk.Template.Child()
    flatpak_user_data_action_row: Adw.ActionRow = Gtk.Template.Child()
    flatpak_user_data_file_chooser_button: Gtk.Button = Gtk.Template.Child()
    flatpak_import_launchers_switch: Adw.SwitchRow = Gtk.Template.Child()

    # Desktop
    desktop_switch: Adw.SwitchRow = Gtk.Template.Child()

    # SteamGridDB
    sgdb_key_entry_row: Adw.EntryRow = Gtk.Template.Child()
    sgdb_switch: Adw.SwitchRow = Gtk.Template.Child()
    sgdb_prefer_switch: Adw.SwitchRow = Gtk.Template.Child()
    sgdb_animated_switch: Adw.SwitchRow = Gtk.Template.Child()
    sgdb_fetch_button: Gtk.Button = Gtk.Template.Child()
    sgdb_stack: Gtk.Stack = Gtk.Template.Child()
    sgdb_spinner: Adw.Spinner = Gtk.Template.Child()

    # Danger Zone
    remove_all_games_button_row: Adw.ButtonRow = Gtk.Template.Child()
    reset_button_row: Adw.ButtonRow = Gtk.Template.Child()

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        self.file_chooser = Gtk.FileDialog()
        self._removed_games: list[Any] = []

        self._bind_switches()
        self._setup_sgdb_key()
        self._init_source_rows()

        if PROFILE == "development":
            self.reset_button_row.set_visible(True)

        if not sys.platform.startswith("linux"):
            self.desktop_switch.set_visible(False)

    def _bind_switches(self) -> None:
        """Bind GSettings keys to corresponding switch widgets."""
        switches = {
            "exit-after-launch",
            "cover-launches-game",
            "high-quality-images",
            "auto-import",
            "remove-missing",
            "steam",
            "lutris",
            "lutris-import-steam",
            "lutris-import-flatpak",
            "heroic",
            "heroic-import-epic",
            "heroic-import-gog",
            "heroic-import-amazon",
            "heroic-import-sideload",
            "itch",
            "legendary",
            "flatpak",
            "flatpak-import-launchers",
            "desktop",
            "sgdb",
            "sgdb-prefer",
            "sgdb-animated",
        }
        for key in switches:
            switch = getattr(self, f'{key.replace("-", "_")}_switch', None)
            if switch is not None:
                SETTINGS.bind(
                    key,
                    switch,
                    "active",
                    Gio.SettingsBindFlags.DEFAULT,
                )

    def _setup_sgdb_key(self) -> None:
        """Bind SteamGridDB API key entry row and lock/unlock switch."""
        self.sgdb_key_entry_row.set_text(SETTINGS.get_string("sgdb-key"))

        def on_key_changed(*_: Any) -> None:
            key = self.sgdb_key_entry_row.get_text()
            SETTINGS.set_string("sgdb-key", key)
            self._update_sgdb_sensitivity(key)

        self.sgdb_key_entry_row.connect("changed", on_key_changed)
        self._update_sgdb_sensitivity(SETTINGS.get_string("sgdb-key"))

    def _update_sgdb_sensitivity(self, key: str) -> None:
        """Enable or disable SteamGridDB controls based on API key presence."""
        has_key = bool(key.strip())
        if not has_key:
            SETTINGS.set_boolean("sgdb", False)
        self.sgdb_switch.set_sensitive(has_key)

    def _init_source_rows(self) -> None:
        """Initialize expander rows binding and button mappings."""
        # Source ID to GSettings enable key mapping
        self._sources = {
            "steam": "steam",
            "lutris": "lutris",
            "heroic": "heroic",
            "itch": "itch",
            "legendary": "legendary",
            "flatpak": "flatpak",
        }

        # Bind expansion to activation
        for source_id in self._sources:
            expander = getattr(self, f"{source_id}_expander_row", None)
            if expander is not None:
                SETTINGS.bind(
                    source_id,
                    expander,
                    "enable-expansion",
                    Gio.SettingsBindFlags.DEFAULT,
                )

        # Connect chooser button signals
        self._button_mappings = {
            "steam_data_file_chooser_button": "steam-location",
            "lutris_data_file_chooser_button": "lutris-location",
            "heroic_config_file_chooser_button": "heroic-location",
            "itch_config_file_chooser_button": "itch-location",
            "legendary_config_file_chooser_button": "legendary-location",
            "flatpak_system_data_file_chooser_button": "flatpak-system-location",
            "flatpak_user_data_file_chooser_button": "flatpak-user-location",
        }

        for btn_name, schema_key in self._button_mappings.items():
            btn = getattr(self, btn_name, None)
            if btn is not None:
                btn.connect("clicked", self._on_chooser_clicked, schema_key)

        self._warning_widgets: dict[str, Gtk.Widget] = {}
        self._update_subtitles()
        self._update_warnings()

    def _on_chooser_clicked(self, _btn: Gtk.Button, schema_key: str) -> None:
        """Open folder dialog to select a folder."""
        self.file_chooser.select_folder(self, None, self._on_folder_selected, schema_key)

    def _on_folder_selected(self, file_dialog: Gtk.FileDialog, result: Gio.AsyncResult, schema_key: str) -> None:
        """Process result when a folder is picked."""
        try:
            gfile = file_dialog.select_folder_finish(result)
            if not gfile:
                return
            path = Path(gfile.get_path())
        except GLib.Error:
            return

        if self._check_location(schema_key, path):
            SETTINGS.set_string(schema_key, str(path))
            self._update_subtitles()
            self._update_warnings()
        else:
            self._show_invalid_dialog(schema_key)

    def _check_location(self, schema_key: str, path: Path) -> bool:
        """Validate if a candidate path matches the subpath rules."""
        if schema_key not in _LOCATION_VALIDATION:
            return True
        rules, _ = _LOCATION_VALIDATION[schema_key]
        for subpath, is_dir in rules:
            p = path / subpath
            if is_dir:
                if not p.is_dir():
                    return False
            else:
                if not p.is_file():
                    return False
        return True

    def _show_invalid_dialog(self, schema_key: str) -> None:
        """Show and alert user about invalid directory configuration."""
        _, invalid_subtitle = _LOCATION_VALIDATION[schema_key]
        source_name = schema_key.split("-")[0].capitalize()
        dialog = Adw.AlertDialog(
            title=_("Invalid Directory"),
            body=invalid_subtitle.format(source_name),
        )
        dialog.add_response("ok", _("OK"))
        dialog.present(self)

    def _update_subtitles(self) -> None:
        """Update subtitle path descriptions for all configuration rows."""
        action_rows = {
            "steam-location": self.steam_data_action_row,
            "lutris-location": self.lutris_data_action_row,
            "heroic-location": self.heroic_config_action_row,
            "itch-location": self.itch_config_action_row,
            "legendary-location": self.legendary_config_action_row,
            "flatpak-system-location": self.flatpak_system_data_action_row,
            "flatpak-user-location": self.flatpak_user_data_action_row,
        }

        for key, row in action_rows.items():
            if row is not None:
                val = SETTINGS.get_string(key)
                if val:
                    subtitle = str(Path(os.path.expanduser(val)))
                    if sys.platform.startswith("linux"):
                        subtitle = re.sub(r"/run/user/\d*/doc/.*/", "", subtitle)
                        subtitle = re.sub(f"^{str(Path.home())}", "~", subtitle)
                    row.set_subtitle(subtitle)
                else:
                    row.set_subtitle(_("Select Location"))

    def _update_warnings(self) -> None:
        """Render or remove error warning badges next to rows."""
        action_rows = {
            "steam-location": self.steam_data_action_row,
            "lutris-location": self.lutris_data_action_row,
            "heroic-location": self.heroic_config_action_row,
            "itch-location": self.itch_config_action_row,
            "legendary-location": self.legendary_config_action_row,
            "flatpak-system-location": self.flatpak_system_data_action_row,
            "flatpak-user-location": self.flatpak_user_data_action_row,
        }

        for key, row in action_rows.items():
            if row is not None:
                val = SETTINGS.get_string(key)
                valid = True
                if val:
                    valid = self._check_location(key, Path(os.path.expanduser(val)))

                if not valid:
                    if key not in self._warning_widgets:
                        title = _("Installation Not Found")
                        description = _("Select a valid directory")
                        format_start = '<span rise="12pt"><b><big>'
                        format_end = "</big></b></span>\n"

                        popover = Gtk.Popover(
                            focusable=True,
                            child=Gtk.Label(
                                label=format_start + title + format_end + description,
                                use_markup=True,
                                wrap=True,
                                max_width_chars=50,
                                halign=Gtk.Align.CENTER,
                                valign=Gtk.Align.CENTER,
                                justify=Gtk.Justification.CENTER,
                                margin_top=9,
                                margin_bottom=9,
                                margin_start=12,
                                margin_end=12,
                            ),
                        )
                        popover.connect("show", lambda w: self.set_focus(w))

                        warning_btn = Gtk.MenuButton(
                            icon_name="dialog-warning-symbolic",
                            valign=Gtk.Align.CENTER,
                            popover=popover,
                            tooltip_text=_("Warning"),
                        )
                        warning_btn.add_css_class("warning")
                        row.add_prefix(warning_btn)
                        self._warning_widgets[key] = warning_btn
                else:
                    if key in self._warning_widgets:
                        row.remove(self._warning_widgets[key])
                        del self._warning_widgets[key]

    @Gtk.Template.Callback()
    def _on_fetch_clicked(self, _btn: Gtk.Button) -> None:
        """Triggered when the user clicks 'Update Covers'."""
        app = Gio.Application.get_default()
        if app is not None:
            app.create_asyncio_task(self._update_sgdb_covers())

    async def _update_sgdb_covers(self) -> None:
        """Fetch and update covers from SteamGridDB asynchronously."""
        import asyncio
        from cartridges import sources
        from cartridges.utils import steamgriddb

        self.sgdb_stack.set_visible_child(self.sgdb_spinner)

        prefer_sgdb = SETTINGS.get_boolean("sgdb-prefer")
        animated = SETTINGS.get_boolean("sgdb-animated")

        games_to_update = []
        for source in sources.model:
            for i in range(source.get_n_items()):
                game = source.get_item(i)
                if game is None:
                    continue
                if not prefer_sgdb and game.cover is not None:
                    continue
                games_to_update.append(game)

        if not games_to_update:
            self._send_toast(_("All covers are up to date!"))
            self.sgdb_stack.set_visible_child(self.sgdb_fetch_button)
            return

        success_count = 0
        total = len(games_to_update)

        for game in games_to_update:
            try:
                sgdb_id = await asyncio.to_thread(steamgriddb.get_game_id, game.name)
                url = await asyncio.to_thread(steamgriddb.get_image_url, sgdb_id, animated)
                success = await asyncio.to_thread(steamgriddb.save_cover_from_url, game.game_id, url)
                if success:
                    from cartridges import cover
                    base = cover.COVERS_DIR / game.game_id
                    new_cover = cover.at_path(f"{base}.gif") or cover.at_path(f"{base}.tiff")
                    if new_cover:
                        GLib.idle_add(setattr, game, "cover", new_cover)
            except Exception:
                continue

        self._send_toast(
            _("Finished updating covers: {}/{} successful.").format(success_count, total)
        )
        self.sgdb_stack.set_visible_child(self.sgdb_fetch_button)

    def _send_toast(self, message: str) -> None:
        app = Gio.Application.get_default()
        if app is not None and app.props.active_window is not None:
            app.props.active_window.send_toast(message)

    def _send_toast_with_undo(self, message: str, undo: Any) -> None:
        app = Gio.Application.get_default()
        if app is not None and app.props.active_window is not None:
            app.props.active_window.send_toast(message, undo=undo)

    @Gtk.Template.Callback()
    def _on_remove_all_clicked(self, *_args: Any) -> None:
        """Present confirmation dialog to remove all games."""
        dialog = Adw.AlertDialog(
            title=_("Remove All Games?"),
            body=_("This will hide all games from your library. You can undo this action."),
        )
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("remove", _("Remove All"))
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")
        dialog.connect("response", self._on_remove_all_response)
        dialog.present(self)

    def _on_remove_all_response(self, _dialog: Adw.AlertDialog, response: str) -> None:
        if response == "remove":
            self._remove_all_games()

    def _remove_all_games(self) -> None:
        """Mark all active games as removed and show an Undo toast."""
        from cartridges import sources

        self._removed_games.clear()
        for source in sources.model:
            for i in range(source.get_n_items()):
                game = source.get_item(i)
                if game is not None and not game.removed:
                    game.removed = True
                    if game.source == "imported":
                        game.save()
                    self._removed_games.append(game)

        if self._removed_games:
            self._send_toast_with_undo(
                _("Removed {} games").format(len(self._removed_games)),
                undo=self._undo_remove_all,
            )
        else:
            self._send_toast(_("No games to remove."))

    def _undo_remove_all(self) -> None:
        """Undo removing all games."""
        for game in self._removed_games:
            game.removed = False
            if game.source == "imported":
                game.save()
        count = len(self._removed_games)
        self._removed_games.clear()
        self._send_toast(_("Restored {} games").format(count))

    @Gtk.Template.Callback()
    def _on_reset_clicked(self, *_args: Any) -> None:
        """Present confirmation dialog to reset the application."""
        dialog = Adw.AlertDialog(
            title=_("Reset App?"),
            body=_("This will erase all cover images, added games, and custom settings. This action cannot be undone."),
        )
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("reset", _("Reset"))
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")
        dialog.connect("response", self._on_reset_response)
        dialog.present(self)

    def _on_reset_response(self, _dialog: Adw.AlertDialog, response: str) -> None:
        if response == "reset":
            self._reset_app()

    def _reset_app(self) -> None:
        """Reset all GSettings and delete user-specific cartridges data."""
        from shutil import rmtree
        from cartridges import DATA_DIR

        rmtree(DATA_DIR, ignore_errors=True)

        for key in SETTINGS.list_keys():
            SETTINGS.reset(key)
        for key in STATE_SETTINGS.list_keys():
            STATE_SETTINGS.reset(key)

        app = Gio.Application.get_default()
        if app is not None:
            app.quit()
