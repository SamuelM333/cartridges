# Research: Game Import

**Feature**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md) | **Date**: 2026-10-08

Each section records one decision, why it was made, and what else was considered. Code references point at the state of `main` at `0e201b5`.

## 1. Where the import logic lives

**Decision**: Add a new module `cartridges/importer.py`. It holds the import-run state object, the async `import_games()` coroutine, and the pure reconciliation function. `cartridges/sources/__init__.py` keeps the `Source` list model and gains one method, `Source.replace_games()`, plus a shared helper for resolving install locations.

**Rationale**:
- `sources/__init__.py` discovers source modules with `pkgutil.iter_modules(__path__)`. Any new module inside `cartridges/sources/` (even a private `_import.py`) would be loaded and treated as a game source, so the import logic cannot live there as a separate file.
- Keeping reconciliation as a pure function on lists of `Game` makes it unit-testable without GTK widgets, matching the stubbed-package style of `tests/test_play_history.py`.
- Principle II: source modules stay focused on discovery. They read their own settings (the Flatpak source already does), but they do not know about import runs, toasts, or the UI.

**Alternatives considered**:
- Put everything in `application.py`: mixes app lifecycle with library logic and is hard to test.
- Put everything in `sources/__init__.py`: possible, but the module would grow an async coroutine and run state on top of the list model; a separate module reads better.

## 2. How a re-scan updates the library

**Decision**: Reconcile by `game_id`, per source, keeping existing `Game` objects:
- A `game_id` present before and after: keep the existing object. Update only launcher-derived fields that cannot hold user edits: `last_played` becomes the max of the old value, the new launcher value, and play history; `cover` is taken from the new scan only if the existing game has none.
- A `game_id` that is new: append it. Its `added` defaults to the import time (same rule as startup, FR-004).
- A `game_id` that is gone: remove it from the source (FR-016, uninstalled games disappear).

The change is applied to each source with one `items_changed` emission that covers the removed and appended items.

**Rationale**:
- Keeping objects means an open game details page, a running cover fetch, a collection membership, and in-session `hidden`/`removed`/edited values all survive (spec edge cases "import while editing" and "user state across re-import").
- Launcher games are not persisted (`Game.save()` is only called for `imported` games), so in-memory objects are the only place user state lives during a session. Replacing objects would silently lose it.
- One `items_changed` per source keeps the `Gtk.FlattenListModel` -> `FilterListModel` -> `SortListModel` chain in `ui/games.py` from re-sorting once per game.

**Alternatives considered**:
- Rebuild each `Source` from scratch (`splice` the whole list): simplest, but drops user state and invalidates any view holding a `Game`.
- Update every property of existing games from the new scan: would overwrite in-session edits to name, executable, developer, and hidden.

## 3. Manually added games during Import Now

**Decision**: Skip the `imported` source during Import Now. It is loaded once at startup, always, regardless of `import-on-startup`.

**Rationale**: Manually added games are owned by Cartridges and saved on every edit, so the in-memory list is already authoritative. Re-reading them cannot find anything new and risks undoing in-session state (FR-011).

**Alternatives considered**: Re-reading `imported_*.json` would only matter if another process wrote game files while Cartridges runs, which is not a supported workflow.

## 4. Keeping the interface responsive during Import Now

**Decision**: Run the scan as an asyncio task on the GLib main loop (`Gio.Application.create_asyncio_task`, already used in `application.py`). Iterate each source's generator on the main thread and yield to the loop with `await asyncio.sleep(0)` after every 25 games and between sources. Apply each source's reconciliation as soon as that source finishes.

**Rationale**:
- Several sources are not safe to run off the main thread: `desktop.py` and `flatpak.py` query a `Gtk.IconTheme`; `itch.py` and `legendary.py` call `app.create_asyncio_task()` for cover downloads, which must happen on the loop thread. Moving them to a worker thread would need per-source changes and locking.
- Source generators are already lazy (`yield` per game), so cooperative yielding needs no change inside the sources.
- Applying per source gives the user visible progress and bounds the work done between yields.

**Risk**: Steam parses `appinfo.vdf` in one call before the first `yield`. On very large Steam libraries this single step may block the loop for longer than the SC-002 budget of 250 ms. Quickstart Scenario 7 measures it. If it exceeds the budget, the follow-up is to move only the `appinfo.vdf` parse into `asyncio.to_thread`, since it touches no GTK objects. This is noted, not pre-built.

**Alternatives considered**:
- Whole scan in `asyncio.to_thread`: rejected for the thread-safety reasons above.
- Keep the scan synchronous, like startup: freezes the Preferences dialog, violating FR-009.

## 5. Startup scan

**Decision**: Startup stays synchronous, as today, when `import-on-startup` is on. When it is off, every source except `imported` starts with an empty list.

**Rationale**: SC-005 requires no regression in startup behavior. Making startup asynchronous would change when the first window frame shows games, which is out of scope. The sidebar already hides sources with zero items (`SourceSidebarItem` binds `visible` to `n-items`), so empty sources disappear without extra code.

## 6. Which failures count as "source cannot be read"

**Decision**: Treat `OSError` and `sqlite3.Error` raised while reading a source as "no games from this source" (FR-005). In Import Now, a source that fails keeps its previous games unchanged instead of having them all removed.

**Rationale**:
- Today `Source.__init__` only catches `OSError`. Lutris and itch read SQLite databases; a locked or corrupt database raises `sqlite3.Error`, which currently would crash startup.
- During Import Now, a temporary failure (for example, a launcher holding a database lock while it updates) should not make every game from that launcher vanish. Removing games is reserved for a successful scan that no longer lists them.

**Alternatives considered**: Catching `Exception` would hide programming errors and fails Ruff `BLE001` (Principle I).

