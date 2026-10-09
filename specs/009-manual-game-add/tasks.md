---

description: "Task list for Manual Game Add (persist manually added games when applied)"
---

# Tasks: Manual Game Add

**Input**: Design documents from `specs/009-manual-game-add/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/persistence-contract.md](contracts/persistence-contract.md), [quickstart.md](quickstart.md)

**Tests**: Included. The plan names `tests/test_manual_games.py` (new). It follows the existing plain-script style of `tests/test_play_history.py`: `check_*` functions that raise `AssertionError`, called from an `if __name__ == "__main__":` block, run with `python3 tests/test_manual_games.py`. It uses the real `gi` like `tests/test_importer.py` and points `GAMES_DIR` at a temporary directory. The toast and the Apply flow are window behavior and are verified by quickstart scenarios, not unit tests.

**Organization**: Tasks are grouped by user story so each story can be implemented and tested on its own.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: User story from spec.md (US1, US2, US3, US4)
- Paths are relative to the repository root.
- Constitution gates that apply to every task: complete type annotations (Pyright strict), Ruff `ALL`, catch `OSError` only (never a blanket `Exception`), no emoji, SPDX header on new files (`GPL-3.0-or-later`, `Copyright 2026 samuelm333`).

**Status note (2026-10-09)**: T006, T010, T014, and T019 are left open because they require driving the real window. Their persistence, numbering, and failure behavior was checked headlessly instead: `GameEditable.apply()` was run against the installed build in separate processes (add three games, restart, edit, restart, then add two games with an unwritable games directory). Still to check by hand in the running app: cover set and removed, hide/launch/collection/remove/undo across a restart, the `kill -9` case, Import Now with startup import off, and the on-screen toast.

---

## Phase 1: Setup

**Purpose**: Branch

- [X] T001 Create branch `feat/009-manual-game-add` from `main` (Constitution: Development & Branching Workflow) and commit the spec documents in `specs/009-manual-game-add/` as the first commit. Do not add `.specify/integrations/claude.manifest.json`, which is unrelated

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Make the record write atomic and reportable. User Stories 1, 2, and 4 all call it.

- [X] T002 In `cartridges/games.py`, rewrite `Game.save()` per contracts/persistence-contract.md section 2 and research.md section 4: create `GAMES_DIR` if missing, write the JSON (same content as today: all `PROPERTIES`, `indent=4`, `sort_keys=True`, UTF-8) to `<GAMES_DIR>/<game_id>.json.tmp`, then replace the final `<game_id>.json` with it. On any `OSError`, remove the temporary file with `unlink(missing_ok=True)` inside its own `OSError` guard (cleanup errors are ignored), leave the existing record unchanged, and re-raise the original `OSError`. Keep the signature `save(self) -> None`. Update the docstring to say it raises `OSError`. Do not change `PROPERTIES` or the file format ("files written by this version MUST be loadable by earlier versions")

**Checkpoint**: `Game.save()` is atomic, raises `OSError` on failure, and leaves no `.tmp` file.

---

## Phase 3: User Story 1 - A Manually Added Game Survives a Restart (Priority: P1) [MVP]

**Goal**: A game applied in the Add Game form is written to disk at that moment, so it is present after a restart with all its values, regardless of the "Import Games on Startup" setting, and imports do not touch it (FR-001 to FR-006, FR-009).

**Independent Test**: Add a game with a name, command, developer, and cover; close and reopen the application (also with `kill -9` right after Apply); confirm the game is present with all values and launches (quickstart Scenarios 1 and 2).

**Background for the implementer** (from research.md sections 1 and 2): `GameEditable.apply()` in `cartridges/ui/games.py` creates the game with `imported.new()`, appends it to `sources.get(imported.ID)`, then copies `executable`, `name`, `developer`. Nothing saves it; the only `game.save()` caller is the `notify::removed` handler in `Source._track` (`cartridges/sources/__init__.py`). Startup already loads `imported_*.json` regardless of "Import Games on Startup" and imports already skip the `imported` source, so no change is needed there. DO NOT save in `Game.__init__`, on each property notify, or at shutdown.

### Tests for User Story 1

- [X] T003 [P] [US1] Create `tests/test_manual_games.py` with the SPDX header, a module docstring ("Test saving, loading, and numbering of manually added games."), and a temporary-directory setup that points `cartridges.games.GAMES_DIR` and `cartridges.sources.imported.GAMES_DIR` at it (and `cartridges.cover.COVERS_DIR` at another temporary directory). Add `check_save_round_trip`: build a `Game` through `imported.new()`, set `name="Test One"`, `executable="true"`, `developer="Dev"`, call `save()`, then assert `imported.get_games()` yields one game whose `game_id`, `name`, `executable`, `developer`, `source`, and `added` equal the saved values, and that no `*.tmp` file remains. Add `check_save_creates_missing_directory` (remove the temp directory first, then save). Wire both into `if __name__ == "__main__":`

### Implementation for User Story 1

- [X] T004 [US1] In `cartridges/ui/games.py`, at the end of `GameEditable.apply()` (after `developer` is copied), call `self.game.save()` when `self.game.source == imported.ID`. Wrap it in `try`/`except OSError as e` that writes one `logging` warning with the game ID and the reason (add `import logging` and a module `_logger = logging.getLogger(__name__)` following `cartridges/sources/__init__.py`) and then continues without raising. Do not show a toast yet (that is T012). Cancel never reaches `apply()`, so cancelled edits are not saved (depends on T002)

**Checkpoint**: User Story 1 works: Apply persists the game; `python3 tests/test_manual_games.py` passes.

---

## Phase 4: User Story 2 - Edits and State Changes Persist (Priority: P1)

**Goal**: Edits to a manually added game are written when applied; cancelled edits never are; hidden, last-played, collection, and removal states keep working across restarts (FR-003, FR-007, FR-010).

**Independent Test**: Edit name, command, developer, and cover of a manually added game and restart; hide it, launch it, put it in a collection, remove it and undo another removal, and restart (quickstart Scenarios 3 and 4).

**Background for the implementer** (from research.md sections 2 and 6): the same `apply()` call from T004 already rewrites the record on every Apply of an existing manual game, so US2 needs no new production code. Hidden state (`hidden.json`), last played (`last-played.json`), removal (`notify::removed` handler) and collections (GSettings, kept because the record now exists) already persist. This phase proves them and adds the missing test coverage. DO NOT change `collections.py`, `hidden_games.py`, or `play_history.py`.

### Tests for User Story 2

- [X] T005 [US2] In `tests/test_manual_games.py`, add `check_edit_overwrites_record`: save a game, change `name` and `executable`, save again, and assert `imported.get_games()` yields exactly one game with the new values and the original `added` and `game_id`. Add `check_removed_state_round_trip`: set `removed = True`, save, reload, assert `removed` is `True`; set it back to `False`, save, reload, assert `False`. Wire both into the `__main__` block (depends on T003)

### Verification for User Story 2

- [ ] T006 [US2] Execute quickstart Scenarios 3 and 4 from `specs/009-manual-game-add/quickstart.md` against the built app with a throwaway `XDG_DATA_HOME`: edits and cancel behavior, cover set and removed, hidden, last-played order, collection membership, remove, and undo, each checked after a restart. If any state does not persist, record the finding in `specs/009-manual-game-add/research.md` and fix it in the smallest affected module before continuing (depends on T004)

**Checkpoint**: User Story 2 verified: edits and states survive restarts.

---

## Phase 5: User Story 3 - Several Added Games Stay Distinct (Priority: P2)

**Goal**: Every manually added game has its own identity even when earlier games were never saved, when removed games exist, or when oddly named files are present (FR-008, FR-013).

**Independent Test**: Without restarting, add three games, restart, and confirm all three exist with their own values; remove one and add another and confirm the removed game's identity is not reused; place `imported_old.json` and a damaged `imported_7.json` in the data directory and confirm Add Game still works (quickstart Scenarios 5 and 7).

**Background for the implementer** (from research.md section 3 and data-model.md section 2): `imported.new()` currently does `{int(p.stem.rsplit("_", 1)[1]) for p in get_paths()}`, which (a) ignores games that are in memory but not on disk, so two unsaved games get the same ID, and (b) raises `ValueError` on any stem that does not end in a number. `cartridges/sources/imported.py` cannot import `cartridges.sources` (that package loads it dynamically), so the in-memory IDs are passed in. DO NOT change the `imported_<n>` ID scheme.

### Tests for User Story 3

- [X] T007 [US3] In `tests/test_manual_games.py`, add `check_next_number_skips_used`: `_next_number` returns the lowest unused number given disk numbers and `taken` IDs (for example used `{0, 1, 3}` gives `2`). Add `check_ignores_odd_file_names`: with `imported_old.json`, `imported_.json`, and `imported_1a.json` present, `imported.new()` does not raise and returns `imported_0`. Add `check_reserves_damaged_and_removed`: a damaged `imported_4.json` (contents `not json`) and a valid record with `removed: true` named `imported_5.json` both reserve their numbers, and the damaged file is byte-for-byte unchanged after `new()`. Add `check_unsaved_games_get_distinct_ids`: with no files on disk, two games created with `imported.new(taken)` where `taken` holds the first game's ID get different IDs. Wire all into the `__main__` block (depends on T005)

### Implementation for User Story 3

- [X] T008 [US3] In `cartridges/sources/imported.py`, add `_number(stem: str) -> int | None` that returns the integer for a stem matching `imported_<digits>` (`re.fullmatch(r"imported_(\d+)", stem)`) and `None` otherwise, and `_next_number(used: Iterable[int]) -> int` returning the lowest non-negative integer not in `used`. Change `new` to `new(taken: Iterable[str] = ()) -> Game`: build `used` from `_number` applied to every path stem in `get_paths()` and to every ID in `taken`, drop `None`, and use `_next_number`. Never open or parse existing files for numbering ("MUST NOT open, parse, or modify existing files to compute `n`"). Update the docstring (depends on T007)
- [X] T009 [US3] In `cartridges/ui/games.py`, in `GameEditable.apply()`, pass the IDs of the games already in the in-memory `imported` source to `imported.new`: take `source = sources.get(imported.ID)` once, build `taken = {g.game_id for g in source}` by iterating the list model (use `source.get_item(i)` for `i in range(source.get_n_items())`, not the private `_games`), call `imported.new(taken)`, then `source.append(game)` as today (depends on T004, T008)

### Verification for User Story 3

- [ ] T010 [US3] Execute quickstart Scenarios 5 and 7 from `specs/009-manual-game-add/quickstart.md` against the built app with a throwaway `XDG_DATA_HOME`: three and ten games added in a row, remove then add, `imported_old.json` and damaged `imported_7.json` present, and a record edited by hand while the app is closed (depends on T009)

**Checkpoint**: User Story 3 verified: identities are unique and never reused, and odd files cannot break Add Game.

---

## Phase 6: User Story 4 - A Failed Save Is Visible and Harmless (Priority: P3)

**Goal**: When the record cannot be written on Apply, the game still works for the session, the user gets one dismissable translatable notice, one warning is logged, nothing else breaks, and earlier saved games stay intact (FR-011, FR-012, FR-015).

**Independent Test**: Make the games directory unwritable, add a game, and confirm the game works, a toast appears within 1 second, no dialog appears, no `.tmp` file remains, and a later successful Apply saves the full state (quickstart Scenario 6).

**Background for the implementer** (from research.md section 5 and contracts section 3): use `Window.send_toast(title)` via the existing `_window()` helper in `cartridges/ui/games.py`, exactly like `play()` and `hide()`. The string must be `_("{} could not be saved and will be lost when Cartridges closes").format(game.name)` preceded by a `# Translators: {} is the name of the game that could not be saved` comment, as `play()` does. Never use an f-string or concatenation. No Undo button. DO NOT show a toast from `Source._save` (removal), only from Apply.

