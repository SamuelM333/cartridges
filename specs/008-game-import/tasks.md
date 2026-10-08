---

description: "Task list for Game Import (Import Now, startup import setting, honoring import settings)"
---

# Tasks: Game Import

**Input**: Design documents from `specs/008-game-import/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/ui-contracts.md](contracts/ui-contracts.md), [quickstart.md](quickstart.md)

**Tests**: Included. The plan names `tests/test_importer.py` (new) and an update to `tests/test_settings.py`. Tests follow the existing plain-script style: `check_*` functions run from an `if __name__ == "__main__":` block, with the `cartridges` package stubbed as in `tests/test_play_history.py`.

**Organization**: Tasks are grouped by user story so each story can be implemented and tested on its own.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: User story from spec.md (US1, US2, US3)
- Paths are relative to the repository root.

---

## Phase 1: Setup

**Purpose**: Branch and new-module scaffolding

- [X] T001 Create branch `feat/008-game-import` from `main` (Constitution: Development & Branching Workflow) and commit the spec documents in `specs/008-game-import/` as the first commit
- [X] T002 Create `cartridges/importer.py` with the SPDX header (`GPL-3.0-or-later`, `Copyright 2026 samuelm333`) and a module docstring only, and add `'importer.py'` to the `python.install_sources(files(...))` list in `cartridges/meson.build` (alphabetical, after `'games.py'`, before `'play_history.py'`, matching the existing order)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Refactor `Source` so both startup and Import Now go through the same scan path. Behavior stays the same as on `main`.

**CRITICAL**: No user story work can begin until this phase is complete.

- [X] T003 In `cartridges/sources/__init__.py`, rename `Source._get_games(self, added)` to a public `Source.scan(self, added: int) -> Generator[Game]` with the same body (play-history `max()` merge and `game.added = game.added or added`), and update the call in `Source.__init__`
- [X] T004 In `cartridges/sources/__init__.py`, widen the `except OSError:` around the initial scan in `Source.__init__` to `except (OSError, sqlite3.Error):` (add `import sqlite3`), so a locked or corrupt Lutris/itch database yields zero games instead of crashing startup (FR-005, research section 6)

**Checkpoint**: The app starts and shows the same library as on `main`. `pyright` and `ruff check` pass.

---

## Phase 3: User Story 1 - Import games on demand from Preferences (Priority: P1) MVP

**Goal**: An "Import Now" row at the top of Preferences > Import re-scans all sources (except manually added games) without restarting, shows a spinner while running, and reports new games in a toast.

**Independent Test**: With Cartridges running, add a `.desktop` game entry in `~/.local/share/applications/`, open Preferences > Import, press Import, and confirm the game appears and a toast says "1 new game imported" (quickstart Scenarios 1 to 3).

### Tests for User Story 1

> Write these first. They must fail (import error or assertion) before T007 to T009 are done.

- [X] T005 [P] [US1] Create `tests/test_importer.py`:
  - Stub the `cartridges` package the way `tests/test_play_history.py` does, providing `DATA_DIR` (temp dir) and a `SETTINGS` stand-in object with `get_boolean`. Then import `cartridges.games` and `cartridges.importer`.
  - Add these `reconcile()` checks against data-model.md section 4:
    - `check_reconcile_adds_new`: scanned ids not in existing go to `added`, in scan order.
    - `check_reconcile_removes_missing`: existing ids not in scanned go to `removed`.
    - `check_reconcile_keeps_objects`: `kept` items are the original objects (`is`), in existing order.
    - `check_reconcile_preserves_user_fields`: an existing game with an edited `name`, `executable`, `developer`, `hidden=True`, `removed=True` and a custom `added` keeps all of them.
    - `check_reconcile_merges_last_played`: `last_played` becomes `max(existing, scanned)`.
    - `check_reconcile_fills_missing_cover_only`: the cover is taken from the scan only if the existing `cover` is `None`.
    - `check_reconcile_dedupes_scan`: a scan yielding the same `game_id` twice keeps the first, so `kept + added` has no duplicate `game_id`.
    - `check_reconcile_idempotent`: reconciling `kept + added` with the same scan again gives `added == []` and `removed == []` (SC-003).
  - Call all checks from `if __name__ == "__main__":`.

### Implementation for User Story 1

- [X] T006 [US1] In `cartridges/importer.py`, implement `class Reconciliation(NamedTuple)` with fields `kept: list[Game]`, `added: list[Game]` and `removed: list[Game]`, and `reconcile(existing: Sequence[Game], scanned: Iterable[Game]) -> Reconciliation`, following data-model.md sections 2 and 4:
  - Key games by `game_id`.
  - Keep the existing objects; set `last_played = max(existing.last_played, scanned.last_played)`; copy `cover` only when the existing `cover is None`; leave every other field untouched.
  - The first occurrence of a duplicate scanned `game_id` wins.

  Fully typed, no `Any`.
- [X] T007 [US1] In `cartridges/sources/__init__.py`, add `Source.replace_games(self, games: list[Game]) -> list[Game]`:
  - Call `importer.reconcile(self._games, games)`.
  - Set `self._games = kept + added`.
  - Emit exactly one `self.items_changed(0, old_len, new_len)` if anything was added or removed, and none otherwise.
  - Return `added`.

  To avoid an import cycle, import `reconcile` inside the method or have `importer.py` import `sources` lazily; `importer.py` must import `Game` from `cartridges.games` only.
- [X] T008 [US1] In `cartridges/importer.py`, implement the import run (data-model.md section 3, contracts section 3, research section 4):
  - `class ImportState(GObject.Object)` with `__gtype_name__ = __qualname__` and `running = GObject.Property(type=bool, default=False)`, plus a module-level `state = ImportState()`.
  - `async def import_games() -> list[Game]`:
    - Set `state.running = True`; take `added = int(time.time())`.
    - For each `Source` in `sources.model` whose `id != "imported"`, iterate `source.scan(added)` into a list, calling `await asyncio.sleep(0)` after every 25 games.
    - On `(OSError, sqlite3.Error)`, leave that source unchanged and continue.
    - Otherwise call `source.replace_games(scanned)` and extend the result list with the returned games.
    - Call `await asyncio.sleep(0)` between sources.
    - Reset `state.running = False` in a `finally` block.
    - Return the newly added games.
- [X] T009 [US1] In `cartridges/application.py`, refactor `_auto_fetch_sgdb_covers(self)` to `_auto_fetch_sgdb_covers(self, games: Iterable[Game])` so it only processes the given games, and have `_check_auto_fetch_sgdb_covers` take and forward that list. The startup call passes every game from every source, exactly as it iterates today, so startup behavior is unchanged.
- [X] T010 [US1] In `cartridges/application.py`, register the `app.import` action (contracts section 2):
  - Create a `Gio.SimpleAction(name="import")` in `do_startup` and bind `importer.state` `running` to the action's `enabled` property with an inverting transform (`SYNC_CREATE`).
  - On activate, call `self.create_asyncio_task(self._import())`.
  - `async def _import(self) -> None` awaits `importer.import_games()`, then sends a toast to `self.props.active_window` if it is a `Window`, via `window.send_toast(...)`:
    - `n > 0`: `ngettext("{} new game imported", "{} new games imported", n).format(n)`, preceded by `# Translators: {} is the number of games that were imported`.
    - `n == 0`: `_("No new games found")`.
  - Then it calls `_check_auto_fetch_sgdb_covers(new_games)`.
  - Do not add a keyboard accelerator.
