# Implementation Plan: Desktop Entries

**Branch**: `fix/009-desktop-entries` | **Date**: 2026-10-09 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/009-desktop-entries/spec.md`

## Summary

This plan documents the Desktop Entries source as it is and fixes broken-image icons on its covers. The root cause was confirmed in the Flatpak sandbox ([research.md](research.md) R-1). The rewrite added an `application-x-executable` fallback to the icon lookup, but the source's private, unnamed `Gtk.IconTheme` searches only hicolor, where that icon does not exist. The rewrite also dropped two upstream rules: icon values containing `/` are file paths, and `pixmaps` folders are searched. In all these cases GTK returns its built-in `image-missing` icon.

Upstream Cartridges `main` (R-1a) never showed broken icons. It looked up icons with no fallbacks and accepted a result only if it resolved to a real file path. Otherwise the game got no cover. This plan restores that approach and, as the spec requires, uses the default application icon where upstream showed no cover:
- Restore the legacy entry-icon lookup: the unnamed theme, `icons` plus `pixmaps` search paths, no `fallbacks`, and the "resolves to a real file path" check.
- Restore "`/` means a file path". Validate that the file loads, and try `/run/host` first inside Flatpak.
- Strip `.png`, `.svg` and `.xpm` from icon names, as GLib does.
- Default icon: `application-x-executable` from a separate Adwaita-named theme, then a bundled copy, then no cover.

Covers saved before the fix are repaired on the next import. Sources can opt in to cover refresh (`REFRESH_COVERS`), and only `desktop` does. Custom covers chosen by the user are applied during every scan, so they survive.

## Technical Context

**Language/Version**: Python 3.13 (GNOME 50 runtime)

**Primary Dependencies**: PyGObject, GTK 4.22 (`Gtk.IconTheme`, `Gtk.IconPaintable`, `Gdk.Texture`), GLib/Gio (`GLib.KeyFile`, `Gio.File`), Libadwaita (UI only, untouched)

**Storage**: Files. `DATA_DIR/library.json` and `DATA_DIR/library-covers/*.png` (saved library, unchanged format), `DATA_DIR/covers/<id>.tiff|.gif` (custom covers, unchanged)

**Testing**: Standalone scripts `python tests/test_*.py` with a stubbed `cartridges` package; `ninja -C _build test` for metadata; `pyright` (strict); `pre-commit run --all-files`

**Target Platform**: Linux desktop, Flatpak-first (GNOME 50 runtime), plus native builds

**Project Type**: Desktop application (GTK 4 / Libadwaita)

**Performance Goals**: Import of a typical desktop source (tens of entries) adds no noticeable time. One lookup or file load per entry; the default icon is resolved once and cached.

**Constraints**: The source must not depend on a display (Constitution II). Must work inside the Flatpak sandbox with host paths under `/run/host` (Constitution IV). No change to the saved library format.

**Scale/Scope**: About 4 Python modules touched, 1 new test file, 1 bundled SVG plus 1 GResource entry

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Strict typing and QA | Pass | New functions fully typed; `REFRESH_COVERS` typed `Final[bool]`; the `getattr` default on the module is typed through the `_SourceModule` protocol or a `cast`. Pre-commit, Pyright and Ruff are required before completion. |
| II. Modular game sources | Pass | Icon logic stays inside `sources/desktop.py`. Cover refresh is a declarative module flag, not a source-ID check in shared code. The source still uses a display-independent `Gtk.IconTheme` (as today), with no widgets. |
| III. Blueprint-driven UI | N/A | No UI changes. |
| IV. Libadwaita, HIG, sandbox | Pass | Host icons are reached through `/run/host` inside Flatpak, and missing files degrade to the default icon instead of failing. |
| V. Resource and asset sandboxing | Pass | The fallback SVG ships in the existing icons GResource under its own prefix. No new directories. Covers stay under `DATA_DIR`. |
| VI. Emoji-free | Pass | No emoji in code or docs. |
| Branching | Pass | Branch from `main` as `fix/009-desktop-entries`. |

**Post-design re-check**: Pass. No violations, so Complexity Tracking is empty.

## Project Structure

### Documentation (this feature)

```text
specs/009-desktop-entries/
├── spec.md
├── plan.md              # This file
├── research.md          # Phase 0: root cause and decisions R-1 to R-7
├── data-model.md        # Phase 1: entry fields, icon resolution, cover lifecycle
├── quickstart.md        # Phase 1: validation scenarios
├── contracts/
│   └── desktop-source.md
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 (/speckit-tasks)
```

### Source Code (repository root)

```text
cartridges/
├── cover.py                 # + custom(game_id)
├── importer.py              # reconcile(..., refresh_covers=False)
├── sources/
│   ├── __init__.py          # _SourceModule.REFRESH_COVERS; scan applies custom covers and
│   │                        #   forgets saved covers for refresh sources; replace_games passes flag
│   ├── desktop.py           # REFRESH_COVERS; legacy entry-icon lookup (icons + pixmaps,
│   │                        #   no fallbacks, real-path check); Adwaita theme for default only;
│   │                        #   _icon(value) -> name / path / default resolution
│   └── imported.py          # use cover.custom (dedupe)
data/icons/
├── application-x-executable.svg   # new: bundled copy of the Adwaita icon (LGPL-3.0 / CC-BY-SA-3.0)
└── icons.gresource.xml.in         # + <gresource prefix="@PREFIX@/fallback">
tests/
├── test_desktop.py          # new: contract C-1
└── test_importer.py         # + checks for C-3, C-4
```

**Structure Decision**: Single-project layout, as in the existing repository. All behavior changes are in `cartridges/sources/desktop.py`, with small, source-agnostic hooks in `sources/__init__.py`, `importer.py`, and `cover.py`. Replacing the other three copies of the custom-cover lookup (`application.py`, `ui/preferences.py`, `ui/cover_picker.py`) with `cover.custom` is optional cleanup that can be done in the same change.

## Implementation Notes

- **Icon resolution** (data-model section 3):
  - `desktop._icon(value: str | None) -> Gdk.Paintable | None` decides between name, path, and default.
  - `_default_icon()` is cached. It tries the theme icon, then the bundled resource, then `None`.
  - `_game_from` calls `cover.from_icon(icon)` only when an icon was found. Otherwise `cover` stays `None`.
- **Legacy reference**: `~/Development/cartridges-main/cartridges/importer/desktop_source.py` (upstream `main`, `d56323e`). It is a behavior reference only (Constitution: Project Provenance). Do not copy its code. Note that the constitution names `/var/home/samuel/Projects/cartridges-main`, but that path does not exist on this machine.
- **Out of scope**: legacy's blurred-background icon cover style (research R-6a).
- **Flatpak detection**: reuse the existing `Path("/.flatpak-info").exists()` idiom. Optionally expose it from `sources/__init__.py` as `IN_FLATPAK` so it is computed once; that name avoids the existing `FLATPAK` path constant.
- **Resource URI**: `f"resource://{PREFIX}/fallback/application-x-executable.svg"`. Check registration with `Gio.resources_get_info` (catch `GLib.Error`) before loading. Unit tests do not register resources.
- **Saved library**: no changes needed. `forget_cover` followed by the existing `request_save` writes the fresh PNG.
- **Ordering in `scan`**: apply `cover.custom` before `_track(game)`, so the change does not emit `notify::cover` and trigger a second save.

## Complexity Tracking

No Constitution violations to justify.
