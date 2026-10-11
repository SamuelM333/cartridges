---

description: "Task list for the Collections feature"
---

# Tasks: Collections

**Input**: Design documents from `specs/011-collections/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: Included, as the plan requires (research R4, constitution Quality Gates item 5). Stories 1 to 3 describe behavior that already exists, so their tasks are tests that lock it in and change no application code. Only story 4 changes the application. The new tests follow `tests/test_importer.py`: `check_*` functions called from an `if __name__ == "__main__":` runner, with the `cartridges` package stubbed. All of them go in one new file, `tests/test_collections.py`, so none are marked parallel.

**Organization**: Tasks are grouped by user story. All commands run inside the `gtk-dev` container.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on incomplete tasks)
- **[Story]**: The user story the task belongs to (US1 to US4)

## Path Conventions

Single project: application code in `cartridges/`, tests in `tests/`, schema in `data/`. Paths are relative to the repository root.

---

## Phase 1: Setup

- [X] T001 Confirm the branch and the baseline: `git branch --show-current` prints `feat/011-collections`; then in `gtk-dev` run `rm -rf _build && meson setup _build -Dprofile=development && ninja -C _build && env -u DISPLAY -u WAYLAND_DISPLAY ninja -C _build test` and confirm all 13 tests pass before any change

---

## Phase 2: Foundational (blocking prerequisites)

**Purpose**: The test file every story adds checks to.

**CRITICAL**: No story task can start before this phase is complete.

- [X] T002 Create `tests/test_collections.py` with the SPDX header (`GPL-3.0-or-later`, `Copyright 2026 samuelm333`) and a module docstring. Copy the stubbing approach of `tests/test_importer.py`: `gi.require_versions({"Gdk": "4.0", "Gtk": "4.0", "Adw": "1"})`, a temporary `DATA_DIR`, a `types.ModuleType("cartridges")` stub put in `sys.modules` with `__path__` set to the repo's `cartridges` folder, and `logging.getLogger("cartridges").addHandler(logging.NullHandler())`. The stub's `SETTINGS` is a small fake class with `get_boolean(key)`, `get_string(key)`, `get_user_value(key)` (as in `_Settings` in `tests/test_importer.py`) plus `get_value("collections")` and `set_value("collections", value)` that store a `GLib.Variant("aa{sv}", [])`. Import `cartridges.games as games`, `cartridges.collections as collections`, `cartridges.sources.imported as imported`, and `cartridges.ui.collections as ui_collections` with `importlib.import_module`. Add helpers: `_expect(actual, expected, what)` (raises `AssertionError` with the message `Expected {what} to be {expected!r}, got {actual!r}`), `_game(game_id, **props)` (copy from `tests/test_importer.py`), `_logged(call)` returning the `logging.LogRecord` list (copy from `tests/test_hidden_games.py`), and `_reset()` which empties `collections.model` and sets the fake setting back to an empty `aa{sv}` variant. End with an `if __name__ == "__main__":` runner that is empty for now. Run `python3 tests/test_collections.py` and confirm exit status 0
- [X] T003 In `tests/meson.build` add `'test_collections',` to the `test_scripts` list, in sorted position (between `'test_check_emojis',` and `'test_desktop',`), so `ninja -C _build test` and CI run it

**Checkpoint**: `env -u DISPLAY -u WAYLAND_DISPLAY ninja -C _build test` lists 14 tests and all pass.

---

## Phase 3: User Story 1 - Create and manage collections (Priority: P1) Implemented

**Goal**: Lock in how collections are created, edited, ordered, and removed, as recorded in the spec (FR-001 to FR-005, `data-model.md`).

**Independent Test**: `python3 tests/test_collections.py` passes the five checks below with no change to application code.

### Tests for User Story 1

- [X] T004 [US1] In `tests/test_collections.py` add `check_icons_and_defaults()` and add it to the runner: `len(collections.ICONS) == 21`; the set of `icon.name` values equals exactly `collection, star, heart, music, people, skull, private, globe, map, city, car, horse, sprout, step-over, gamepad, ball, puzzle, flashlight, knife, gun, fist`; every icon has a non-empty `a11y_label`; `collections.Collection().icon == "collection"` (the default) and `.icon_name == "collection-symbolic"` (FR-003)
- [X] T005 [US1] In `tests/test_collections.py` add `check_editable_validity()` and add it to the runner: for `ui_collections.CollectionEditable()`, `valid` is `False` when `name` is empty, `True` once `name` is `"Co-op"` and `icon` is `"star"`, and still `True` for `name = "   "` (the data model says: "a name of only spaces is accepted"); `apply()` on an invalid editable changes nothing (FR-003)
- [X] T006 [US1] In `tests/test_collections.py` add `check_apply_creates_and_edits()` and add it to the runner: with `_reset()`, set `name="Co-op"`, `icon="star"` on a `CollectionEditable()` and call `apply()`; `collections.model` then holds one collection with that name and icon and the fake setting's `collections` value was written. Repeat with `game=_game("steam_1")` and expect the new collection to contain `"steam_1"`. Then edit: create `CollectionEditable(collection=existing)` with a new name and icon, `apply()`, and expect the same `Collection` object changed (not a second one) and saved (FR-002, FR-004)
- [X] T007 [US1] In `tests/test_collections.py` add `check_remove_and_undo()` and add it to the runner: monkeypatch `ui_collections._window` (with `vars(ui_collections)["_window"] = ...`) to return a fake object whose `send_toast(title, *, undo=None)` records its arguments. Call `ui_collections.remove(collection)`: `collection.removed` is `True`, the saved value has `removed` true for it, the fake window got the title `"{name} removed"` and an `undo` callable; calling `undo()` sets `removed` back to `False` and saves. Restore `_window` in a `finally` block (FR-005)
- [X] T008 [US1] In `tests/test_collections.py` add `check_sidebar_order()` and add it to the runner: after `_reset()`, append collections named `"b"`, `"A"`, `"c"` to `collections.model` and expect `ui_collections.model` (the sorted, filtered model) to list `A, b, c` (alphabetical, ignoring case); set one collection's `removed = True` and expect it to leave `ui_collections.model` while staying in `collections.model` (FR-001)

**Checkpoint**: The five checks pass; US1 is protected.

---

## Phase 4: User Story 2 - Put games in collections and browse them (Priority: P1) Implemented

**Goal**: Lock in membership and the collection filter (FR-006, FR-007).

**Independent Test**: The two checks below pass with no change to application code.

### Tests for User Story 2

- [X] T009 [US2] In `tests/test_collections.py` add `check_collection_membership()` and add it to the runner: `Collection(game_ids=["a", "b"])` supports `in`, iteration, `add("c")`, and `discard("a")`; the `items-changed` signal (connect with `collection.connect("items-changed", callback)`) fires once for a real change and not at all when adding a game already present or discarding one that is absent
- [X] T010 [US2] In `tests/test_collections.py` add `check_collection_filter()` and add it to the runner: build `Gtk.FilterListModel(model=<Gio.ListStore of _game("a"), _game("b"), _game("c")>, filter=ui_collections.CollectionFilter())`. With no collection set, all three games are listed; after `filter.collection = Collection(game_ids=["a", "c"])` only `a` and `c`; after `collection.add("b")` all three again; after `collection.discard("a")` only `b` and `c`; after `filter.collection = None` all three (FR-007)

**Checkpoint**: Both checks pass; US1 and US2 together cover creating and browsing.

---

## Phase 5: User Story 3 - Collections last and stay correct (Priority: P2) Implemented

**Goal**: Lock in persistence and the load rules in `data-model.md`.

**Independent Test**: The four checks below pass with no change to application code.

### Tests for User Story 3

- [X] T011 [US3] In `tests/test_collections.py` add `check_save_load_round_trip()` and add it to the runner: put two collections (names, icons, games) in `collections.model`, call `collections.save()`, empty the model with `_reset()`-style code that keeps the saved value, call `collections.load()`, and expect the same names, icons, and game sets back, with the stored form being `aa{sv}` dictionaries that have the keys `name`, `icon`, `game-ids`, and `removed` (FR-010)
- [X] T012 [US3] In `tests/test_collections.py` add `check_removed_collections_do_not_return()` and add it to the runner: mark one of two saved collections removed and save; `collections.load()` must skip it and then save again so the stored value no longer contains it. Also check the undo path before a restart: set `removed = False` on a still-loaded collection, save, load, and expect it back (FR-005, FR-010)
- [X] T013 [US3] In `tests/test_collections.py` add `check_invalid_entries_warn()` and add it to the runner: store three entries where one is missing `game-ids` and one has `icon` of the wrong type; `_logged(collections.load)` must return exactly one warning per bad entry whose message starts with `Ignored invalid collection`, and the valid entry still loads (FR-011)
- [X] T014 [US3] In `tests/test_collections.py` add `check_membership_pruning()` and add it to the runner: monkeypatch `imported.get_paths` (`vars(imported)["get_paths"] = ...`) to yield `Path("imported_1.json")` only; store a collection with game ids `imported_1`, `imported_2`, `steam_620`, `lutris_9`; after `collections.load()` it must hold `imported_1`, `steam_620`, and `lutris_9` but not `imported_2` (manually added games that no longer exist are dropped; every other id is kept, installed or not). Restore `get_paths` in a `finally` block (FR-009)

**Checkpoint**: The four checks pass; US1 to US3 are protected.

---

## Phase 6: User Story 4 - Keep hidden games reachable through collections (Priority: P2) New

**Goal**: Add the "Hidden games show in Collections" preference and the rule behind it (FR-012 to FR-016, `contracts/`).

**Independent Test**: Walk `quickstart.md` scenarios 4 to 13 in a development build; automated, the checks below pass and the rule table in `contracts/visibility-rules.md` holds.

### Tests for User Story 4 (write first; confirm they fail before T021)

- [X] T015 [US4] In `tests/test_collections.py` add `check_hidden_filter_unit()` and add it to the runner: `ui_collections.HiddenInCollectionFilter()` has `collection` (a `Collection` or `None`), `enabled` (`bool`, default `False`), and `hidden_only` (`bool`, default `False`; the view lists only hidden games). `do_match()` is `True` only when `collection` is set, `enabled` is `True`, and `hidden_only` is `False`, whatever item is passed. `get_strictness()` is `Gtk.FilterMatch.ALL` in the `True` case and `Gtk.FilterMatch.NONE` otherwise. Connect to the `changed` signal and expect exactly one emission each time `collection`, `enabled`, or `hidden_only` changes value
- [X] T016 [US4] In `tests/test_collections.py` add `check_hidden_rule_table()` and add it to the runner. Build the same tree as `window.blp` has: a `Gtk.EveryFilter` containing `ui_collections.CollectionFilter()` and a `Gtk.AnyFilter` that holds `Gtk.BoolFilter(expression=Gtk.PropertyExpression.new(games.Game, None, "hidden"), invert=<not show-hidden>)` and a `HiddenInCollectionFilter` (whose `hidden_only` follows Show Hidden Games), on a `Gtk.FilterListModel(watch_items=True)` over three games: `visible`, `hidden_in` (hidden, in the collection), and `hidden_out` (hidden, not in it). Walk all eight rows of the table in `contracts/visibility-rules.md`. Note that Show Hidden Games on lists **only** hidden games, so the expected games are, for "All Games": `visible` / `visible` / `hidden_in, hidden_out` / `hidden_in, hidden_out`, and for the collection: `visible` / `hidden_in, visible` / `hidden_in` / `hidden_in` (preference off or on within each show-hidden state). With the preference off every row must equal today's behavior (SC-004)
- [X] T017 [US4] In `tests/test_collections.py` add `check_hidden_rule_live()` and add it to the runner, using the same tree: with a collection open and the preference on, hiding a visible member keeps it listed and unhiding keeps it listed (FR-016); with the preference off, hiding a member removes it at once and unhiding brings it back; flipping the preference adds or removes the hidden member at once; turning Show Hidden Games on lists only `hidden_in` and turning it off lists `hidden_in, visible` again; closing the collection removes hidden members; hiding a game never changes `Collection` membership (`"visible" in collection` stays `True`). Keep every tree alive for the length of the run (a module-level list) and end the runner with `os._exit(0)` after flushing: freeing the window's filter tree crashes GTK, with or without this feature

### Implementation for User Story 4

- [X] T018 [P] [US4] In `data/page.samuelm333.Cartridges.gschema.xml.in` add, after the `show-game-titles` key, `<key name="hidden-games-in-collections" type="b"><default>false</default></key>` laid out like the keys around it (FR-013: off by default). Run `ninja -C _build` and confirm `_build/data/gschemas.compiled` rebuilds
- [X] T019 [P] [US4] In `tests/test_settings.py` add `"hidden-games-in-collections": "b"` to the `expected_keys` dictionary and, in `check_schema_integrity`, a check that the key's default (`schema.get_key("hidden-games-in-collections").get_default_value().get_boolean()`) is `False`, raising `ValueError` with a message otherwise
- [X] T020 [US4] In `cartridges/ui/collections.py`, directly after `CollectionFilter`, add `class HiddenInCollectionFilter(Gtk.Filter)` with `__gtype_name__ = __qualname__`, a docstring, `collection = GObject.Property(type=Collection)`, `enabled = GObject.Property(type=bool, default=False)`, `hidden_only = GObject.Property(type=bool, default=False)`, an `__init__(self, **kwargs: Any)` that calls `super().__init__(**kwargs)` and connects `notify::collection`, `notify::enabled`, and `notify::hidden-only` to `lambda *_: self.changed(Gtk.FilterChange.DIFFERENT)`, `@override do_match(self, item: GObject.Object | None = None) -> bool` returning `bool(self.collection and self.enabled and not self.hidden_only)`, and `@override do_get_strictness(self) -> Gtk.FilterMatch` returning `Gtk.FilterMatch.ALL` when `do_match()` is true and `Gtk.FilterMatch.NONE` otherwise. Fully typed, no `Any` except the existing `**kwargs: Any` pattern used by the neighboring classes. Run `python3 tests/test_collections.py`; T015, T016, and T017 must now pass
- [X] T021 [US4] In `cartridges/ui/window.py` add `hidden_in_collections = GObject.Property(type=bool, default=False)` next to `show_hidden`, and in `Window.__init__`, after the `STATE_SETTINGS.bind(...)` lines, add `SETTINGS.bind("hidden-games-in-collections", self, "hidden-in-collections", Gio.SettingsBindFlags.GET)` (one way, so only Preferences writes the key). Depends on T018: binding a key that is not in the schema aborts the app
- [X] T022 [US4] In `cartridges/ui/window.blp`, in the grid's `FilterListModel`, replace the `BoolFilter { expression: expr item as <$Game>.hidden; invert: bind template.show-hidden inverted; }` entry of the `EveryFilter` with `AnyFilter { BoolFilter { expression: expr item as <$Game>.hidden; invert: bind template.show-hidden inverted; } $HiddenInCollectionFilter { collection: bind template.collection; enabled: bind template.hidden-in-collections; hidden-only: bind template.show-hidden; } }`. Keep `watch-items: true`. Depends on T020 and T021. Run `ninja -C _build`: the blueprint must compile
- [X] T023 [US4] In `cartridges/ui/preferences.blp`, in `behavior_group` after `cover_launches_game_switch`, add `Adw.SwitchRow hidden_games_in_collections_switch { title: _("Hidden games show in Collections"); tooltip-text: _("Useful for hiding launchers and tools"); }` (exact texts, no subtitle, per `contracts/preferences-ui.md`). In `cartridges/ui/preferences.py` add `hidden_games_in_collections_switch: Adw.SwitchRow = Gtk.Template.Child()` under the `# Behavior & Images` children, and add `"hidden-games-in-collections"` to the `switches` set in `_bind_switches()` (the attribute is found from the key name, so no other binding code is needed). Depends on T018

