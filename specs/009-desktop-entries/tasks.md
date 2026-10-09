---

description: "Task list for Desktop Entries (document source, fix broken icons, repair saved covers)"
---

# Tasks: Desktop Entries

**Input**: Design documents from `specs/009-desktop-entries/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/desktop-source.md](contracts/desktop-source.md), [quickstart.md](quickstart.md)

**Tests**: Included. The plan names `tests/test_desktop.py` (new) and additions to `tests/test_importer.py`. Tests follow the existing plain-script style: `check_*` functions run from an `if __name__ == "__main__":` block, with the `cartridges` package stubbed as in `tests/test_importer.py` (a `types.ModuleType("cartridges")` with `__path__`, `DATA_DIR` and `SETTINGS`). Use `_expect(actual, expected, what)` for assertions.

**Organization**: Tasks are grouped by user story so each story can be implemented and tested on its own.

**Legacy reference**: `~/Development/cartridges-main/cartridges/importer/desktop_source.py` is a behavior reference only. Do not copy its code (Constitution: Project Provenance).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: User story from spec.md (US1, US2, US3)
- Paths are relative to the repository root.

---

## Phase 1: Setup

**Purpose**: Branch, spec commit, and the bundled fallback asset

- [X] T001 Create branch `fix/009-desktop-entries` from `main` (Constitution: Development & Branching Workflow)
- [X] T002 Commit the spec documents in `specs/009-desktop-entries/` as the first commit on the branch, message `docs: add desktop entries spec (009)`
- [X] T003 [P] Copy the Adwaita icon `/usr/share/icons/Adwaita/scalable/mimetypes/application-x-executable.svg` (from the host or the GNOME 50 runtime) to `data/icons/application-x-executable.svg`, then run `svgo data/icons/application-x-executable.svg`
- [X] T004 Register the icon in `data/icons/icons.gresource.xml.in` as a new `<gresource prefix="@PREFIX@/fallback">` block containing `<file>application-x-executable.svg</file>`, after the existing blocks. Put an XML comment above it saying the file is a copy of the Adwaita icon theme's `application-x-executable`, licensed LGPL-3.0-only OR CC-BY-SA-3.0, and used as the default desktop entry icon when the icon theme lacks it. The comment goes here and not in the SVG because svgo strips SVG comments. Do NOT put it under an `icons/` prefix: it must not become a themed icon (research R-4)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared helpers used by more than one story

**CRITICAL**: US1 and US2 depend on this phase

- [X] T005 Add `custom(game_id: str) -> Gdk.Paintable | None` to `cartridges/cover.py` after `at_url`. Docstring: "Load the cover the user chose for the game with `game_id`, if any." Body: `return at_path(COVERS_DIR / f"{game_id}.gif") or at_path(COVERS_DIR / f"{game_id}.tiff")` (contract C-2)
- [X] T006 [P] Replace the inline `cover.at_path(f"{base}.gif") or cover.at_path(f"{base}.tiff")` lookup in `cartridges/sources/imported.py` with `cover.custom(game.game_id)`, and drop the now-unused `COVERS_DIR` import
- [X] T007 Add an optional `REFRESH_COVERS` attribute to the source module contract in `cartridges/sources/__init__.py`. Keep `_SourceModule` unchanged (a Protocol cannot declare an optional attribute) and read the flag with a typed helper `def _refreshes_covers(module: _SourceModule) -> bool: return bool(getattr(module, "REFRESH_COVERS", False))`, with a docstring explaining that a true value means "covers from this source are regenerated on every import instead of being kept" (data-model section 4)

**Checkpoint**: `pyright` and `ruff check` pass. Behavior is unchanged.

---

## Phase 3: User Story 1 - Desktop entry games show a usable icon (Priority: P1) MVP

**Goal**: No desktop entry game's cover ever shows GTK's `image-missing` icon. Real icons (theme name, `pixmaps`, file path) show. Everything else shows the default application icon.

**Independent Test**: Quickstart Scenarios 1, 2 and 5. Create the `cart-test-*.desktop` entries, import, and check each cover.

### Tests for User Story 1

- [X] T008 [US1] Create `tests/test_desktop.py`:
  - SPDX header `GPL-3.0-or-later`, `Copyright 2026 samuelm333`, and a module docstring.
  - Stub `cartridges` as in `tests/test_importer.py`. Also stub `cartridges.config` with `PREFIX = "/page/samuelm333/Cartridges/Test"`.
  - Import `cartridges.sources`, then patch `sources.DATA` and `sources.SYSTEM_DATA` to point into a `tempfile.mkdtemp()` tree before importing `cartridges.sources.desktop`.
  - Include a helper `_write_entry(name: str, **keys: str) -> Path` that writes `<tmp>/applications/<name>.desktop` with `[Desktop Entry]`, `Type=Application`, `Exec=true`, `Categories=Game;`, plus `keys`.
- [X] T009 [US1] Add icon-outcome checks to `tests/test_desktop.py`, one per row of contract C-1's icon table. Assert on the resolved source, not on pixels: call `desktop._icon(value)` and compare `paintable.get_file().get_path()` (for `Gtk.IconPaintable`) with the expected file:
  - `check_icon_missing_uses_default`
  - `check_icon_unknown_name_uses_default`
  - `check_icon_theme_name` (write a PNG into `<tmp>/icons/hicolor/48x48/apps/cart-test.png` using `PIL.Image.new("RGBA", (48, 48)).save(...)`)
  - `check_icon_name_with_extension` (`cart-test.png`)
  - `check_icon_pixmaps` (PNG in `<tmp>/pixmaps/cart-test-pixmap.png`)
  - `check_icon_path_valid`
  - `check_icon_path_missing_uses_default`
  - `check_icon_path_not_an_image_uses_default` (a file containing `not an image`)
  - `check_icon_never_image_missing`, which, for every case above, asserts the result is `None` or that its file path is not `None` and does not end with `image-missing.png`
  - `check_default_is_adwaita`, which asserts the default resolves to a path ending in `Adwaita/scalable/mimetypes/application-x-executable.svg`

### Implementation for User Story 1

- [X] T010 [US1] In `cartridges/sources/desktop.py`, add `pixmaps` to the entry icon search path, as legacy did (research R-1a, R-5). Change `_ICON_PATHS` to `tuple(path / sub for path in _DATA_PATHS for sub in ("icons", "pixmaps"))`. Keep `_icon_theme()` as an **unnamed** `Gtk.IconTheme()`, which is the legacy behavior. Fix the existing bug where `path not in search_path` compares a `Path` to `str` (convert before comparing)
- [X] T011 [US1] In `cartridges/sources/desktop.py`, add `_lookup(theme: Gtk.IconTheme, name: str) -> Gtk.IconPaintable | None`. It calls `theme.lookup_icon(name, fallbacks=None, size=cover.ICON_SIZE, scale=2, direction=Gtk.TextDirection.NONE, flags=Gtk.IconLookupFlags.NONE)` and returns the paintable only if `(file := icon.get_file()) is not None and file.get_path() is not None`, else `None`. Add a comment that GTK's own `image-missing` icon is a `resource://` file without a path, and that `fallbacks` must not be used because fallbacks found in a parent theme shadow real icons in hicolor (research R-2)
- [X] T012 [US1] In `cartridges/sources/desktop.py`, add `@functools.cache def _default_icon() -> Gdk.Paintable | None`. It returns, in order:
  1. `_lookup(Gtk.IconTheme(theme_name="Adwaita"), _ICON_FALLBACK)`
  2. the bundled resource, if `Gio.resources_get_info(path, Gio.ResourceLookupFlags.NONE)` succeeds for `path = f"{PREFIX}/fallback/{_ICON_FALLBACK}.svg"` (catch `GLib.Error`): `Gtk.IconPaintable.new_for_file(Gio.File.new_for_uri(f"resource://{path}"), cover.ICON_SIZE, 2)`
  3. `None`

  Import `PREFIX` from `cartridges.config`.