### Tests for User Story 4

- [X] T011 [US4] In `tests/test_manual_games.py`, add failure checks that monkeypatch the filesystem operation and restore it afterwards, following `check_record_survives_replace_failure` and `check_record_survives_mkdir_failure` in `tests/test_play_history.py`: `check_save_raises_on_replace_failure` and `check_save_raises_on_mkdir_failure` (each asserts `Game.save()` raises `OSError`), `check_failed_save_keeps_previous_record` (a saved record is byte-for-byte unchanged after a failed save of changed values), `check_failed_save_leaves_no_tmp` (no `*.tmp` in `GAMES_DIR` after a failed save, including when removing the temporary file also fails), `check_later_save_writes_full_state` (after a failed save and a successful one, reloading yields the latest values), and `check_damaged_file_untouched_by_other_saves` (saving a new game leaves a damaged `imported_7.json` byte-for-byte unchanged). Wire all into the `__main__` block (depends on T007)

### Implementation for User Story 4

- [X] T012 [US4] In `cartridges/ui/games.py`, extend the `except OSError` branch added in T004 so that, after writing the warning, it calls `_window().send_toast(...)` with the notice text from the background above, including the `# Translators:` comment. It must show at most one toast per Apply and never raise (depends on T004)

### Verification for User Story 4