**Checkpoint**: Quickstart scenarios 4 to 13 pass in a development build.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [ ] T024 (not done in the implementing session: the real window was launched and ran with the preference on and no GTK errors, but scenarios 1 to 15 need a person at the keyboard) Walk `quickstart.md` scenarios 1 to 15 with the scratch install recipe at the top of the manual section, in a development build, and write down any scenario that fails or that you could not perform. Scenarios 7, 12, and 13 are the only check that the real `window.blp` matches the Python filter tree in the tests
- [X] T025 In `gtk-dev` run `uv run pre-commit run --all-files`, `env -u DISPLAY -u WAYLAND_DISPLAY ninja -C _build test` (14 tests, all passing), `python3 .specify/scripts/bash/check-emojis.py`, and `python3 .specify/scripts/bash/check-emojis.py --cached` after staging; fix every finding (constitution Quality Gates)
- [X] T026 Commit with `uv run git commit` (never `--no-verify`), ending each message with `Co-Authored-By: Claude <noreply@anthropic.com>`: one commit for the tests of existing behavior (T002 to T014 and the `tests/meson.build` entry), one for the preference (T015 to T023), and one for the spec artifacts under `specs/011-collections/`. Push with `git push -u origin feat/011-collections`
- [X] T027 Open the pull request into `main` with `gh pr create` (constitution: Pull Request on Implementation). Title in the repository's style, for example `feat: Hidden games show in Collections`. The body summarizes the change, links `specs/011-collections/`, lists the verification you did, and states what you did not verify (for example any quickstart scenario you could not perform) and what only GitHub can show. End the body with the line stating it was generated with Claude Code and linking to the tool

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: none.
- **Foundational (Phase 2)**: depends on Phase 1; blocks every story because all tests live in the file it creates.
- **US1, US2, US3 (Phases 3 to 5)**: each depends only on Phase 2 and none depends on another story. They change no application code.
- **US4 (Phase 6)**: depends on Phase 2 only. It does not need US1 to US3, so it can be done first.
- **Polish (Phase 7)**: depends on the stories being done; T026 depends on T024 and T025.