- [X] T013 [US1] In `cartridges/sources/desktop.py`, add `_file_icon(value: str) -> Gdk.Paintable | None`. Candidates are `(Path("/run/host", Path(value).relative_to("/")), Path(value))` when `Path("/.flatpak-info").exists()` and the value is absolute, else `(Path(value),)`. Return `Gtk.IconPaintable.new_for_file(Gio.File.new_for_path(str(candidate)), cover.ICON_SIZE, 2)` for the first candidate where `candidate.is_file()` and `Gdk.Texture.new_from_filename(str(candidate))` does not raise `GLib.Error`. Otherwise return `None` (research R-3)
- [X] T014 [US1] In `cartridges/sources/desktop.py`, add `_icon(value: str | None) -> Gdk.Paintable | None` implementing data-model section 3:
  - empty or `None` gives `_default_icon()`
  - a value containing `/` gives `_file_icon(value) or _default_icon()`
  - otherwise strip one trailing `.png`, `.svg` or `.xpm` (case-sensitive, as GLib does), then `_lookup(_icon_theme(), name) or _default_icon()`
- [X] T015 [US1] In `_game_from` in `cartridges/sources/desktop.py`, replace the `icon_name` / `lookup_icon(..., fallbacks=(_ICON_FALLBACK,), ...)` block. Read `Icon` with `suppress(GLib.Error)` into `icon_value: str | None`, then set `cover=cover.from_icon(icon) if (icon := _icon(icon_value)) else None` on the `Game`. Keep the existing comment about assuming 2x scaling next to the size and scale constants used by `_lookup`
- [X] T016 [US1] Run `python tests/test_desktop.py` (inside `gtk-dev`, or with `flatpak run --command=python3 page.samuelm333.Cartridges` from the repo root) and fix any failures until every check passes

