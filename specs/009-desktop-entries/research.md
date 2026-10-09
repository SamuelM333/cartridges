# Research: Desktop Entries

**Feature**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

All findings below were reproduced on 2026-10-09 inside the installed `page.samuelm333.Cartridges` Flatpak (GNOME 50 runtime, GTK 4.22), using the same icon search path the Desktop source builds today.

## R-1: Why desktop entry games show a broken-image icon

**Finding**: `_icon_theme()` creates `Gtk.IconTheme()` without a theme name. Its `theme_name` is `None`, so only `hicolor` and the unthemed search directories are consulted. Results of `lookup_icon(name, fallbacks=("application-x-executable",), ...)`:

| Icon value in entry | Result |
|---------------------|--------|
| `does-not-exist` | `resource:///org/gtk/libgtk/icons/16x16/status/image-missing.png` |
| `/usr/share/pixmaps/foo.png` (absolute path) | `image-missing` |
| `/run/host/usr/share/icons/hicolor/48x48/apps/steam.png` (absolute path, file exists) | `image-missing` |
| `application-x-executable` (the fallback itself) | `image-missing` |
| `steam` (installed in hicolor) | correct icon |

So there are two causes, both confirmed:

1. **The fallback icon is never found.** `application-x-executable` lives in the Adwaita theme (`/usr/share/icons/Adwaita/scalable/mimetypes/application-x-executable.svg` in the runtime), not in hicolor. With no theme set, GTK falls through to its built-in `image-missing` placeholder. That is the broken-image icon users see, for every missing or unknown icon.
2. **Absolute paths are treated as theme names.** GTK 4's `lookup_icon` does not load files by path. Entries with `Icon=/path/to/icon.png` always show `image-missing`, even when the file exists.

**Decision**: Fix both. Details follow in R-1a to R-5.

## R-1a: How upstream Cartridges `main` did it (legacy, known to work)

Source: `cartridges/importer/desktop_source.py` and `cartridges/store/managers/cover_manager.py` in the local clone of upstream `main` (`~/Development/cartridges-main`, commit `d56323e`). Per the constitution, this is used only as a behavior reference, not as code to copy.

