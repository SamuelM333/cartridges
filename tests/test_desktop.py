# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright 2026 samuelm333

"""Test reading games and their icons from desktop entries."""

import importlib
import shlex
import sys
import tempfile
import types
from pathlib import Path
from typing import TYPE_CHECKING

import gi

gi.require_versions({"Gdk": "4.0", "Gtk": "4.0"})
from gi.repository import Gdk, GLib, Gtk
from PIL import Image

if TYPE_CHECKING:
    from cartridges.games import Game


class _Settings:
    """Stand-in for the application's `Gio.Settings`."""

    def get_boolean(self, _key: str) -> bool:
        return False

    def get_string(self, _key: str) -> str:
        return ""

    def get_user_value(self, _key: str) -> GLib.Variant | None:
        return None


_ROOT = Path(tempfile.mkdtemp())
_DATA = _ROOT / "data"
_SYSTEM_DATA = _ROOT / "system"
_ICON = "cartridges-test-icon"

# Importing the real `cartridges` package needs the meson-generated `config.py`
# and compiled GSettings schemas, so stub the package with only what
# `sources.desktop` uses.
_package = types.ModuleType("cartridges")
_package.__path__ = [str(Path(__file__).resolve().parents[1] / "cartridges")]
_package.DATA_DIR = _ROOT / "cartridges"  # pyright: ignore[reportAttributeAccessIssue]
_package.SETTINGS = _Settings()  # pyright: ignore[reportAttributeAccessIssue]
sys.modules["cartridges"] = _package

_config = types.ModuleType("cartridges.config")
_config.PREFIX = "/page/samuelm333/Cartridges/Test"  # pyright: ignore[reportAttributeAccessIssue]
sys.modules["cartridges.config"] = _config

sources = importlib.import_module("cartridges.sources")
vars(sources)["DATA"] = _DATA
vars(sources)["SYSTEM_DATA"] = (_SYSTEM_DATA,)

desktop = importlib.import_module("cartridges.sources.desktop")
vars(desktop)["_DESKTOP_PATHS"] = (
    _DATA / "applications",
    _SYSTEM_DATA / "applications",
)