- [X] T011 [US1] In `cartridges/ui/preferences.blp`, add a new untitled `Adw.PreferencesGroup` as the first child of `import_page`, above `import_behavior_group`, containing:
  - `Adw.ActionRow import_now_row` with title `_("Import Now")` and subtitle `_("Scan your sources for new and uninstalled games")`.
  - A suffix `Stack import_stack` holding `Button import_button` (`label: _("Import")`, `valign: center`, `action-name: "app.import"`) and `Adw.Spinner import_spinner` (`valign: center`).

  Mirror the structure of the existing "Update Covers" row (`sgdb_stack`) in the same file.
- [X] T012 [US1] In `cartridges/ui/preferences.py`, add the template children `import_stack: Gtk.Stack`, `import_button: Gtk.Button` and `import_spinner: Adw.Spinner`. In `__init__`, bind `importer.state` `running` to `import_stack` `visible-child` with a transform (`True` -> `import_spinner`, `False` -> `import_button`) and `GObject.BindingFlags.SYNC_CREATE`, so reopening Preferences mid-import shows the spinner.
- [X] T013 [US1] Verify US1 with quickstart Scenarios 1, 2 and 3 (new game appears; button disabled and spinner while running; toast still shows after closing Preferences; 10 repeated imports give no duplicates and keep hidden/edited state; "Added" games untouched) and `python tests/test_importer.py`.

