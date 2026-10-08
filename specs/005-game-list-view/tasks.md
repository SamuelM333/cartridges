# Tasks: Main Game List View and Cover Interactions

**Feature**: Main Game List View and Cover Interactions
**Branch**: `feat/005-game-list-view`
**Spec**: [specs/005-game-list-view/spec.md](file:///var/home/samuel/Projects/cartridges/specs/005-game-list-view/spec.md)
**Plan**: [specs/005-game-list-view/plan.md](file:///var/home/samuel/Projects/cartridges/specs/005-game-list-view/plan.md)

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify development environment, build tools, and baseline templates.

- [X] T001 Verify GTK4/Libadwaita build environment and meson setup in `_build/`
- [X] T002 [P] Verify pre-commit formatting and linting configuration in `.pre-commit-config.yaml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core UI structure and stylesheet preparation required before individual user stories.

- [X] T003 Update hover button transform animations for top-corner overlay buttons in `cartridges/ui/style.css`
- [X] T004 Restructure `cartridges/ui/game-item.blp` overlay to position the circular action button at top-left (`margin: 6px`, `halign: start`, `valign: start`) and menu button at top-right (`margin: 6px`, `halign: end`, `valign: start`)

**Checkpoint**: Foundation ready - game card layout and styling established for user story behaviors.

---

## Phase 3: User Story 1 - Browse and Launch Games from Grid (Priority: P1) [MVP]

**Goal**: Restore top-left hover Play button and cover click activation for default configuration.

**Independent Test**: Hovering over a game card reveals the top-left circular Play button (`media-playback-start-symbolic`). Clicking Play launches the game; clicking the cover directly opens game details.

### Implementation for User Story 1

- [X] T005 [US1] Update `cartridges/ui/game_item.py` template children mapping to replace `play` with `action_button`
- [X] T006 [US1] Implement default Play button icon, tooltip (`Play`), and action (`game.play`) in `cartridges/ui/game_item.py`
- [X] T007 [US1] Implement pointer motion hover reveal logic for `action_button` in `cartridges/ui/game_item.py`
- [X] T008 [US1] Verify cover click activation in `cartridges/ui/window.py` navigates to game details when `cover-launches-game` is false

**Checkpoint**: User Story 1 MVP fully functional and independently testable.

---

## Phase 4: User Story 2 - Invert Cover and Button Behavior via Settings Toggle (Priority: P1)

**Goal**: Invert cover click and hover action button behaviors when "Cover Image Launches Game" is enabled.

**Independent Test**: When "Cover Image Launches Game" is toggled in Preferences, the top-left hover button immediately swaps to an Info icon (`help-about-symbolic`) with tooltip "Details", clicking it opens details, and clicking the cover directly launches the game.

### Implementation for User Story 2

- [X] T009 [US2] Connect `SETTINGS.connect("changed::cover-launches-game", ...)` in `cartridges/ui/game_item.py` to trigger dynamic button state updates
- [X] T010 [US2] Implement inverted Info button state (`help-about-symbolic`, tooltip `Details`, action `game.details`) when `cover-launches-game` is true in `cartridges/ui/game_item.py`
- [X] T011 [US2] Verify cover click activation in `cartridges/ui/window.py` launches game directly when `cover-launches-game` is true

**Checkpoint**: User Stories 1 and 2 independently functional; dynamic toggle operates cleanly in runtime.

---

## Phase 5: User Story 3 - Access Game Context Menu via Hover Three-Dots Button (Priority: P2)

**Goal**: Ensure the top-right three-dots menu button opens contextual actions and remains visible while menu is open.

**Independent Test**: Hovering over a game card reveals the top-right circular three-dots button (`view-more-symbolic`). Clicking opens the popover with Edit, Hide/Unhide, Remove, and Collections. The button and popover remain visible even if the pointer moves away from the card.

### Implementation for User Story 3

- [X] T012 [US3] Verify menu button layout, circular styling, and `view-more-symbolic` icon in `cartridges/ui/game-item.blp`
- [X] T013 [US3] Ensure `_reveal_buttons` keeps menu button visible while `options.props.active` is true in `cartridges/ui/game_item.py`
- [X] T014 [US3] Verify action triggers for Edit (`game.edit`), Hide/Unhide (`game.hide`/`game.unhide`), and Remove (`game.remove`) in `cartridges/ui/games.py`

**Checkpoint**: User Stories 1, 2, and 3 functional with persistent contextual popovers.

---

## Phase 6: User Story 4 - Empty States and Library Navigation (Priority: P3)

**Goal**: Verify empty state pages (Search, Hidden, Collection, Library) and keyboard/gamepad accessibility.

**Independent Test**: Empty searches, empty collections, empty hidden lists, and fresh libraries display corresponding GNOME status pages; keyboard Tab/Enter and gamepad controls navigate and activate grid items.

### Implementation for User Story 4

- [X] T015 [US4] Verify empty status pages in `cartridges/ui/window.blp` for empty search, empty hidden list, empty collections, and empty library
- [X] T016 [US4] Verify keyboard focus outline and item activation in `cartridges/ui/window.py` and `cartridges/ui/style.css`
- [X] T017 [US4] Verify gamepad navigation integration with `cartridges/gamepads.py`

**Checkpoint**: All user stories complete and accessible across input modalities.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Format validation, static typing, and automated test execution.

- [X] T018 Run blueprint compiler formatting on `cartridges/ui/game-item.blp` and `cartridges/ui/window.blp`
- [X] T019 Run Pyright static analysis in strict mode across `cartridges/ui/`
- [X] T020 Run Ruff linter and formatter verification across modified Python sources
- [X] T021 Run `ninja -C _build test` and execute end-to-end scenarios from `specs/005-game-list-view/quickstart.md`
- [X] T022 Verify all project documentation and sources strictly comply with Constitution Principle VI (Emoji-Free Standard)

---

## Phase 8: Launch Toast Notification & Internationalization (User Story 1 and 2 acceptance scenarios, FR-012, FR-013)

**Note**: This phase was originally labelled "User Story 5". The 2026-10-08 spec amendment assigned User Story 5 to time-precise "Last Played" sorting, so these completed tasks are relabelled `[US1]` (the toast is part of User Story 1 scenario 3 and User Story 2 scenario 3).

**Goal**: Display a dismissable in-app toast notification "Launched <game name>" upon launching a game from any UI surface, with proper gettext translation and translator comment.

**Independent Test**: Launching a game via hover Play button, cover click (when inverted), or details view triggers `game.play()` and displays a dismissable `Adw.Toast` with localized text "Launched <game name>".

### Implementation for Launch Toast

- [X] T023 [US1] Implement centralized `play(game: Game) -> None` in `cartridges/ui/games.py` that invokes `game.play()` and dispatches `_window().send_toast(_("Launched {}").format(game.name))` with `# Translators:` comment
- [X] T024 [US1] Update `GameActions` in `cartridges/ui/games.py` to route `"play"` action to `play(self.game)`
- [X] T025 [US1] Update `Window._show_details` in `cartridges/ui/window.py` to call `games.play(game)` when `cover-launches-game` is true
- [X] T026 [US1] Run `ninja -C _build cartridges-pot` to extract the new translatable string and verify translator comment in `po/cartridges.pot`
- [X] T027 [US1] Run Pyright strict type check and Ruff linter on `cartridges/ui/games.py` and `cartridges/ui/window.py`
- [X] T028 [US1] Run `ninja -C _build test` and verify Constitution Principle VI (Emoji-Free Standard) across all files

---

## Phase 9: User Story 5 - Time-Precise "Last Played" Sorting (Priority: P2, amendment 2026-10-08)

**Goal**: Record the exact launch time whenever a game is launched from Cartridges, persist it for every source, merge it with launcher-reported times, and re-sort so the launched game moves to the first position under the "Last Played" sort (FR-014 to FR-021).

**Independent Test**: With sort mode "Last Played", launch game A, wait at least one second, then launch game B. B is first and A second regardless of names, both within 1 second of launch; the order survives an application restart; under sort mode "A-Z" a launch does not move the game (quickstart Scenarios 8 and 9).

**Background for the implementer** (from research.md sections 6-9): `Game.last_played` is already a `GObject.Property(type=int)` holding Unix seconds, and `_sort` in `cartridges/ui/games.py` already orders "last_played" newest first with `0` last and a name tie-break. DO NOT modify `_sort`, `_name_cmp`, or `_SORT_MODES`. Only `imported` games are written to disk today; launcher games (Steam, Lutris, Heroic, ...) are rebuilt from the launcher every start, which is why a separate play-history file is needed. `game_id` is always source-prefixed (`steam_620`, `imported_0`, ...) and is unique across sources.

### Implementation for User Story 5

- [X] T029 [US5] Create `cartridges/play_history.py` with the SPDX header used by other new files (`# SPDX-License-Identifier: GPL-3.0-or-later` and `# SPDX-FileCopyrightText: Copyright 2026 samuelm333`), a module docstring, and only stdlib imports plus `from . import DATA_DIR` (no `gi`/GTK imports, per contracts/ui-contracts.md section 6). Define `_PATH = DATA_DIR / "last-played.json"` and a module-level cache `_history: dict[str, int] | None = None`. Implement `load() -> dict[str, int]`: on first call read `_PATH` as UTF-8 JSON; if the file is missing, unreadable (`OSError`), invalid JSON (`json.JSONDecodeError`, `UnicodeDecodeError`), or not a JSON object, use `{}`; otherwise keep only entries where the key is a `str` and the value is an `int` (not `bool`) and `>= 0` ("Values must be non-negative integers; any other entry is ignored on load"). Cache and return the dict. `load()` MUST NEVER raise.
- [X] T030 [US5] In `cartridges/play_history.py`, implement `record(game_id: str, timestamp: int) -> None`: call `load()`, set `history[game_id] = timestamp`, create `DATA_DIR` with `mkdir(parents=True, exist_ok=True)`, write the whole mapping with `json.dump(..., indent=4, sort_keys=True)` to a temporary file in the same directory (e.g. `_PATH.with_suffix(".json.tmp")`), then `os.replace(tmp, _PATH)` so the write is atomic. The write is synchronous by design (it must land before `exit-after-launch` quits). Keep full Pyright-strict type annotations and Ruff `ALL` compliance (depends on T029)
- [X] T031 [US5] In `Game.play()` in `cartridges/games.py`, add `import time` and `from . import play_history` (keep the existing `from . import DATA_DIR, SETTINGS` import style and Ruff import order). At the very start of `play()`, before `subprocess.Popen`, set `self.last_played = int(time.time())` and call `play_history.record(self.game_id, self.last_played)`. Leave the `subprocess.Popen` call and the `exit-after-launch` block unchanged and after the recording, so the time is saved even if the launch fails and before the application quits (FR-014, FR-015). Update the docstring to mention that the launch time is recorded (depends on T030)
- [X] T032 [US5] In `Source._get_games` in `cartridges/sources/__init__.py`, add `from cartridges import play_history` and, after the existing `game.added = game.added or added` line, add `game.last_played = max(game.last_played, play_history.load().get(game.game_id, 0))` so every source keeps the newer of the launcher-reported and Cartridges-recorded times (FR-019). Do not modify any individual source module under `cartridges/sources/` (depends on T029)
- [X] T033 [US5] In `play(game: Game)` in `cartridges/ui/games.py`, after `game.play()` and the existing toast call, add `sorter.changed(Gtk.SorterChange.DIFFERENT)` (same pattern as `GameEditable.apply`). Call it unconditionally: under "Last Played" the launched game moves to position 0 of the full list and any active search/collection/hidden filter (FR-018); under other sort modes the comparator ignores `last_played`, so the order is unchanged (FR-021). Do not touch the translatable toast string (depends on T031)
- [X] T034 [US5] Add `'play_history.py',` to the explicit Python sources list at the top of `cartridges/meson.build`, keeping the list in alphabetical order (after `'gamepads.py'`/`'games.py'` and before the next entry). Without this, the module is not installed and the built app fails with `ImportError` (depends on T029)
- [X] T035 [P] [US5] Create `tests/test_play_history.py` following the style of `tests/test_settings.py` (SPDX header, module docstring, `check_*` functions returning `None` that raise on failure, and an `if __name__ == "__main__":` block calling each check). Because importing the real `cartridges` package needs the meson-generated `config.py` and compiled GSettings, the test MUST stub the package before importing: create a `types.ModuleType("cartridges")` with `__path__ = [str(Path(__file__).resolve().parents[1] / "cartridges")]` and `DATA_DIR` set to a `tempfile.mkdtemp()` path, insert it into `sys.modules["cartridges"]`, then `importlib.import_module("cartridges.play_history")`. Reset `play_history._history = None` between checks. Checks: (a) missing file -> `load() == {}`; (b) `record("steam_620", 1791489600)` then reset cache and `load()` returns `{"steam_620": 1791489600}` and no `.tmp` file remains; (c) file containing `not json` -> `load() == {}` without raising; (d) file `{"a": 5, "b": "x", "c": -1, "d": true}` -> `load() == {"a": 5}`. Run with `python tests/test_play_history.py` (depends on T030)

**Checkpoint**: User Story 5 complete. A launched game moves to the first position under "Last Played", order survives restart, and other sort modes are unaffected.

---

## Phase 10: Polish for Amendment (2026-10-08)

**Purpose**: Quality gates and manual validation for User Story 5.

- [X] T036 [P] Run `pyright` (strict) and `ruff check` / `ruff format --check` on `cartridges/play_history.py`, `cartridges/games.py`, `cartridges/sources/__init__.py`, `cartridges/ui/games.py`, and `tests/test_play_history.py`; fix all findings
- [ ] T037 [P] Run `pre-commit run --all-files` and `meson setup _build --reconfigure && ninja -C _build && ninja -C _build test` inside the `gtk-dev` Distrobox container; confirm `play_history.py` is installed alongside `games.py` in the build/install output (verifies T034)
- [X] T038 Run `python tests/test_play_history.py` and confirm all checks pass
- [ ] T039 Execute quickstart Scenarios 8, 9, and 10 from `specs/005-game-list-view/quickstart.md` against `_build/cartridges/cartridges`; for Scenario 10 record the observed scroll and focus behavior, and if keyboard focus is lost after the re-sort, implement the fallback from research.md section 9 (restore focus to the launched game's new position) in `cartridges/ui/games.py` or `cartridges/ui/window.py`
- [ ] T040 Verify Constitution Principle VI (no emoji) across `cartridges/play_history.py`, `tests/test_play_history.py`, and all files in `specs/005-game-list-view/`

---

## Phase 11: User Story 5 Follow-up - Launch Survives a Failed Save (amendment 2026-10-08)

**Goal**: Make `play_history.record()` non-fatal so a storage failure never blocks, delays, or interrupts a game launch, while keeping the in-session sort and label correct, logging one warning, and leaving no temporary file (FR-022 to FR-025, SC-010).

**Independent Test**: With the data directory unwritable, launching a game starts it, shows the "Launched" toast, moves it first under "Last Played", logs one warning, and leaves no `last-played.json.tmp`; an earlier valid history file is unchanged (quickstart Scenario 11 and `python tests/test_play_history.py`).

**Background for the implementer** (from research.md section 10 and contracts/ui-contracts.md section 6): the existing `record()` in `cartridges/play_history.py` calls `mkdir`, writes `_PATH.with_suffix(".json.tmp")`, and calls `tmp.replace(_PATH)` with no error handling, and `Game.play()` calls it before `subprocess.Popen`, so any `OSError` stops the launch. DO NOT change the order in `Game.play()` and DO NOT catch errors there. DO NOT show a toast or dialog and DO NOT add translatable strings: reporting is log-only. Catch `OSError` only (not `Exception`) so Ruff `BLE001` and `S110` stay satisfied. The project logs with `logging.getLogger(__name__)` (see `cartridges/ui/preferences.py`, which defines `_logger = logging.getLogger(__name__)`). `load()` and its cache must not change.

### Implementation for Follow-up

- [X] T041 [US5] In `cartridges/play_history.py`, add `import logging` and a module-level `_logger = logging.getLogger(__name__)`, then rewrite the body of `record(game_id: str, timestamp: int)` so that: (1) `history = load()` and `history[game_id] = timestamp` still run first and outside any `try`, so the in-memory mapping is updated even when saving fails (FR-023); (2) `DATA_DIR.mkdir(parents=True, exist_ok=True)`, the temp-file write (`json.dump(history, f, indent=4, sort_keys=True)` to `_PATH.with_suffix(".json.tmp")`), and `tmp.replace(_PATH)` are inside one `try` that catches only `OSError`; (3) the `except OSError` branch logs exactly one warning with `_logger.warning("Could not save play history to %s: %s", _PATH, e)` (lazy `%s` formatting, no f-string, per Ruff `G004`), then removes the temporary file with `tmp.unlink(missing_ok=True)` inside its own nested `try`/`except OSError` that logs nothing further, so a failed cleanup neither raises nor adds a second warning (FR-024, FR-025); (4) the function returns `None` normally in every case and never raises `OSError` (FR-022). Keep the temp path in a local variable defined before the `try` so the handler can reference it. Update the docstring to say that failures are logged and not raised. Keep full Pyright-strict annotations and Ruff `ALL` compliance (depends on T030)
- [X] T042 [US5] In `cartridges/games.py`, update the `Game.play()` docstring to state that recording the launch time is best effort and cannot prevent the launch; make no code change to `Game.play()`, and confirm by reading it that `self.last_played = int(time.time())` still comes before `play_history.record(...)` and both come before `subprocess.Popen` and the `exit-after-launch` block (FR-022, FR-023) (depends on T041)

### Tests for Follow-up

- [X] T043 [US5] Add failure-case checks to `tests/test_play_history.py`, following its existing `check_*` style, and call each from the `if __name__ == "__main__":` block. The tests must not rely on `chmod`, because they may run as root; force failures by path shape instead, restoring the data directory between checks via the existing `_reset` helper (extend it to remove any directory or file left at `_PATH` or the `.json.tmp` path). Checks: (a) `check_record_survives_replace_failure`: make `_PATH` an existing empty directory so `tmp.replace(_PATH)` raises, call `play_history.record("steam_620", 1791489600)`, assert it returns without raising, `play_history.load()` still contains `{"steam_620": 1791489600}` (in-memory kept, FR-023), and no `*.tmp` file remains in the data directory (FR-025); (b) `check_record_survives_mkdir_failure`: temporarily point `play_history`'s `DATA_DIR` at a path that is an existing regular file (set `vars(play_history)["DATA_DIR"]` and `vars(play_history)["_PATH"]` to paths under it, restoring both in a `finally`), call `record(...)`, assert no exception and the in-memory mapping updated; (c) `check_previous_history_kept_on_failure`: write a valid history file with one entry, load it, make the temp path an existing directory so the temp-file open raises, call `record(...)` for another game, assert no exception and that re-reading `_PATH` as JSON still equals the original single entry (FR-025); (d) `check_failed_save_logs_one_warning`: attach a `logging.Handler` collecting records to the `cartridges.play_history` logger, repeat the replace-failure case from (a), and assert exactly one `WARNING` record whose message contains the file name `last-played.json`, and that a successful `record(...)` afterwards logs nothing; (e) `check_later_save_includes_earlier_failed_time`: after the failure in (a), remove the blocking directory, call `record("steam_730", 1791489700)`, reset the cache, and assert `load()` equals `{"steam_620": 1791489600, "steam_730": 1791489700}` (FR-023, spec edge case) (depends on T041)

### Verification for Follow-up

- [X] T044 [P] [US5] Run `pyright` (strict), `ruff check`, and `ruff format --check` on `cartridges/play_history.py`, `cartridges/games.py`, and `tests/test_play_history.py`; fix all findings without adding broad `noqa` or `# type: ignore` comments beyond what the existing code already uses (depends on T041, T042, T043)
- [X] T045 [US5] Run `python tests/test_play_history.py` and confirm every check, old and new, passes and that the run leaves no `.tmp` files in the temporary data directory (depends on T043)
- [ ] T046 [US5] Execute quickstart Scenario 11 from `specs/005-game-list-view/quickstart.md` against `_build/cartridges/cartridges` inside the `gtk-dev` Distrobox container: launch a game with an unwritable data directory and confirm it starts, the toast appears, the game moves first, exactly one warning is logged, no temp file remains, and "Exit After Launching Games" still exits (SC-010) (depends on T041)
- [ ] T047 [P] Verify Constitution Principle VI (no emoji) across `cartridges/play_history.py`, `tests/test_play_history.py`, and all files in `specs/005-game-list-view/`, and run `pre-commit run --all-files` (depends on T044)

**Checkpoint**: Follow-up complete. A failed history save never prevents a launch, the session sort and label stay correct, one warning is logged, and no temporary files or lost history result.

---

## Phase 12: User Story 6 - Show or Hide Game Titles in the Library (Priority: P3, amendment 2026-10-09)

**Note**: Task IDs continue after T047 (Phase 11, the save-failure follow-up).

**Goal**: Add a General-page preference that shows or hides the title under each cover in the main view, on by default, applied live to every card, persisted, with the name still exposed to assistive technology and still visible for games without a cover (FR-026 to FR-030).

**Independent Test**: Open Preferences, General, turn "Show Game Titles" off, and confirm titles vanish from all covers immediately (except covers-less games), that hover buttons, toast, search, sort and the details view are unchanged, and that the choice survives a restart (quickstart Scenario 12).

**Background for the implementer** (from research.md section 11, data-model.md section 6, contracts/ui-contracts.md section 7): the card title is the final `Label { label: bind template.game as <$Game>.name; ellipsize: middle; }` in `cartridges/ui/game-item.blp`. Switch rows in `cartridges/ui/preferences.blp` are bound to GSettings by `Preferences._bind_switches` in `cartridges/ui/preferences.py`, which looks up a template child named after the key with `-` replaced by `_` plus `_switch`. `GameItem` in `cartridges/ui/game_item.py` already reacts to a setting live via `SETTINGS.connect("changed::cover-launches-game", self._update_action_button)`; follow that pattern. The placeholder for games without a cover shows only the application icon, so the title MUST stay visible for them. DO NOT touch hover buttons, `cartridges/ui/games.py` (toast, sorting), or the details view.

### Implementation for User Story 6

- [X] T048 [P] [US6] In `data/page.samuelm333.Cartridges.gschema.xml.in`, add `<key name="show-game-titles" type="b"><default>true</default></key>` immediately after the `cover-launches-game` key, matching the file's indentation and formatting ("Game titles MUST be shown by default, including for existing users who have no stored preference"). Validate with `glib-compile-schemas --strict --dry-run` on a copy with the `@APP_ID@` and `@PREFIX@` placeholders substituted, or via the meson build
- [X] T049 [P] [US6] In `cartridges/ui/preferences.blp`, inside `general_page`, add a new `Adw.PreferencesGroup appearance_group { title: _("Appearance"); }` between `behavior_group` and `images_group`, containing `Adw.SwitchRow show_game_titles_switch { title: _("Show Game Titles"); subtitle: _("Display the name under each cover in the library"); }`. Keep Blueprint formatting valid (`blueprint-compiler format --fix --no-diff`)
- [X] T050 [US6] In `cartridges/ui/preferences.py`, add `show_game_titles_switch: Adw.SwitchRow = Gtk.Template.Child()` next to `cover_launches_game_switch`, and add `"show-game-titles",` to the `switches` set in `_bind_switches` (after `"cover-launches-game"`) so it binds to `active` with `Gio.SettingsBindFlags.DEFAULT` (depends on T049)
- [X] T051 [P] [US6] In `cartridges/ui/game-item.blp`, give the final title label the id `title_label` (`Label title_label { ... }`, keeping `label: bind template.game as <$Game>.name;` and `ellipsize: middle;`), and add an `accessibility { label: bind template.game as <$Game>.name; }` block to the `$GameItem` template so the name is exposed whether or not the label is visible (FR-029, SC-012)
- [X] T052 [US6] In `cartridges/ui/game_item.py`, add `title_label: Gtk.Label = Gtk.Template.Child()` and a method `_update_title(self, *_args: Any) -> None` that calls `self.title_label.set_visible(SETTINGS.get_boolean("show-game-titles") or self.game is None or self.game.cover is None)` (rule: "title visible = show-game-titles OR game has no cover"). In `__init__`, call `SETTINGS.connect("changed::show-game-titles", self._update_title)` next to the existing `cover-launches-game` connection and call `self._update_title()` once. Because grid items are rebound to different games, also connect `notify::game` on the item to re-run `_update_title` and to move a `notify::cover` handler: keep the handler id and the connected game in instance attributes, disconnect the old one when `game` changes, and connect `notify::cover` on the new game to `_update_title`. Keep full Pyright-strict annotations (depends on T051)
- [ ] T053 [US6] Make the new strings translatable: `po/POTFILES.in` currently lists no preferences files, so add `cartridges/ui/preferences.blp` and `cartridges/ui/preferences.py` in sorted position (after `cartridges/ui/games.py`), then run `ninja -C _build cartridges-pot` and confirm `po/cartridges.pot` contains the msgids "Appearance", "Show Game Titles", and "Display the name under each cover in the library". Expect the catalog to also gain the pre-existing preferences strings; that is intended (depends on T049)

### Verification for User Story 6

- [ ] T054 [P] [US6] Run `blueprint-compiler format --fix --no-diff` on `cartridges/ui/preferences.blp` and `cartridges/ui/game-item.blp`, then `pyright` (strict) and `ruff check` / `ruff format --check` on `cartridges/ui/game_item.py` and `cartridges/ui/preferences.py`; fix all findings (depends on T050, T052)
- [ ] T055 [US6] Run `meson setup _build --reconfigure && ninja -C _build && ninja -C _build test` inside the `gtk-dev` Distrobox container and confirm the schema compiles and the app starts (depends on T048, T050, T052)
- [ ] T056 [US6] Execute quickstart Scenario 12 from `specs/005-game-list-view/quickstart.md` against `_build/cartridges/cartridges`: default shown, switch present in "Appearance", live hide and show, unchanged hover/toast/search/sort/details, accessible name present, persistence after restart, and large-library reflow; if rows do not reflow, apply the `queue_resize()` fallback from research.md section 11 (depends on T055)
- [ ] T057 [P] [US6] Verify Constitution Principle VI (no emoji) across the changed files and `specs/005-game-list-view/`, and run `pre-commit run --all-files` (depends on T054)

**Checkpoint**: User Story 6 complete. The titles preference works live, persists, defaults to shown, keeps names accessible, and leaves all other behavior unchanged.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately.
- **Foundational (Phase 2)**: Depends on Setup (Phase 1) - blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2) - delivers MVP.
- **User Story 2 (Phase 4)**: Depends on User Story 1 (Phase 3).
- **User Story 3 (Phase 5)**: Depends on Foundational (Phase 2) - can run in parallel with US1/US2.
- **User Story 4 (Phase 6)**: Depends on US1, US2, and US3.
- **Polish (Phase 7)**: Depends on completion of all user story phases.
- **Launch Toast (Phase 8)**: Depends on Phase 3 and Phase 4 - delivers launch toast feedback.
- **User Story 5 (Phase 9)**: Depends on Phase 8 (`play()` in `cartridges/ui/games.py` must exist). Independent of US2, US3, and US4.
- **Amendment Polish (Phase 10)**: Depends on Phase 9.
- **Save-Failure Follow-up (Phase 11)**: Depends on Phase 9 (`play_history.record()` and `Game.play()` must exist). Independent of Phase 10, whose T036 to T040 can run before or after it; re-run T036 and T040 if Phase 11 lands first.
- **Show/Hide Titles (Phase 12)**: Depends only on the existing grid card (Phase 2 and Phase 3). Independent of Phases 8 to 10.

### Within User Story 5

```text
T029 (load) -> T030 (record) -> T031 (Game.play records) -> T033 (re-sort after launch)
                    |       \-> T032 (merge on load)   [needs only T029, can follow T029 directly]
                    \-> T035 (unit test)               [parallel with T031-T033]
T029 -> T034 (add play_history.py to cartridges/meson.build) [required before running the built app]
```

### Within the Save-Failure Follow-up

```text
T041 (harden record) -> T042 (Game.play docstring)
          |           \-> T046 (quickstart Scenario 11)
          \-> T043 (failure tests) -> T045 (run tests)
T041 + T042 + T043 -> T044 (pyright/ruff) -> T047 (emoji check, pre-commit)
```

### Within User Story 6

```text
T048 (schema) ---------------------------\
T049 (preferences.blp) -> T050 (prefs.py) -+-> T055 (build) -> T056 (quickstart)
                     \-> T053 (POTFILES + pot)
T051 (game-item.blp) -> T052 (game_item.py) -/
T050 + T052 -> T054 (format/lint) -> T057 (emoji, pre-commit)
```

### Parallel Opportunities

- T001 and T002 can run in parallel during Setup.
- T012 and T014 can be validated in parallel with User Story 1 work.
- T018, T019, T020, and T022 can run as parallel verification checks in Polish.
- T026 and T027 can run in parallel during Phase 8.
- T032 (`cartridges/sources/__init__.py`) can be done in parallel with T030/T031 once T029 exists.
- T035 (`tests/test_play_history.py`) can be written in parallel with T031-T033 once T030 exists.
- T036 and T037 can run in parallel during Phase 10.
- T042 (`cartridges/games.py` docstring) and T043 (`tests/test_play_history.py`) can be done in parallel once T041 is in place; T044 and T047 can run in parallel at the end of Phase 11.

### Parallel Example: User Story 6

```text
At the start of Phase 12:
  Agent A: T048  (data/page.samuelm333.Cartridges.gschema.xml.in)
  Agent B: T049 then T050 and T053  (cartridges/ui/preferences.blp, preferences.py, po/POTFILES.in)
  Agent C: T051 then T052  (cartridges/ui/game-item.blp, game_item.py)
```

### Parallel Example: User Story 5

```text
After T030 completes:
  Agent A: T031 then T033  (cartridges/games.py, cartridges/ui/games.py)
  Agent B: T032            (cartridges/sources/__init__.py)
  Agent C: T035            (tests/test_play_history.py)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (Layout & CSS in `game-item.blp` and `style.css`)
3. Complete Phase 3: User Story 1 (Restore top-left Play button and cover click details)
4. Validate User Story 1 independently in local build

### Incremental Delivery

1. Setup + Foundational -> UI grid structure ready
2. User Story 1 -> Play button hover + cover details activation (MVP)
3. User Story 2 -> Dynamic "Cover Image Launches Game" toggle support (Info button)
4. User Story 3 -> Three-dots menu button persistence and actions
5. User Story 4 -> Empty states and controller navigation
6. Polish -> Formatting, strict typing, tests, and emoji-free verification
7. Launch Toast -> Game launch toast notification with full gettext translation
8. User Story 5 -> Time-precise "Last Played" sorting; launched game moves to the first position (amendment 2026-10-08)
9. Amendment Polish -> Type checks, tests, and quickstart Scenarios 8-10
10. Save-Failure Follow-up -> Non-fatal history recording, failure tests, and quickstart Scenario 11 (FR-022 to FR-025, SC-010)
11. User Story 6 -> Show/hide game titles preference (amendment 2026-10-09)

### Amendment Delivery (current work)

Phases 1-9 are implemented (commit `3be3332`). Remaining work is Phase 10 verification (T036 to T040) and the Phase 11 follow-up. The smallest shippable slice for the follow-up is T041 (the fix) plus T043 (its tests); T042 is a docstring-only change and T044 to T047 are the verification gates. Because T041 removes a path where a launch can fail outright, it should ship before the next release.

### Titles Amendment Delivery (2026-10-09)

The smallest shippable slice for User Story 6 is T048 to T052 (key, switch, card behavior with accessible name); T053 makes the strings translatable and T054 to T057 are the verification gates. Tests are not requested for this story: the behavior is GTK widget state that is covered by quickstart Scenario 12 rather than by a unit test.