### Within User Story 4

- T015, T016, and T017 first (they fail until T020).
- T018 before T021 and T023 (the key must exist before anything binds it).
- T020 before T022; T021 before T022.
- T018 and T019 can run in parallel (different files).

### Parallel Opportunities

- T018 and T019 together (schema and `tests/test_settings.py`).
- Every task that edits `tests/test_collections.py` is sequential (same file), so stories 1 to 3 are parallel only if different people merge their functions into the file.

---

## Parallel Example: User Story 4

```text
# The two edits to different files that do not depend on each other:
Task: "T018 Add hidden-games-in-collections to data/page.samuelm333.Cartridges.gschema.xml.in"
Task: "T019 Add the key and default check to tests/test_settings.py"
```

---

## Implementation Strategy

### MVP First (the only change to the app)

Stories 1 to 3 protect behavior that already ships; story 4 is the whole change. The smallest shippable slice is therefore:

1. Phase 1 and Phase 2 (T001 to T003).
2. Phase 6 (T015 to T023), tests first.
3. Validate with `quickstart.md` scenarios 4 to 13, then Phase 7.

### Incremental Delivery

1. Add the protective tests for US1, US2, and US3 (T004 to T014) before or after the MVP; they pass immediately because they only describe existing behavior. If one fails, the spec's baseline claim is wrong, so fix the spec rather than the code.
2. Each story's checks are independent and can be dropped without affecting the others.