**Checkpoint**: Import Now works end to end. The main window "+" button still runs `game.add` only (FR-012; no change needed in `cartridges/ui/window.blp`).

---

## Phase 4: User Story 2 - Library is populated at startup, gated by "Import Games on Startup" (Priority: P1)

**Goal**: Startup behavior is preserved with default settings, and the renamed "Import Games on Startup" switch (default on) skips launcher scanning when off.

**Independent Test**: Reset settings, confirm the switch is on and startup shows all launcher games. Turn it off, restart, and confirm only manually added games show until Import Now is pressed (quickstart Scenarios 5 and 9).

### Tests for User Story 2

- [ ] T014 [P] [US2] In `tests/test_settings.py`, remove `"remove-missing"` from `expected_keys` and add `"import-on-startup": "b"`. Add a check that the schema has no `auto-import` key and that `import-on-startup` defaults to `true` (`schema.get_key("import-on-startup").get_default_value().get_boolean()`).

### Implementation for User Story 2

- [ ] T015 [US2] In `data/page.samuelm333.Cartridges.gschema.xml.in`, replace the `auto-import` key with `<key name="import-on-startup" type="b"><default>true</default></key>` at the same position (FR-017, FR-018; research section 10 explains why a new key name is used)
- [ ] T016 [US2] In `cartridges/sources/__init__.py`, gate the initial scan in `Source.__init__`. Scan only when `module.ID == "imported"` or `SETTINGS.get_boolean("import-on-startup")`; otherwise start with `self._games = []` (data-model.md section 1, "Initial load" table). Import `SETTINGS` from `cartridges`.
- [ ] T017 [US2] In `cartridges/ui/preferences.blp`, rename `Adw.SwitchRow auto_import_switch` to `import_on_startup_switch` with title `_("Import Games on Startup")`. In `cartridges/ui/preferences.py`, rename the template child to `import_on_startup_switch` and replace `"auto-import"` with `"import-on-startup"` in the `_bind_switches` key set.
- [ ] T018 [US2] Verify US2 with quickstart Scenario 5 (default on; off -> only "Added" games and launcher sources absent from the sidebar; Import Now restores them; back on -> startup import returns) and Scenario 9 (same games, counts and launcher-reported last-played values as `main`), and run `ninja -C _build test` plus `python tests/test_settings.py`.

**Checkpoint**: US1 and US2 both work. Defaults match `main`.

---

## Phase 5: User Story 3 - Import preferences control what is imported (Priority: P2)

**Goal**: Every enable switch, user-set install location and sub-option on the Import page affects the next import, and "Remove Uninstalled Games" is gone.

**Independent Test**: Turn Steam off, press Import Now, and confirm Steam games and the Steam sidebar entry disappear; turn it back on and import again to bring them back. Repeat for each row of quickstart Scenario 6.

### Tests for User Story 3