def _png(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGBA", (48, 48), "red").save(path)
    return path


_THEME_ICON = _png(_DATA / "icons" / "hicolor" / "48x48" / "apps" / f"{_ICON}.png")
_PIXMAP_ICON = _png(_SYSTEM_DATA / "pixmaps" / f"{_ICON}-pixmap.png")
_PATH_ICON = _png(_ROOT / "elsewhere" / "icon.png")
_NOT_AN_IMAGE = _ROOT / "elsewhere" / "not-an-image.png"
_NOT_AN_IMAGE.write_text("not an image", encoding="utf-8")


def _write_entry(name: str, folder: Path = _DATA / "applications", **keys: str) -> Path:
    keys = {
        "Type": "Application",
        "Name": name,
        "Exec": "true",
        "Categories": "Game;",
        **keys,
    }
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{name}.desktop"
    lines = ["[Desktop Entry]", *(f"{key}={value}" for key, value in keys.items())]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _games() -> dict[str, "Game"]:
    return {game.game_id: game for game in desktop.get_games()}


def _icon_path(value: str | None) -> str | None:
    icon = desktop._icon(value)  # noqa: SLF001
    if icon is None:
        return None

    if not isinstance(icon, Gtk.IconPaintable):
        msg = f"Expected an icon paintable for {value!r}, got {icon!r}"
        raise AssertionError(msg)  # noqa: TRY004

    file = icon.get_file()
    return None if file is None else file.get_path()


def _default_path() -> str | None:
    return _icon_path(None)


def _expect(actual: object, expected: object, what: str) -> None:
    if actual != expected:
        msg = f"Expected {what} to be {expected!r}, got {actual!r}"
        raise AssertionError(msg)


def check_default_is_adwaita() -> None:
    """Validate that the default icon is the Adwaita application icon."""
    path = _default_path()
    suffix = "Adwaita/scalable/mimetypes/application-x-executable.svg"
    if path is None or not path.endswith(suffix):
        msg = f"Expected the default icon to end with {suffix}, got {path!r}"
        raise AssertionError(msg)


def check_icon_missing_uses_default() -> None:
    """Validate that an entry without an icon uses the default icon."""
    _expect(_icon_path(""), _default_path(), "icon for an empty value")


def check_icon_unknown_name_uses_default() -> None:
    """Validate that an icon name that is not installed uses the default icon."""
    _expect(
        _icon_path("cartridges-test-does-not-exist"),
        _default_path(),
        "icon for an unknown name",
    )


def check_icon_theme_name() -> None:
    """Validate that an icon installed in hicolor is found by name."""
    _expect(_icon_path(_ICON), str(_THEME_ICON), "icon for a theme name")


def check_icon_name_with_extension() -> None:
    """Validate that a trailing image extension is ignored, as GLib does."""
    _expect(_icon_path(f"{_ICON}.png"), str(_THEME_ICON), "icon for a name.png")


def check_icon_pixmaps() -> None:
    """Validate that icons in pixmaps folders are found by name."""
    _expect(_icon_path(f"{_ICON}-pixmap"), str(_PIXMAP_ICON), "icon in pixmaps")


def check_icon_path_valid() -> None:
    """Validate that an icon given as a path to an image is used."""
    _expect(_icon_path(str(_PATH_ICON)), str(_PATH_ICON), "icon for a valid path")


def check_icon_path_missing_uses_default() -> None:
    """Validate that a path to a missing file uses the default icon."""
    _expect(
        _icon_path(str(_ROOT / "missing.png")),
        _default_path(),
        "icon for a missing file",
    )


def check_icon_path_not_an_image_uses_default() -> None:
    """Validate that a path to a file that is not an image uses the default icon."""
    _expect(
        _icon_path(str(_NOT_AN_IMAGE)),
        _default_path(),
        "icon for a file that is not an image",
    )


def check_icon_never_image_missing() -> None:
    """Validate that GTK's missing image icon is never used."""
    for value in (
        None,
        "",
        "cartridges-test-does-not-exist",
        "cartridges-test-does-not-exist.png",
        _ICON,
        str(_ROOT / "missing.png"),
        str(_NOT_AN_IMAGE),
    ):
        path = _icon_path(value)
        if path is None or path.endswith("image-missing.png"):
            msg = f"Expected a real icon file for {value!r}, got {path!r}"
            raise AssertionError(msg)


def check_game_has_cover() -> None:
    """Validate that a game whose icon is missing still gets a cover."""
    _write_entry("cover", Icon="cartridges-test-does-not-exist")
    game = _games()["desktop_cover"]
    if not isinstance(game.cover, Gdk.Paintable):
        msg = f"Expected a cover, got {game.cover!r}"
        raise AssertionError(msg)  # noqa: TRY004


def check_requires_game_category() -> None:
    """Validate that entries outside the Game category are skipped."""
    _write_entry("not-a-game", Categories="Utility;")
    _expect("desktop_not-a-game" in _games(), False, "entry without Game imported")


def check_skips_nodisplay() -> None:
    """Validate that entries not to be displayed are skipped."""
    _write_entry("nodisplay", NoDisplay="true")
    _expect("desktop_nodisplay" in _games(), False, "NoDisplay entry imported")


def check_skips_hidden() -> None:
    """Validate that hidden entries are skipped."""
    _write_entry("hidden", Hidden="true")
    _expect("desktop_hidden" in _games(), False, "Hidden entry imported")


def check_skips_blacklisted_file_name() -> None:
    """Validate that entries of other sources are skipped by file name."""
    _write_entry("net.lutris.foo")
    _expect("desktop_net.lutris.foo" in _games(), False, "Lutris entry imported")


def check_skips_blacklisted_exec() -> None:
    """Validate that entries of other sources are skipped by launch command."""
    _write_entry("steam-game", Exec="steam://rungameid/1")
    _expect("desktop_steam-game" in _games(), False, "Steam entry imported")


def check_skips_x_flatpak() -> None:
    """Validate that entries exported by Flatpak are skipped."""
    path = _write_entry("flatpak-app")
    with path.open("a", encoding="utf-8") as f:
        f.write("X-Flatpak=org.example.App\n")

    _expect("desktop_flatpak-app" in _games(), False, "Flatpak entry imported")


def check_skips_missing_name() -> None:
    """Validate that entries without a name are skipped."""
    path = _write_entry("nameless")
    text = path.read_text(encoding="utf-8").replace("Name=nameless\n", "")
    path.write_text(text, encoding="utf-8")
    _expect("desktop_nameless" in _games(), False, "entry without Name imported")


def check_skips_unreadable_entry() -> None:
    """Validate that a broken entry is skipped and others still import."""
    folder = _DATA / "applications"
    (folder / "broken.desktop").write_text("not a key file\n", encoding="utf-8")
    _write_entry("still-works")
    games = _games()
    _expect("desktop_broken" in games, False, "broken entry imported")
    _expect("desktop_still-works" in games, True, "other entry imported")


def check_first_location_wins() -> None:
    """Validate that the first folder wins when two have the same file name."""
    _write_entry("twice", Name="User")
    _write_entry("twice", _SYSTEM_DATA / "applications", Name="System")
    _expect(_games()["desktop_twice"].name, "User", "name of a duplicate entry")


def check_game_fields() -> None:
    """Validate the fields of an imported game."""
    path = _write_entry("fields", Name="Some Game")
    game = _games()["desktop_fields"]
    _expect(game.source, "desktop", "source")
    _expect(game.name, "Some Game", "name")
    _expect(game.executable, f"gio launch {shlex.quote(str(path))}", "executable")


if __name__ == "__main__":
    check_default_is_adwaita()
    check_icon_missing_uses_default()
    check_icon_unknown_name_uses_default()
    check_icon_theme_name()
    check_icon_name_with_extension()
    check_icon_pixmaps()
    check_icon_path_valid()
    check_icon_path_missing_uses_default()
    check_icon_path_not_an_image_uses_default()
    check_icon_never_image_missing()
    check_game_has_cover()
    check_requires_game_category()
    check_skips_nodisplay()
    check_skips_hidden()
    check_skips_blacklisted_file_name()
    check_skips_blacklisted_exec()
    check_skips_x_flatpak()
    check_skips_missing_name()
    check_skips_unreadable_entry()
    check_first_location_wins()
    check_game_fields()
