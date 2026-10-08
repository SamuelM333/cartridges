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

- [ ] T029 [US5] Create `cartridges/play_history.py` with the SPDX header used by other new files (`# SPDX-License-Identifier: GPL-3.0-or-later` and `# SPDX-FileCopyrightText: Copyright 2026 samuelm333`), a module docstring, and only stdlib imports plus `from . import DATA_DIR` (no `gi`/GTK imports, per contracts/ui-contracts.md section 6). Define `_PATH = DATA_DIR / "last-played.json"` and a module-level cache `_history: dict[str, int] | None = None`. Implement `load() -> dict[str, int]`: on first call read `_PATH` as UTF-8 JSON; if the file is missing, unreadable (`OSError`), invalid JSON (`json.JSONDecodeError`, `UnicodeDecodeError`), or not a JSON object, use `{}`; otherwise keep only entries where the key is a `str` and the value is an `int` (not `bool`) and `>= 0` ("Values must be non-negative integers; any other entry is ignored on load"). Cache and return the dict. `load()` MUST NEVER raise.
- [ ] T030 [US5] In `cartridges/play_history.py`, implement `record(game_id: str, timestamp: int) -> None`: call `load()`, set `history[game_id] = timestamp`, create `DATA_DIR` with `mkdir(parents=True, exist_ok=True)`, write the whole mapping with `json.dump(..., indent=4, sort_keys=True)` to a temporary file in the same directory (e.g. `_PATH.with_suffix(".json.tmp")`), then `os.replace(tmp, _PATH)` so the write is atomic. The write is synchronous by design (it must land before `exit-after-launch` quits). Keep full Pyright-strict type annotations and Ruff `ALL` compliance (depends on T029)
- [ ] T031 [US5] In `Game.play()` in `cartridges/games.py`, add `import time` and `from . import play_history` (keep the existing `from . import DATA_DIR, SETTINGS` import style and Ruff import order). At the very start of `play()`, before `subprocess.Popen`, set `self.last_played = int(time.time())` and call `play_history.record(self.game_id, self.last_played)`. Leave the `subprocess.Popen` call and the `exit-after-launch` block unchanged and after the recording, so the time is saved even if the launch fails and before the application quits (FR-014, FR-015). Update the docstring to mention that the launch time is recorded (depends on T030)
- [ ] T032 [US5] In `Source._get_games` in `cartridges/sources/__init__.py`, add `from cartridges import play_history` and, after the existing `game.added = game.added or added` line, add `game.last_played = max(game.last_played, play_history.load().get(game.game_id, 0))` so every source keeps the newer of the launcher-reported and Cartridges-recorded times (FR-019). Do not modify any individual source module under `cartridges/sources/` (depends on T029)
- [ ] T033 [US5] In `play(game: Game)` in `cartridges/ui/games.py`, after `game.play()` and the existing toast call, add `sorter.changed(Gtk.SorterChange.DIFFERENT)` (same pattern as `GameEditable.apply`). Call it unconditionally: under "Last Played" the launched game moves to position 0 of the full list and any active search/collection/hidden filter (FR-018); under other sort modes the comparator ignores `last_played`, so the order is unchanged (FR-021). Do not touch the translatable toast string (depends on T031)
- [ ] T034 [US5] Add `'play_history.py',` to the explicit Python sources list at the top of `cartridges/meson.build`, keeping the list in alphabetical order (after `'gamepads.py'`/`'games.py'` and before the next entry). Without this, the module is not installed and the built app fails with `ImportError` (depends on T029)
- [ ] T035 [P] [US5] Create `tests/test_play_history.py` following the style of `tests/test_settings.py` (SPDX header, module docstring, `check_*` functions returning `None` that raise on failure, and an `if __name__ == "__main__":` block calling each check). Because importing the real `cartridges` package needs the meson-generated `config.py` and compiled GSettings, the test MUST stub the package before importing: create a `types.ModuleType("cartridges")` with `__path__ = [str(Path(__file__).resolve().parents[1] / "cartridges")]` and `DATA_DIR` set to a `tempfile.mkdtemp()` path, insert it into `sys.modules["cartridges"]`, then `importlib.import_module("cartridges.play_history")`. Reset `play_history._history = None` between checks. Checks: (a) missing file -> `load() == {}`; (b) `record("steam_620", 1791489600)` then reset cache and `load()` returns `{"steam_620": 1791489600}` and no `.tmp` file remains; (c) file containing `not json` -> `load() == {}` without raising; (d) file `{"a": 5, "b": "x", "c": -1, "d": true}` -> `load() == {"a": 5}`. Run with `python tests/test_play_history.py` (depends on T030)

**Checkpoint**: User Story 5 complete. A launched game moves to the first position under "Last Played", order survives restart, and other sort modes are unaffected.

---

## Phase 10: Polish for Amendment (2026-10-08)

**Purpose**: Quality gates and manual validation for User Story 5.

- [ ] T036 [P] Run `pyright` (strict) and `ruff check` / `ruff format --check` on `cartridges/play_history.py`, `cartridges/games.py`, `cartridges/sources/__init__.py`, `cartridges/ui/games.py`, and `tests/test_play_history.py`; fix all findings
- [ ] T037 [P] Run `pre-commit run --all-files` and `meson setup _build --reconfigure && ninja -C _build && ninja -C _build test` inside the `gtk-dev` Distrobox container; confirm `play_history.py` is installed alongside `games.py` in the build/install output (verifies T034)
- [ ] T038 Run `python tests/test_play_history.py` and confirm all checks pass
- [ ] T039 Execute quickstart Scenarios 8, 9, and 10 from `specs/005-game-list-view/quickstart.md` against `_build/cartridges/cartridges`; for Scenario 10 record the observed scroll and focus behavior, and if keyboard focus is lost after the re-sort, implement the fallback from research.md section 9 (restore focus to the launched game's new position) in `cartridges/ui/games.py` or `cartridges/ui/window.py`
- [ ] T040 Verify Constitution Principle VI (no emoji) across `cartridges/play_history.py`, `tests/test_play_history.py`, and all files in `specs/005-game-list-view/`

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

### Within User Story 5

```text
T029 (load) -> T030 (record) -> T031 (Game.play records) -> T033 (re-sort after launch)
                    |       \-> T032 (merge on load)   [needs only T029, can follow T029 directly]
                    \-> T035 (unit test)               [parallel with T031-T033]
T029 -> T034 (add play_history.py to cartridges/meson.build) [required before running the built app]
```

### Parallel Opportunities

- T001 and T002 can run in parallel during Setup.
- T012 and T014 can be validated in parallel with User Story 1 work.
- T018, T019, T020, and T022 can run as parallel verification checks in Polish.
- T026 and T027 can run in parallel during Phase 8.
- T032 (`cartridges/sources/__init__.py`) can be done in parallel with T030/T031 once T029 exists.
- T035 (`tests/test_play_history.py`) can be written in parallel with T031-T033 once T030 exists.
- T036 and T037 can run in parallel during Phase 10.

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

### Amendment Delivery (current work)

Phases 1-8 are complete. The remaining work is Phase 9 and Phase 10 only. The smallest shippable slice is T029, T030, T031, T033, and T034 (launch recorded, persisted, and the game moves first); T032 adds the launcher-time merge and should ship in the same change so Steam-reported times are not ignored after restart.