| Step | Legacy behavior |
|------|-----------------|
| Icon theme | `Gtk.IconTheme.new()`, no theme name (same as today) |
| Search path | `add_search_path` for `<host data>/icons`, `/run/host/usr/local/share/icons`, `/run/host/usr/share/icons`, `/run/host/usr/share/pixmaps`, `/usr/share/pixmaps`, and each `GLib.get_system_data_dirs()/icons`. Paths under `/app/` are skipped. |
| `Icon` missing | No icon; the game gets no cover |
| `Icon` contains `/` | Used directly as a file path, with no lookup |
| `Icon` is a name | `lookup_icon(name, None, 512, 1, ...)`, **with no fallbacks**. Accepted only if `.get_file().get_path()` is not `None`. |
| Icon not found | `get_path()` is `None` (GTK's `image-missing` is a `resource://` file), so no icon and no cover |
| Path missing or not an image | The cover manager skips it if `not is_file()`. A decode error leaves no cover. |
| Cover | Icon at 0.7 scale over a blurred, stretched copy of itself (a 1x2 blur upscaled to cover size), saved as the game's cover file |

**Why it never showed a broken icon**: it never asked GTK for a fallback. It treated "lookup did not resolve to a real file path" as "no icon", and a game without an icon got no cover. The UI then showed its normal placeholder. Real app icons resolved because hicolor and pixmaps were searched without anything in front of them.

**Verified on GTK 4.22** (same sandbox as R-1), with the legacy-style unnamed theme plus host `icons` and `pixmaps` paths:

| Name | `lookup_icon(name, None, ...).get_file().get_path()` |
|------|--------------------------------------------------------|
| `steam` | `/run/host/share/icons/hicolor/256x256/apps/steam.png` |
| `cupsprinter` (pixmaps only) | `/run/host/usr/share/pixmaps/cupsprinter.png` |
| `does-not-exist` | `None` |
| `application-x-executable` | `None` (not in hicolor) |

`Gtk.IconTheme(theme_name="Adwaita").lookup_icon("application-x-executable", None, ...)` resolves to `/usr/share/icons/Adwaita/scalable/mimetypes/application-x-executable.svg`.

**What the current code changed, and why it broke**: the rewrite added `fallbacks=("application-x-executable",)` to give icon-less entries a generic icon. That icon is not in hicolor, and the theme has no name, so the fallback never resolves and GTK returns `image-missing`. The rewrite also dropped the `/`-means-path rule and the `pixmaps` search paths.

**Decision**: Follow the legacy approach for finding an entry's own icon. Then, instead of "no cover", use the default application icon, as the spec requires (FR-014). Legacy showed the placeholder; the spec asks for the generic desktop icon.

## R-2: Which icon theme to look in

**Pitfall found**: When `lookup_icon` is given a fallback list, GTK searches each theme in the inheritance chain for *all* names before moving to the next theme. With `theme_name="Adwaita"`, `lookup_icon("steam", fallbacks=("application-x-executable",))` returned the generic Adwaita icon even though `steam.png` is installed in hicolor. Fallbacks shadow real app icons.

**Decision**: Use two lookups, never `fallbacks`:
1. **Entry icon**: the unnamed `Gtk.IconTheme()` with the legacy search path (R-1a, R-5). Look up the name with no fallbacks, and accept the result only if `get_file().get_path()` is not `None`. This is the legacy detection, and it is what kept legacy free of broken icons.
2. **Default icon**: a separate `Gtk.IconTheme(theme_name="Adwaita")`, used only to look up `application-x-executable`, with the same path check. If that fails, use the bundled copy (R-4).

**Rationale**: Entry icon lookup stays exactly as proven in legacy. Adwaita is only consulted for the one icon it provides, so it cannot shadow or replace any app's icon. Both themes are display-independent (Constitution II).

**Alternatives considered**:
- *A single Adwaita-named theme for everything, with `has_icon` first* (the previous version of this plan): this works, but Adwaita's own icons would take priority over hicolor for overlapping names, so lookups would diverge from legacy for no benefit.
- *Use the user's icon theme* (`Gtk.IconTheme.get_for_display`): this ties the source to a display. Neither legacy nor the baseline did this.
- *Keep `fallbacks`*: this is the bug.
- *Legacy's "no cover" when no icon is found*: rejected by the spec (FR-014 asks for the default application icon).

## R-3: Icons given as file paths

**Finding**: `Gdk.Texture.new_from_filename()` (GTK 4.22) loads PNG and SVG files. It raises `GLib.Error` for a missing file ("No such file or directory") or a non-image file ("Unrecognized image file format"). That makes it a reliable validity check. `Gtk.IconPaintable.new_for_file(file, size, scale)` renders the file at the requested size (sharp SVGs), but it loads lazily and draws `image-missing` on failure. It must only be used after validation.

Legacy treated any value containing `/` as a path and only checked `is_file()`. If the image could not be decoded, the result was no cover. The steps below keep that rule and add a decode check, so an invalid file falls back to the default icon instead of failing.

**Decision**: When `Icon` contains `/` (the legacy rule; in practice an absolute path):
1. Build the candidate paths. Inside Flatpak, try `/run/host/<path>` first (host `/usr` is only visible there), then the path itself (home directories and other exposed locations). Outside Flatpak, use the path only.
2. Use the first candidate that is a file and that `Gdk.Texture.new_from_filename()` loads without error. Render it with `Gtk.IconPaintable.new_for_file(..., cover.ICON_SIZE, 2)`.
3. If no candidate passes, use the default application icon.

**Alternatives considered**: Loading with PIL (`cover.at_path`) does not support SVG. `GdkPixbuf` works, but it is a deprecated path in GTK 4 and needs an extra typelib.

## R-4: Default application icon when Adwaita is not installed

**Finding**: Native (non-Flatpak) installs on non-GNOME desktops may not have the Adwaita icon theme. Then the Adwaita lookup of `application-x-executable` does not resolve to a file path. Using it anyway would again show `image-missing`.

**Decision**: Bundle a copy of Adwaita's `application-x-executable.svg` in the app's icon GResource, under its own prefix (`@PREFIX@/fallback`). That way it is not registered as a themed icon and cannot shadow the user's theme. Load it with `Gtk.IconPaintable.new_for_file(Gio.File.new_for_uri("resource://..."))` only when the theme lookup fails. If the resource is not registered (for example, in unit tests), return no cover. The UI then shows its normal "no cover" placeholder, which is still not a broken-image icon.

**Rationale**: FR-015 requires that a broken-image icon is never shown. The bundled copy is about 2 KB.

**Licensing note**: Adwaita icons are dual-licensed LGPL-3.0 / CC-BY-SA-3.0. Both are compatible with redistribution in a GPL-3.0-or-later application. Record the source and license in the SVG's SPDX header, or in a comment next to the GResource entry. `svgo` (pre-commit) must keep that comment or its equivalent.

## R-5: Icon names with a file extension

**Finding**: GLib's own desktop entry loader (`GDesktopAppInfo`) strips `.png`, `.svg`, and `.xpm` from non-absolute `Icon` values before theme lookup. Many legacy entries use names like `mygame.png`.

**Decision**: Strip those three extensions before lookup, as GLib does. Legacy did not strip them, but stripping is harmless for names without an extension. Restore legacy's `pixmaps` search paths by adding `<data>/pixmaps` next to `<data>/icons` for every data directory (`DATA`, `SYSTEM_DATA`). This covers legacy's `/run/host/usr/share/pixmaps`, and the freedesktop icon spec requires it. GTK's default search path already includes the sandbox's own `/usr/share/pixmaps`.

## R-6: Covers saved before the fix (FR-016)

**Finding**: Three code paths keep a stale or broken cover:
1. **Import Now / startup import into an existing library** (`importer.reconcile`): a game already in the library keeps its cover. A scanned cover is only used if the game had none.
2. **Startup with "Import Games on Startup" on** (`Source.__init__` -> `scan`): games are rebuilt from the scan, so the in-memory cover is fresh. But `saved_library._write_covers` only writes a cover PNG if none exists, so the broken PNG on disk is kept. The next start with the switch off shows it again.
3. **Custom covers**: a cover the user picks (local file or SteamGridDB) is written to `cover.COVERS_DIR/<game_id>.tiff|.gif`. Only `sources/imported.py` reads those files back. For launcher games, path 2 replaces a custom cover with the scanned one after a restart. This is a baseline defect that FR-016 ("a cover the user chose MUST NOT be replaced") touches.

**Decision**:
- Add `cover.custom(game_id) -> Gdk.Paintable | None`. It loads `COVERS_DIR/<game_id>.gif` or `.tiff`, which is the logic currently repeated in `imported.py`, `application.py`, `preferences.py`, and `cover_picker.py`.
- In `Source.scan`, prefer `cover.custom(game.game_id)` over the cover the source module produced, for every source. This fixes path 3 and makes "custom" visible to reconcile.
- Source modules may declare `REFRESH_COVERS: Final = True`. Only `desktop` does. For such sources:
  - `reconcile(..., refresh_covers=True)` replaces the kept game's cover with the scanned cover whenever the scanned cover is not `None`. The existing `notify::cover` handler then deletes the saved PNG and requests a save (path 1).
  - `Source.scan` calls `saved_library.forget_cover(game_id)` for each scanned game, so the next save writes the fresh cover (path 2).

**Rationale**: Covers made from desktop entry icons are cheap to regenerate and are never edited by the user. Refreshing them each import is the only way a fixed or newly installed icon reaches existing users (spec edge cases "icon becomes available/unavailable later"). Applying custom covers in `scan` is one line that serves every source. Without it, FR-016's "custom cover is kept" would not hold at startup.

**Alternatives considered**:
- *Refresh covers for every source*: Steam and similar sources would rewrite hundreds of cover PNGs on every import, with no user-visible benefit. Rejected.
- *Mark icon-derived covers with a flag on `Game`*: this adds a persisted property and a library format change for a fact that can be derived (custom cover file exists or not). Rejected.
- *Hard-code `source.id == "desktop"` in `Source`*: this works, but it leaks source knowledge into the generic class. A module-level flag follows the existing `ID`/`NAME` pattern (Constitution II).

## R-6a: Legacy cover style (blurred background)

**Finding**: Legacy covers for icons were not a centered icon on a blank canvas. They showed the icon at 0.7 scale over a blurred, stretched copy of itself (R-1a).

**Decision**: Out of scope. The spec covers which icon is shown, not the cover style, and `cover.from_icon` is shared with the Flatpak source. Record this as a possible follow-up feature.

## R-7: Testing without a display

**Finding**: Repository tests are plain scripts (`python tests/test_*.py`) that stub the `cartridges` package (no meson `config.py`, no GSettings). `Gtk.IconTheme()`, `Gtk.IconTheme(theme_name=...)`, `lookup_icon`, and `Gdk.Texture.new_from_filename` worked in the sandbox without creating a window. In CI, the GNOME 50 SDK provides the Adwaita theme through `XDG_DATA_DIRS`.

**Decision**: Add `tests/test_desktop.py`, which stubs `cartridges`, `cartridges.config` (`PREFIX`) and `cartridges.sources` data paths to a temporary directory. It writes `.desktop` files and icon files there and checks the resolved icon source (theme icon / file / fallback) rather than pixels. Extend `tests/test_importer.py` with `refresh_covers` and custom-cover checks.