- [ ] T019 [P] [US3] In `tests/test_importer.py`, add `location()` checks against data-model.md section 6 using a `SETTINGS` stand-in whose `get_user_value(key)` returns `None` or a `GLib.Variant("s", path)`, and `get_string`:
  - `check_location_user_set_is_strict`: a user-set path is returned expanded, even if it does not exist.
  - `check_location_default_autodetects`: with no user value, the first existing candidate directory is returned.
  - `check_location_none_found`: with no user value and no existing candidate, `FileNotFoundError` is raised.

  Import `location` from `cartridges.sources`. If importing the real package needs more stubs (`GLib` user dirs), stub only what `sources/__init__.py` touches at import time.

### Implementation for User Story 3

- [ ] T020 [US3] In `cartridges/sources/__init__.py`, add `location(key: str, candidates: Iterable[Path]) -> Path`:
  - If `SETTINGS.get_user_value(key) is not None`, return `Path(SETTINGS.get_string(key)).expanduser()`.
  - Otherwise return the first `p` in `candidates` with `p.is_dir()`.
  - Otherwise raise `FileNotFoundError`.

  (research section 8)
- [ ] T021 [US3] In `cartridges/sources/__init__.py`, make `Source.scan()` yield nothing when the source is disabled: `self.id != "imported" and not SETTINGS.get_boolean(self.id)` (FR-013, research section 7). In `cartridges/sources/flatpak.py`, remove the now-redundant `if not SETTINGS.get_boolean("flatpak"): return` at the top of `get_games()`.
- [ ] T022 [US3] In `cartridges/importer.py`, make sure a disabled source is reconciled against an empty list so its games disappear on Import Now. If T021 already makes `scan()` yield nothing, no extra code is needed; confirm with quickstart Scenario 6 "Steam off".
- [ ] T023 [P] [US3] In `cartridges/sources/steam.py`, change `_data_dir()` to `return location("steam-location", _DATA_PATHS)`; import `location` from `.`.
- [ ] T024 [P] [US3] In `cartridges/sources/lutris.py`:
  - Change `_data_dir()` to `return location("lutris-location", _DATA_PATHS)`.
  - Remove the `AND games.runner IS NOT "steam"` and `AND games.runner IS NOT "flatpak"` lines from `_QUERY`.
  - In `get_games()`, skip rows whose runner (`row[3]`) is `"steam"` unless `SETTINGS.get_boolean("lutris-import-steam")`, and rows whose runner is `"flatpak"` unless `SETTINGS.get_boolean("lutris-import-flatpak")`. Both keys default to `false`, so default output is unchanged.

  Import `SETTINGS` from `cartridges`.
- [ ] T025 [P] [US3] In `cartridges/sources/heroic.py`:
  - Change `_config_dir()` to `return location("heroic-location", _CONFIG_PATHS)`.
  - In `get_games()`, iterate `(_LegendarySource, "heroic-import-epic")`, `(_GOGSource, "heroic-import-gog")`, `(_NileSource, "heroic-import-amazon")` and `(_SideloadSource, "heroic-import-sideload")`, and skip a store when `SETTINGS.get_boolean(key)` is false.

  Import `SETTINGS` from `cartridges`.
- [ ] T026 [P] [US3] In `cartridges/sources/itch.py`, change `_config_dir()` to `return location("itch-location", _CONFIG_PATHS)`.
- [ ] T027 [P] [US3] In `cartridges/sources/legendary.py`, change `_config_dir()` to `return location("legendary-location", (_CONFIG_PATH,))`.
- [ ] T028 [US3] Remove "Remove Uninstalled Games" (FR-016):
  - Delete the `remove-missing` key from `data/page.samuelm333.Cartridges.gschema.xml.in`.
  - Delete `Adw.SwitchRow remove_missing_switch` from `cartridges/ui/preferences.blp`.
  - Delete the `remove_missing_switch` template child and the `"remove-missing"` entry in `_bind_switches` from `cartridges/ui/preferences.py`.
  - In `tests/test_settings.py`, add a check that the schema has no `remove-missing` key.
- [ ] T029 [US3] Verify US3 with quickstart Scenario 4 (uninstalled game disappears; no "Remove Uninstalled Games" switch), Scenario 6 (every row of the settings table) and Scenario 8 (an unreadable `pga.db` leaves Lutris games unchanged while other sources import), and run `python tests/test_importer.py`.

