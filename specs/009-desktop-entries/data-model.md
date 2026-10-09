# Data Model: Desktop Entries

**Feature**: [spec.md](spec.md) | **Research**: [research.md](research.md)

No persisted format changes. `library.json` (`_VERSION = 1`) and the cover files are unchanged. Only how a cover is chosen, and when it is refreshed, changes.

## 1. Desktop entry (input, read-only)

A `.desktop` file read as a `GLib.KeyFile`, group `Desktop Entry`.

| Key | Use | Required |
|-----|-----|----------|
| `Name` | Game title | yes; entry skipped if missing |
| `Exec` | Checked against the executable blacklist only; the game launches the entry, not `Exec` | yes; entry skipped if missing |
| `Categories` | Must contain `Game` | yes |
| `NoDisplay`, `Hidden` | Entry skipped if either is true | no |
| `X-Flatpak` | Entry skipped if present | no |
| `TryExec` | Entry skipped if present and not found with `which` (on the host, inside Flatpak) | no |
| `Icon` | Cover icon, see section 3 | no |

**Search order** (first file name wins): user Desktop folder, `DATA/applications`, each `SYSTEM_DATA/applications`. The file-name blacklist is `page.kramo.Cartridges.*`, `page.samuelm333.Cartridges.*`, `net.lutris.*`. The Exec prefix blacklist is `steam://rungameid/`, `heroic://launch/`, `bottles-cli `. The Flatpak export blacklist is implied by `X-Flatpak`.

## 2. Desktop entry game (`Game`, unchanged shape)

| Field | Value |
|-------|-------|
| `game_id` | `desktop_<file stem>` |
| `source` | `desktop` |
| `name` | `Name` |
| `executable` | `gio launch <quoted real path>`; `/run/host` prefix removed inside Flatpak |
| `cover` | `cover.custom(game_id)` if the user chose one, else the icon cover from section 3 |

## 3. Icon resolution (new rules)

Input: the `Icon` value (may be missing). Output: an icon paintable, or `None`. It is padded into a cover with `cover.from_icon`.

```text
Icon missing or empty        -> DEFAULT
Icon contains "/"            -> first candidate that is a file and loads as an image, else DEFAULT
                                candidates: Flatpak: (/run/host/<path>, <path>); native: (<path>,)
Icon is a name               -> strip trailing .png / .svg / .xpm
                                entry_theme.lookup(name) resolves to a real file path ? that icon : DEFAULT

DEFAULT                      -> default_theme.lookup("application-x-executable") resolves to a real file path ? that icon
                                : bundled resource @PREFIX@/fallback/application-x-executable.svg if registered
                                : None (UI shows its "no cover" placeholder)
```

"Resolves to a real file path" means `icon.get_file().get_path() is not None`. GTK's built-in `image-missing` is a `resource://` file with no path, so it is rejected. This is the legacy detection (research R-1a).

**Entry icon theme**: an unnamed `Gtk.IconTheme()`, as in legacy and today. The search path is the GTK default plus `<data>/icons` and `<data>/pixmaps` for every data directory (`DATA`, `SYSTEM_DATA`).

**Default icon theme**: `Gtk.IconTheme(theme_name="Adwaita")`, used only for `application-x-executable`.

Both lookups use size `cover.ICON_SIZE`, scale 2, and **no `fallbacks` argument** (research R-2).

**Invariant**: The result is never GTK's built-in `image-missing` paintable (FR-015).

## 4. Source module contract (extended)

| Attribute | Type | Meaning |
|-----------|------|---------|
| `ID` | `Final[str]` | unchanged |
| `NAME` | `Final[str]` | unchanged |
| `get_games()` | `Generator[Game]` | unchanged |
| `REFRESH_COVERS` | `Final[bool]`, optional, default `False` | **new**. Covers from this source are regenerated on every import instead of being kept. `True` only for `desktop`. |

## 5. Cover lifecycle for a source game

| Event | Non-refresh source (Steam, ...) | Refresh source (`desktop`) |
|-------|---------------------------------|----------------------------|
| Scan (`Source.scan`) | `cover = custom or scanned` | `cover = custom or scanned`; saved PNG forgotten |
| Reconcile, game already in library | keep existing cover; take scanned only if existing is `None` | take scanned cover if not `None` (it already is the custom cover when one exists) |
| User picks a cover | written to `COVERS_DIR/<id>.tiff\|.gif`; `notify::cover` -> saved PNG forgotten, save requested | same |
| User deletes cover | custom files removed; `cover = None` | same; next import restores the icon cover |
| Save (`saved_library.write`) | PNG written only if missing | same; after a refresh the PNG is missing, so the fresh cover is written |

## 6. `importer.reconcile` (extended signature)

```text
reconcile(existing, scanned, *, refresh_covers: bool = False) -> Reconciliation
```

All existing invariants (from `specs/008-game-import/data-model.md` section 4) hold. The only addition: when `refresh_covers` is true and a kept game's scanned counterpart has a non-`None` cover, the kept game's `cover` is set to it.
