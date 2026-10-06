# Tasks: System Color Scheme Synchronization

**Feature**: System Color Scheme Synchronization
**Branch**: `feat/006-color-scheme`
**Spec**: [spec.md](file:///var/home/samuel/Projects/cartridges/specs/006-color-scheme/spec.md)
**Plan**: [plan.md](file:///var/home/samuel/Projects/cartridges/specs/006-color-scheme/plan.md)

---

## Phase 1: Setup (Schema Cleanliness)

**Purpose**: Ensure GSettings schema is clean without unneeded theme keys

- [X] T001 Ensure `color-scheme` key is removed from `data/page.samuelm333.Cartridges.gschema.xml.in`
- [X] T002 Recompile GSettings schemas into `_build/data` using `glib-compile-schemas` inside `gtk-dev` container

---

## Phase 2: Foundational (Application Theme Synchronization)

**Purpose**: Configure Libadwaita StyleManager to follow the host system theme dynamically

**CRITICAL**: Foundational tasks must be completed before verifying UI and preferences behavior

- [X] T003 In `cartridges/application.py`, update `do_startup()` to set `self.props.style_manager.props.color_scheme = Adw.ColorScheme.DEFAULT`
- [X] T004 In `cartridges/application.py`, remove obsolete `_apply_color_scheme` and `_on_color_scheme_changed` methods and `changed::color-scheme` GSettings connection

**Checkpoint**: Application defaults to Libadwaita system color scheme synchronization on startup

---

## Phase 3: User Story 1 - System Color Scheme Synchronization (Priority: P1) - MVP

**Goal**: Automatically follow host desktop light and dark appearance in real time

**Independent Test**: Switch host desktop theme between Light and Dark mode while Cartridges is closed and while running, observing immediate visual restyling of application surfaces

### Implementation for User Story 1

- [X] T005 [P] [US1] Create automated validation test in `tests/test_settings.py` verifying that `Adw.StyleManager` defaults to `Adw.ColorScheme.DEFAULT`
- [X] T006 [US1] Validate that Cartridges windows dynamically adapt to system light and dark themes at launch and runtime per `specs/006-color-scheme/quickstart.md`

**Checkpoint**: User Story 1 functional; Cartridges synchronizes natively with system theme

---

## Phase 4: User Story 2 - Streamlined Preferences Interface (Priority: P2)

**Goal**: Present a clean Preferences dialog without redundant or non-functional theme toggles

**Independent Test**: Open Preferences > General and verify that no appearance or theme toggle group is shown

### Implementation for User Story 2

- [X] T007 [P] [US2] In `cartridges/ui/preferences.blp`, ensure `general_page` does not contain `appearance_group` or `color_scheme_group`
- [X] T008 [P] [US2] In `cartridges/ui/preferences.py`, ensure `CartridgesPreferences` does not declare `color_scheme_group` template child or binding
- [X] T009 [US2] In `tests/test_settings.py`, verify schema integrity and assert absence of `color-scheme` key

**Checkpoint**: User Story 2 functional; General preferences page remains clean and focused

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Validate compilation, formatting, typing, automated tests, and emoji compliance

- [X] T010 [P] Compile all Blueprint templates via `blueprint-compiler` inside `gtk-dev` container
- [X] T011 [P] Run Pyright static analysis in strict mode (`uv run pyright`)
- [X] T012 [P] Run Ruff linter and formatter (`uv run ruff check`, `uv run ruff format --check`)
- [X] T013 Run Meson automated test suite (`ninja -C _build test`) inside `gtk-dev` container
- [X] T014 Verify complete absence of emoji characters across all modified files and documentation per Principle VI

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Must run first to ensure clean schema definitions
- **Foundational (Phase 2)**: Depends on Phase 1; implements backend application theme synchronization
- **User Story 1 (Phase 3)**: Depends on Phase 2; verifies automated system theme synchronization
- **User Story 2 (Phase 4)**: Depends on Phase 2; streamlines preferences UI and updates schema tests
- **Polish (Phase 5)**: Runs after user story implementations to validate QA gates

### Parallel Opportunities

- T005 and T006 can run in parallel with T007 and T008 (independent files)
- T010, T011, and T012 can run concurrently in Phase 5

---

## Implementation Strategy

### MVP First (User Story 1 Only)
1. Complete Phase 1 (Schema cleanliness)
2. Complete Phase 2 (Application StyleManager configuration)
3. Complete Phase 3 (User Story 1 validation)
4. Validate MVP: Application launches and syncs with system theme

### Incremental Delivery
1. Foundation: Schema cleanup + Application style manager (Phases 1 & 2)
2. User Story 1 (MVP): Automatic system color scheme synchronization (Phase 3)
3. User Story 2: Clean preferences dialog and automated test coverage (Phase 4)
4. Polish: Full QA gates (Pyright, Ruff, Meson tests, emoji check) (Phase 5)
