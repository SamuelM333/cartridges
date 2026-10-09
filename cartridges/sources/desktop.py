# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright 2023-2026 kramo
# SPDX-FileCopyrightText: Copyright 2026 Jamie Gravendeel

import functools
import itertools
import shlex
import subprocess
from collections.abc import Generator
from contextlib import suppress
from gettext import gettext as _
from pathlib import Path
from typing import Final, cast

from gi.repository import Gdk, Gio, GLib, Gtk

from cartridges import cover, games
from cartridges.config import PREFIX
from cartridges.games import Game

from . import DATA, SYSTEM_DATA

ID, NAME = "desktop", _("Desktop")

# Covers are made from entry icons, so they are made again on each import
# to pick up icons that were installed, removed or fixed since.
REFRESH_COVERS: Final = True

_DATA_PATHS = (DATA, *SYSTEM_DATA)
_ICON_PATHS = tuple(path / sub for path in _DATA_PATHS for sub in ("icons", "pixmaps"))
_DESKTOP_PATHS = (
    Path(cast(str, GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DESKTOP))),
    *(path / "applications" for path in _DATA_PATHS),
)

_FILE_BLACKLIST = (
    "page.kramo.Cartridges.*",
    "page.samuelm333.Cartridges.*",
    "net.lutris.*",
)
_EXECUTABLE_BLACKLIST = (
    "steam://rungameid/",
    "heroic://launch/",
    "bottles-cli ",
)
_FLATPAK_ID_BLACKLIST = frozenset((
    "hu.kramo.Cartridges",
    "hu.kramo.Cartridges.Devel",
    "page.kramo.Cartridges",
    "page.kramo.Cartridges.Devel",
    "page.samuelm333.Cartridges",
    "page.samuelm333.Cartridges.Devel",
    "com.heroicgameslauncher.hgl",
    "com.usebottles.bottles",
    "com.valvesoftware.Steam",
    "io.itch.itch",
    "net.lutris.Lutris",
    "org.libretro.RetroArch",
))

_HIDDEN_KEYS = "NoDisplay", "Hidden"

_ICON_FALLBACK = "application-x-executable"
_ICON_EXTENSIONS = ".png", ".svg", ".xpm"


def get_games() -> Generator[Game]:
    """Installed desktop entries."""
    seen = set()
    paths = itertools.chain.from_iterable(p.glob("*.desktop") for p in _DESKTOP_PATHS)
    for path in paths:
        if path.name in seen or any(path.match(pattern) for pattern in _FILE_BLACKLIST):
            continue

        try:
            game = _game_from(path)
        except (GLib.Error, ValueError):
            continue

        yield game
        seen.add(path.name)


def _game_from(path: Path) -> Game:
    file = GLib.KeyFile()
    file.load_from_file(str(path), GLib.KeyFileFlags.NONE)

    if "Game" not in file.get_string_list("Desktop Entry", "Categories"):
        raise ValueError

    for key in _HIDDEN_KEYS:
        with suppress(GLib.Error):
            if file.get_boolean("Desktop Entry", key):
                raise ValueError

    exe = file.get_string("Desktop Entry", "Exec")
    if any(exe.startswith(cmd) for cmd in _EXECUTABLE_BLACKLIST):
        raise ValueError

    try:
        file.get_string("Desktop Entry", "X-Flatpak")
        raise ValueError
    except GLib.Error:
        pass

    with suppress(GLib.Error):
        if not _try_exec(file.get_string("Desktop Entry", "TryExec")):
            raise ValueError

    icon_value = None
    with suppress(GLib.Error):
        icon_value = file.get_string("Desktop Entry", "Icon")

    try:
        real_path = Path("/", path.relative_to("/run/host"))
    except ValueError:
        real_path = path

    return Game(
        executable=f"gio launch {shlex.quote(str(real_path))}",
        game_id=f"{ID}_{path.stem}",
        source=ID,
        name=file.get_string("Desktop Entry", "Name"),
        cover=cover.from_icon(icon) if (icon := _icon(icon_value)) else None,
    )


def _icon(value: str | None) -> Gdk.Paintable | None:
    """Get the icon an entry's `Icon` key refers to, or the default icon."""
    if not value:
        return _default_icon()

    if "/" in value:
        return _file_icon(value) or _default_icon()

    # Like GLib, ignore an image extension some entries add to the icon name.
    if value.endswith(_ICON_EXTENSIONS):
        value = value.rsplit(".", 1)[0]

    return _lookup(_icon_theme(), value) or _default_icon()


def _lookup(theme: Gtk.IconTheme, name: str) -> Gtk.IconPaintable | None:
    """Look up `name` in `theme`, if it is installed.

    GTK returns its own missing image icon when nothing is found, which is a
    resource without a path, so only icons with a path count as found.
    No fallbacks are given, since GTK looks for them in a theme before its
    parents and they would hide icons of apps that are only in hicolor.
    """
    icon = theme.lookup_icon(
        name,
        fallbacks=None,
        size=cover.ICON_SIZE,
        # Sources shouldn't know about the user's display,
        # so we assume 2x scaling and render the icon at the correct size later.
        scale=2,
        direction=Gtk.TextDirection.NONE,
        flags=Gtk.IconLookupFlags.NONE,
    )
    file = icon.get_file()
    return icon if file is not None and file.get_path() is not None else None


def _file_icon(value: str) -> Gtk.IconPaintable | None:
    """Load the image at the path `value`, if it is one."""
    path = Path(value)
    paths = (
        (Path("/run/host", path.relative_to("/")), path)
        if path.is_absolute() and Path("/.flatpak-info").exists()
        else (path,)
    )
    for candidate in paths:
        if not candidate.is_file():
            continue

        try:
            Gdk.Texture.new_from_filename(str(candidate))
        except GLib.Error:
            continue

        file = Gio.File.new_for_path(str(candidate))
        return Gtk.IconPaintable.new_for_file(file, cover.ICON_SIZE, 2)

    return None


@functools.cache
def _default_icon() -> Gtk.IconPaintable | None:
    """Get the icon for entries without an icon of their own.

    Use the copy bundled with Cartridges if the Adwaita icon theme is missing.
    """
    if icon := _lookup(Gtk.IconTheme(theme_name="Adwaita"), _ICON_FALLBACK):
        return icon

    path = f"{PREFIX}/fallback/{_ICON_FALLBACK}.svg"
    try:
        Gio.resources_get_info(path, Gio.ResourceLookupFlags.NONE)
    except GLib.Error:
        return None

    file = Gio.File.new_for_uri(f"resource://{path}")
    return Gtk.IconPaintable.new_for_file(file, cover.ICON_SIZE, 2)


def _try_exec(executable: str) -> bool:
    try:
        subprocess.run(  # noqa: S603
            shlex.split(games.format_executable(f"which {executable}")),
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError:
        return False
    else:
        return True


@functools.cache
def _icon_theme() -> Gtk.IconTheme:
    icon_theme = Gtk.IconTheme()
    search_path = icon_theme.props.search_path or []
    search_path += [p for path in _ICON_PATHS if (p := str(path)) not in search_path]
    icon_theme.props.search_path = search_path
    return icon_theme
