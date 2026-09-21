# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright 2025 Zoey Ahmed
# SPDX-FileCopyrightText: Copyright 2022-2026 kramo

import os
from collections.abc import Generator
from gettext import gettext as _
from pathlib import Path

from gi.repository import GLib, Gtk

from cartridges import SETTINGS, cover
from cartridges.games import Game

ID, NAME = "flatpak", _("Flatpak")

_ICON_FALLBACK = "application-x-executable"


def get_games() -> Generator[Game]:
    """Installed Flatpak games."""
    if not SETTINGS.get_boolean("flatpak"):
        return

    system_loc = SETTINGS.get_string("flatpak-system-location")
    user_loc = SETTINGS.get_string("flatpak-user-location")

    system_path = Path(os.path.expanduser(system_loc)) if system_loc else None
    user_path = Path(os.path.expanduser(user_loc)) if user_loc else None

    app_dirs: list[Path] = []
    icon_dirs: list[Path] = []

    if system_path:
        app_dirs.append(system_path / "exports" / "share" / "applications")
        icon_dirs.append(system_path / "exports" / "share" / "icons")

    if user_path:
        app_dirs.append(user_path / "exports" / "share" / "applications")
        icon_dirs.append(user_path / "exports" / "share" / "icons")

    blacklist = {
        "page.samuelm333.Cartridges",
        "page.samuelm333.Cartridges.Devel",
    }
    if not SETTINGS.get_boolean("flatpak-import-launchers"):
        blacklist.update({
            "com.valvesoftware.Steam",
            "net.lutris.Lutris",
            "com.heroicgameslauncher.hgl",
            "com.usebottles.Bottles",
            "io.itch.itch",
            "org.libretro.RetroArch",
        })

    icon_theme = _get_icon_theme(icon_dirs)
    imported_ids: set[str] = set()

    for app_dir in app_dirs:
        if not app_dir.is_dir():
            continue

        for entry in app_dir.glob("*.desktop"):
            if not entry.is_file():
                continue

            keyfile = GLib.KeyFile.new()
            try:
                if not keyfile.load_from_file(str(entry), GLib.KeyFileFlags.NONE):
                    continue

                categories = keyfile.get_string_list("Desktop Entry", "Categories")
                if "Game" not in categories:
                    continue

                flatpak_id = keyfile.get_string("Desktop Entry", "X-Flatpak")
                if flatpak_id in blacklist or flatpak_id != entry.stem:
                    continue

                name = keyfile.get_string("Desktop Entry", "Name")
            except GLib.Error:
                continue

            if flatpak_id in imported_ids:
                continue
            imported_ids.add(flatpak_id)

            try:
                icon_name = keyfile.get_string("Desktop Entry", "Icon")
            except GLib.Error:
                icon_name = _ICON_FALLBACK

            icon = icon_theme.lookup_icon(
                icon_name,
                fallbacks=(_ICON_FALLBACK,),
                size=cover.ICON_SIZE,
                scale=2,
                direction=Gtk.TextDirection.NONE,
                flags=Gtk.IconLookupFlags.NONE,
            )

            yield Game(
                executable=f"flatpak run {flatpak_id}",
                game_id=f"{ID}_{flatpak_id}",
                source=ID,
                name=name,
                cover=cover.from_icon(icon),
            )


def _get_icon_theme(icon_dirs: list[Path]) -> Gtk.IconTheme:
    icon_theme = Gtk.IconTheme()
    search_path = icon_theme.props.search_path or []
    for d in icon_dirs:
        if d.is_dir() and str(d) not in search_path:
            search_path.append(str(d))
    icon_theme.props.search_path = search_path
    return icon_theme