## 7. Honoring the enable switch for each source

**Decision**: Check the enable switch centrally, in `Source`, before calling the module's `get_games()`. The GSettings key equals the source `ID` (`steam`, `lutris`, `heroic`, `itch`, `legendary`, `desktop`, `flatpak`). The `imported` source has no key and is always enabled. Remove the now-redundant check at the top of `flatpak.get_games()`.

**Rationale**: One check covers all seven sources (FR-013) and source modules do not each need the same three lines. Key names already match IDs.

## 8. Honoring install locations

**Decision**: Add a helper in `sources/__init__.py`:

```text
location(key, candidates) -> Path
  if the user has set `key` (SETTINGS.get_user_value(key) is not None): return that path, expanded
  else: return the first existing directory among `candidates` (today's auto-detection)
  raise FileNotFoundError if nothing matches
```

Steam, Lutris, Heroic, itch, and Legendary replace their `_data_dir()` / `_config_dir()` lookups with this helper. Flatpak keeps reading its two location keys directly, as it does today.

**Rationale**:
- FR-014: a location the user picked in Preferences is used, strictly.
- SC-005: the schema defaults do not match the auto-detected paths for most users (for example `lutris-location` defaults to the Flatpak Lutris path, while native Lutris lives in `~/.local/share/lutris`). Reading the default value strictly would hide games that load today. Using the default only through auto-detection keeps current behavior for users who never changed it.
- `get_user_value()` distinguishes "never set" from "set to the same string as the default", so a user who explicitly picks the default path still gets it strictly.
- Preferences already validates a chosen folder (`_LOCATION_VALIDATION` in `ui/preferences.py`), so a user-set path is known to have the expected files at the time it was chosen.

**Alternatives considered**:
- Always read the setting value: regression for native installs.
- Change schema defaults to empty strings: changes how the Preferences rows display the current location, and is a larger UI change.

## 9. Honoring sub-options

**Decision**:
- **Lutris**: remove the two `runner IS NOT` conditions from the SQL query and filter in Python: drop rows with runner `steam` unless `lutris-import-steam` is on, and rows with runner `flatpak` unless `lutris-import-flatpak` is on. Both default to off, so default behavior is unchanged.
- **Heroic**: map each store class to its key before iterating: `_LegendarySource` -> `heroic-import-epic`, `_GOGSource` -> `heroic-import-gog`, `_NileSource` -> `heroic-import-amazon`, `_SideloadSource` -> `heroic-import-sideload`. All default to on.
- **Flatpak**: already honors `flatpak-import-launchers` and its two locations; no change.

**Rationale**: FR-015, with defaults chosen so users who never touched these switches see the same games as today (SC-005).

## 10. Settings changes ("Remove Uninstalled Games", "Import Games on Startup")

**Decision**:
- Delete the `remove-missing` key from the schema, its switch from `preferences.blp`, its entry in `_bind_switches`, its `Gtk.Template.Child`, and its expected entry in `tests/test_settings.py`.
- Replace the `auto-import` key with a new key `import-on-startup` (boolean, default `true`). Rename the switch to `import_on_startup_switch` with title "Import Games on Startup". The existing `_bind_switches` loop derives the widget name from the key, so it binds automatically once the key is listed.

**Rationale**:
- Clarification Q1 (B): the switch goes; uninstalled games always disappear.
- Clarification Q2 (A): the switch gates the startup scan, under a new name.
- A new key name is used instead of renaming the title only, because the default flips from `false` to `true` (FR-018). Reusing `auto-import` would keep any stored `false` value from users who toggled the old, ineffective switch, and those users would lose their launcher games on next start. Stale `auto-import` and `remove-missing` values in dconf are ignored by GSettings once the keys leave the schema (spec edge case).

## 11. Where the Import Now trigger lives

**Decision**: Register an application action `app.import` in `Application.do_startup`. The Preferences button uses `action-name: "app.import"`. The action is disabled while an import runs. When the run finishes, the application sends the result toast to the active window and, if SteamGridDB is enabled, fetches covers for the newly found games only.

**Rationale**:
- Constitution IV.6 prefers `Gio.ActionMap` actions. Disabling the action automatically makes the button insensitive (FR-008).
- Owning the run in the application rather than the Preferences dialog means closing Preferences does not cancel the import, and the toast still appears (spec edge case).
- Reusing the existing startup SteamGridDB cover logic for new games covers the "cover art" edge case. `_auto_fetch_sgdb_covers` is refactored to take the list of games to process.

**Alternatives considered**: A `clicked` handler in `preferences.py` that runs the import itself (the "Update Covers" pattern): the run would be tied to the dialog's lifetime.

## 12. Progress display

**Decision**: An `Adw.ActionRow` titled "Import Now" at the top of the Import page, in its own untitled `Adw.PreferencesGroup` above Behavior. Its suffix is a `Gtk.Stack` with an "Import" button and an `Adw.Spinner`, the same structure as the existing "Update Covers" row. The stack's visible child follows a boolean `running` property on the importer state object.

**Rationale**: Matches the existing in-app precedent (Constitution IV.5: spinner embedded in the action row) and keeps the two long-running Preferences actions consistent. A per-source progress bar is not needed: a typical import finishes within seconds (SC-002).

## 13. Result toast wording

**Decision**:
- At least one new game: `ngettext("{} new game imported", "{} new games imported", n).format(n)`
- None: `_("No new games found")`

Both get `Translators:` comments. The strings live in `cartridges/application.py`, which formats the toast from the count `import_games()` returns; that file is already in `po/POTFILES.in`. `cartridges/importer.py` has no user-visible strings, so it is not added there.

**Rationale**: FR-010. `ngettext` is required for correct plural forms; f-strings and concatenation are not used (same rules as feature 005).