**Checkpoint**: US1 is complete. New imports never show a broken icon (SC-001, SC-002).

---

## Phase 4: User Story 2 - Previously broken icons are repaired on the next import (Priority: P1)

**Goal**: Covers saved before the fix are replaced on the next import, by Import Now or at startup. Covers the user chose are kept.

**Independent Test**: Quickstart Scenarios 3 and 4.

### Tests for User Story 2

- [X] T017 [P] [US2] Add to `tests/test_importer.py`, following contract C-4's table (use small `Gdk.MemoryTexture` paintables or `object()`-distinct paintables from the existing test helpers as covers A and X):
  - `check_reconcile_refresh_covers_replaces_cover`: `refresh_covers=True`, existing A, scanned X, result X
  - `check_reconcile_refresh_covers_keeps_when_scan_has_none`: `refresh_covers=True`, existing A, scanned None, result A
  - `check_reconcile_without_refresh_keeps_cover`: the default, existing A, scanned X, result A (the existing `check_reconcile_fills_missing_cover_only` already covers None to X)
- [X] T018 [P] [US2] Add to `tests/test_importer.py`:
  - `check_scan_prefers_custom_cover`: write a 1x1 TIFF to `cover.COVERS_DIR / "<id>.tiff"` with PIL, and use a fake source module whose game has a scanned cover. Assert that after `Source.scan` the game's cover is a `_PILPaintable`, not the scanned one.
  - `check_scan_forgets_saved_cover_for_refresh_sources`: create `saved_library._cover_path("<id>")` as a file, and use a fake module with `REFRESH_COVERS = True`. Assert that after `list(source.scan(0))` the file is gone.
  - `check_scan_keeps_saved_cover_for_other_sources`: the same setup without the flag. Assert that the file remains.

### Implementation for User Story 2

- [X] T019 [US2] In `cartridges/importer.py`, add a keyword-only parameter `refresh_covers: bool = False` to `reconcile`. Change the cover merge to `if found.cover is not None and (refresh_covers or game.cover is None): game.cover = found.cover`. Extend the docstring: "With `refresh_covers`, the scanned cover replaces the existing one, for sources whose covers are cheap to regenerate."
- [X] T020 [US2] In `Source.replace_games` in `cartridges/sources/__init__.py`, pass `refresh_covers=_refreshes_covers(self._module)` to `reconcile`
- [X] T021 [US2] In `Source.scan` in `cartridges/sources/__init__.py`, before `self._track(game)`, so that no `notify::cover` is emitted:
  - add `game.cover = cover.custom(game.game_id) or game.cover`
  - add `if _refreshes_covers(self._module): saved_library.forget_cover(game.game_id)`

  Import `cover` from `cartridges`. Update the `scan` docstring to mention that a cover the user chose always wins (contract C-3, research R-6)
- [X] T022 [US2] Add `REFRESH_COVERS: Final = True` to `cartridges/sources/desktop.py` next to `ID, NAME`, with a one-line comment: "Covers are made from entry icons, so they are rebuilt on each import to pick up icon fixes." Import `Final` from `typing`
- [X] T023 [US2] Run `python tests/test_importer.py` and `python tests/test_saved_library.py` and fix any failures

**Checkpoint**: US1 and US2 both work. Existing users' broken icons are repaired after one import (SC-003), and custom covers survive (SC-004).

---

## Phase 5: User Story 3 - Games from desktop entries appear in the library (Priority: P2)

**Goal**: Lock in the documented baseline filtering and launch behavior (FR-001 to FR-011) with tests, so the icon changes cannot regress it.

**Independent Test**: `python tests/test_desktop.py` filtering checks pass, plus quickstart Scenario 6.

### Tests for User Story 3