- [X] T013 [US4] Run `ninja -C _build cartridges-pot` inside the `gtk-dev` Distrobox container and confirm `po/cartridges.pot` contains the msgid "{} could not be saved and will be lost when Cartridges closes" with its `Translators:` comment and no extraction warnings (quickstart Scenario 8) (depends on T012)
- [ ] T014 [US4] Execute quickstart Scenario 6 from `specs/009-manual-game-add/quickstart.md` against the built app with an unwritable games directory: notice within 1 second, one log warning, no dialog, no `.tmp` file, different IDs for two unsaved games, and the full state saved after the directory is writable again (depends on T009, T012)

**Checkpoint**: User Story 4 verified: a failed save is reported once and does no harm.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Quality gates required by the constitution before the feature is marked complete

- [X] T015 [P] Run `uvx pre-commit run --all-files` (or `pre-commit run --all-files`) inside the `gtk-dev` Distrobox container; fix all Ruff, formatting, trailing-whitespace, and Blueprint findings in the changed files. Note: the pre-commit Pyright hook cannot import `gi` in its isolated environment and reports the same `reportMissingImports` errors on untouched GTK files; confirm no new error types are introduced by comparing against an untouched file such as `cartridges/ui/cover.py`
- [X] T016 [P] Run `meson setup _build --reconfigure && ninja -C _build && ninja -C _build test` inside the `gtk-dev` Distrobox container and confirm the build and the desktop, schema, and AppStream checks pass. No Blueprint file changes in this feature, so no manual Blueprint recompile is needed
- [X] T017 [P] Run `python3 tests/test_manual_games.py` and the existing `tests/test_play_history.py`, `tests/test_hidden_games.py`, `tests/test_importer.py`, and `tests/test_saved_library.py` inside the `gtk-dev` Distrobox container; all must pass
- [X] T018 [P] Verify Constitution Principle VI (no emoji) across `cartridges/games.py`, `cartridges/sources/imported.py`, `cartridges/ui/games.py`, `tests/test_manual_games.py`, and all files in `specs/009-manual-game-add/`
- [ ] T019 Execute quickstart Scenarios 1 and 2 end to end against the built app (including the `kill -9` case and Import Now with "Import Games on Startup" off) as the final acceptance check, then record any deviation in the checklist notes of `specs/009-manual-game-add/checklists/requirements.md` (depends on T012, T015 to T018)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup. T002 blocks T004 and, through it, every story.
- **User Story 1 (Phase 3)**: Depends on Phase 2. MVP.
- **User Story 2 (Phase 4)**: Depends on US1 (T004). No new production code.
- **User Story 3 (Phase 5)**: T008 (`imported.py`) is independent of US1; T009 edits `cartridges/ui/games.py` after T004. Independent of US2.
- **User Story 4 (Phase 6)**: Depends on T004. Independent of US2 and US3 for production code; T014 needs T009 for the distinct-ID check.
- **Polish (Phase 7)**: Depends on all stories.