**Checkpoint**: All Import settings have an observable effect (SC-004).

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T030 Measure responsiveness with quickstart Scenario 7 on the largest available Steam library. If any main-loop stall exceeds 250 ms, move only the `_parse_appinfo_vdf` call in `cartridges/sources/steam.py` behind `asyncio.to_thread` as described in research.md section 4, and record the measured durations in that section.
- [ ] T031 [P] Run `ninja -C _build cartridges-pot`. Confirm `po/cartridges.pot` contains "Import Now", "Scan your sources for new and uninstalled games", "Import", "Import Games on Startup", the plural pair "{} new game imported"/"{} new games imported" with its translator comment, and "No new games found", and no longer contains "Remove Uninstalled Games" or "Import Games Automatically".
- [ ] T032 Run the full quality gate from the constitution: `pre-commit run --all-files`, `pyright`, `ruff check`, `blueprint-compiler` compile of `cartridges/ui/preferences.blp`, `meson setup _build` and `ninja -C _build test`, and `python3 .specify/scripts/bash/check-emojis.py` on all changed files. Fix any findings.
- [ ] T033 Run the whole of `specs/008-game-import/quickstart.md` once more end to end on a fresh settings profile (`gsettings reset-recursively`) and tick the spec checklist.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup. Blocks all stories (every story uses `Source.scan()`).
- **US1 (Phase 3)**: Depends on Foundational.
- **US2 (Phase 4)**: Depends on Foundational. Its test step (T018) uses Import Now, so finish US1 first if you want to run Scenario 5 fully; T014 to T017 can be done without US1.
- **US3 (Phase 5)**: Depends on Foundational. T022 and T029 need US1's `import_games()`. T028 edits the same schema, Blueprint and Python files as T015 and T017, so do it after US2.
- **Polish (Phase 6)**: Depends on all stories.

### Within Each Story

- Tests (T005, T014, T019) first; they must fail before implementation.
- US1: T006 (reconcile) -> T007 (`replace_games`) -> T008 (`import_games`) -> T009, T010 (application) -> T011, T012 (UI) -> T013.
- US3: T020 (`location`) before T023 to T027. T021 before T022.

### Parallel Opportunities

- T005 can be written while T003/T004 are in progress (new file).
- T014 (test file) in parallel with T015 (schema).
- T023, T024, T025, T026 and T027 each touch a different source module and can run in parallel once T020 is done.
- T031 in parallel with T030.

---

## Parallel Example: User Story 3

```bash
# After T020 (location helper) is in place:
Task: "T023 steam.py: _data_dir() uses location('steam-location', _DATA_PATHS)"
Task: "T024 lutris.py: location + runner sub-options"
Task: "T025 heroic.py: location + store sub-options"
Task: "T026 itch.py: _config_dir() uses location('itch-location', _CONFIG_PATHS)"
Task: "T027 legendary.py: _config_dir() uses location('legendary-location', (_CONFIG_PATH,))"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 Setup, Phase 2 Foundational.
2. Phase 3 (US1): Import Now with reconciliation, action, toast and spinner.
3. Stop and validate with quickstart Scenarios 1 to 3. This alone removes the need to restart to pick up new games.

### Incremental Delivery

1. Setup + Foundational: same behavior as `main`, cleaner scan path.
2. US1: Import Now (MVP).
3. US2: "Import Games on Startup" replaces the dead "Import Games Automatically" switch.
4. US3: all source settings take effect; "Remove Uninstalled Games" removed.
5. Polish: responsiveness measurement, translations, quality gate.

Commit after each task or logical group, using the branch `feat/008-game-import`.

---

## Notes

- [P] tasks touch different files and have no dependency on an incomplete task.
- Keep source modules free of UI imports (Principle II); they may read `SETTINGS` only.
- Do not use upstream pre-rewrite Cartridges code as a reference for the import logic (Constitution: Project Provenance).