---

## Notes

- Constitution v3.0.0 applies: no new `except` clauses are needed; if one is added it must log or carry a `# silent-ok:` marker, and `tests/test_silent_failures.py` enforces it.
- No emoji in code, comments, or docs; the 21 collection icons already in `cartridges/collections.py` are functional content and stay as they are.
- `tests/test_collections.py` is the only new test file, and it must be registered in `tests/meson.build` (T003) or CI will not run it.
- The debug-logs quickstart (`specs/010-debug-logs/quickstart.md`) tells people to run `meson devenv -C _build cartridges`, which does not work; that is outside this feature and is not changed here.

---

## Phase 8: Convergence

**Purpose**: Close the gaps found by `/speckit-converge` on 2026-10-11, started by the report that the tooltip from the original request is not in the implementation.

- [ ] T028 Check the tooltip in a built development app: follow `quickstart.md` scenario 6, hover the "Hidden games show in Collections" row over its title and then over its switch, waiting 2 seconds each time, and write what you saw in the pull request. The tooltip is set in `cartridges/ui/preferences.blp` (line 26), is in the compiled `preferences.ui`, and a live `CartridgesPreferences()` reports `get_tooltip_text()` as "Useful for hiding launchers and tools" and `get_has_tooltip()` as True, but nobody has hovered it in a real window, and the user reports not seeing it. If it shows, say so and note that the user's build may predate PR #25. If it does not show, stop and ask the user whether to also show the text as the row subtitle; that reverses the spec assumption "uses the tooltip as requested" and needs `spec.md` (FR-012 and Assumptions) and `contracts/preferences-ui.md` changed first. Do not choose alone per FR-012 (partial)
- [X] T029 In `tests/test_settings.py`, in `check_schema_integrity`, add a check that the default of `hidden-games-in-collections` is `False`, next to the existing default check for `import-on-startup` (line 54): `default = schema.get_key("hidden-games-in-collections").get_default_value()`, and raise `ValueError` with a clear message if `default.get_boolean()` is not `False`. Task T019 asked for this and only the key and its type were added. Run `python3 tests/test_settings.py` after `ninja -C _build` per T019, FR-013 (partial)