### Shared files (tasks that touch the same file run in order)

- `cartridges/ui/games.py`: T004, then T009 and T012. Do T009 and T012 one after the other.
- `tests/test_manual_games.py`: T003, T005, T007, T011 in that order.
- `cartridges/games.py`: T002 only.
- `cartridges/sources/imported.py`: T008 only.

### Within the stories

```text
T001 -> T002 -> T004 -> T009 -> T014
         |        \-> T012 -> T013
         |            \-> T014
T003 -> T005 -> T007 -> T011
T007 -> T008 -> T009
T004 -> T006
T009, T012 -> T010, T014 -> T015..T018 -> T019
```

### Parallel Opportunities

- T003 (new test file) can start as soon as T002 exists, in parallel with T004 (different files).
- T008 (`cartridges/sources/imported.py`) can be written in parallel with T004 and T012 once T007 exists.
- T013 and T014 can run in parallel after T012 (pot extraction vs. manual scenario).
- T015, T016, T017, and T018 are independent gates and can run in parallel in Phase 7.

### Parallel Example: After T002

```text
Agent A: T004 then T012  (cartridges/ui/games.py: save on Apply, then the failure notice)
Agent B: T003 then T005 then T007  (tests/test_manual_games.py)
Agent C: T008  (cartridges/sources/imported.py, after T007 defines the expected behavior)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. T001 branch, T002 atomic save.
2. T003 test file, T004 save on Apply.
3. Validate with `python3 tests/test_manual_games.py` and quickstart Scenario 1. This alone fixes the reported problem: a manually added game survives a restart.

### Incremental Delivery

1. US1: game persists when applied (MVP).
2. US2: prove edits and states persist (tests and manual verification; no new production code).
3. US3: unique identities and tolerance of odd files (prevents silent data loss and a crash in Add Game).
4. US4: visible, harmless failure (notice and translation).
5. Polish: formatting, build, full test run, emoji check, final acceptance.

### Notes

- Tests for the toast and the Apply flow are manual (quickstart) because they need a window; the persistence, numbering, and failure logic they depend on are unit tested.
- Games added by earlier versions but never saved cannot be recovered; this is accepted in the spec assumptions.
- Keep the diff small: four production files at most (`games.py`, `sources/imported.py`, `ui/games.py`, plus `po/cartridges.pot` regenerated if the project commits it).