- [X] T024 [P] [US3] Add filtering checks to `tests/test_desktop.py`, one per row of contract C-1's filtering table, calling `list(desktop.get_games())` after pointing `desktop._DESKTOP_PATHS` at the temp `applications` folders:
  - `check_requires_game_category`
  - `check_skips_nodisplay`
  - `check_skips_hidden`
  - `check_skips_blacklisted_file_name` (`net.lutris.foo.desktop`)
  - `check_skips_blacklisted_exec` (`Exec=steam://rungameid/1`)
  - `check_skips_x_flatpak`
  - `check_skips_missing_name`
  - `check_skips_unreadable_entry` (invalid key file content)
  - `check_first_location_wins` (the same file name in two folders; the first folder's `Name` is kept)
  - `check_game_fields`: `game_id == "desktop_<stem>"`, `source == "desktop"`, and `executable == f"gio launch {shlex.quote(str(path))}"`

  Skip `TryExec` here because it shells out through `games.format_executable`, and cover it in quickstart Scenario 6.

### Implementation for User Story 3

- [X] T025 [US3] Run the T024 checks against the current `cartridges/sources/desktop.py`. They document existing behavior and must pass without source changes. If one fails, fix the test unless the failure contradicts spec FR-001 to FR-011, in which case report it before changing `desktop.py`

**Checkpoint**: All stories are independently verified.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T026 [P] Optional cleanup (plan, Structure Decision): replace the duplicated `cover.at_path(f"{base}.gif") or cover.at_path(f"{base}.tiff")` with `cover.custom(game.game_id)` in `cartridges/application.py`, `cartridges/ui/preferences.py` and `cartridges/ui/cover_picker.py` (`self.game.game_id`)
- [X] T027 Run the quality gates (Constitution: Quality Gates): `pre-commit run --all-files`, `pyright`, `ruff check`, `meson setup _build -Dprofile=development` (if missing) and `ninja -C _build && ninja -C _build test` inside `gtk-dev`. Confirm that `_build` compiles the icons GResource with the new `fallback` prefix (`gresource list _build/data/icons/icons.gresource | grep fallback`)
- [ ] T028 Walk through quickstart Scenarios 1 to 6 in `specs/009-desktop-entries/quickstart.md` with `meson devenv -C _build cartridges`. Do Scenario 5 with the Devel Flatpak. Remove the test entries afterwards
  - Partly verified without the UI (2026-10-09): the real desktop source ran over this machine's six game entries, and each cover was rendered with `cover.save`. On `main`, all six were GTK's missing-image icon (the same 128x112 drawn area). With the fix, each shows its own icon. All six use `Icon=` file paths. The interactive scenarios (Import Now, restart, custom cover) still need a manual run.
- [X] T029 [P] Set `**Status**: Implemented` in `specs/009-desktop-entries/spec.md`, tick all tasks here, and confirm that no emoji appear in changed files (`python .specify/scripts/bash/check-emojis.py` if applicable)
- [X] T030 Commit the implementation on `fix/009-desktop-entries` with message `fix: Show the default icon for desktop entries with missing icons (009)` and the required co-author trailer

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: T001 is done. T002 comes next. T003 then T004 (same asset).
- **Phase 2 (Foundational)**: depends on Phase 1. T005 before T006. T007 is independent of T005 and T006, but in the same file as later US2 tasks.
- **Phase 3 (US1)**: depends on T004 (resource) and T005 is not needed. Tasks T010 to T015 all edit `cartridges/sources/desktop.py`, so they run sequentially. T008 and T009 are written first and fail until T015.
- **Phase 4 (US2)**: depends on T005 and T007. It can run alongside US1 except T022, which edits `desktop.py` and should follow T015.
- **Phase 5 (US3)**: depends on T008 (test scaffolding) only. It can run alongside US1 and US2.
- **Phase 6 (Polish)**: depends on all stories.

### User Story Dependencies

- **US1 (P1)**: independent; the MVP.
- **US2 (P1)**: independent in code. Its user-visible effect (repairing broken icons) only shows once US1 produces good covers.
- **US3 (P2)**: independent; tests only.

### Parallel Opportunities

- T003 runs alongside T005, T006 and T007.
- T017 and T018 (`tests/test_importer.py`) can be written while US1 is implemented in `desktop.py`.
- T019 (`importer.py`) and T020/T021 (`sources/__init__.py`) are different files from US1's work.
- T024 (`tests/test_desktop.py` filtering checks) can be written alongside T019 to T021.
- T026 and T029 are independent files.

---

## Parallel Example: User Story 2 alongside User Story 1

```text
Developer A (US1, sequential in desktop.py): T010 -> T011 -> T012 -> T013 -> T014 -> T015 -> T016
Developer B (US2): T017 + T018 (tests) -> T019 (importer.py) -> T020 + T021 (sources/__init__.py) -> wait for T015 -> T022 -> T023
Developer C (US3): T024 -> T025
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phases 1 and 2 (T002 to T007)
2. Phase 3 (T008 to T016)
3. Stop and validate quickstart Scenarios 1, 2 and 5. New imports have no broken icons.

### Incremental Delivery

1. US1: fixes new imports and installs.
2. US2: repairs existing users' saved covers and keeps custom covers across restarts.
3. US3: regression tests for the baseline.
4. Polish: quality gates, manual walkthrough, commit.

---

## Notes

- Do not pass `fallbacks` to `Gtk.IconTheme.lookup_icon` anywhere in `desktop.py`. That is the bug (research R-1, R-2).
- The entry icon theme stays unnamed. Only the default icon uses `theme_name="Adwaita"`.
- No library format change: `saved_library._VERSION` stays `1`.
- The legacy blurred-background cover style is out of scope (research R-6a).
