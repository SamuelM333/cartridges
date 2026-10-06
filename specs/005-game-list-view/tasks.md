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

## Phase 8: User Story 5 - Game Launch Toast Notification & Internationalization (Priority: P2)

**Goal**: Display a dismissable in-app toast notification "Launched <game name>" upon launching a game from any UI surface, with proper gettext translation and translator comment.

**Independent Test**: Launching a game via hover Play button, cover click (when inverted), or details view triggers `game.play()` and displays a dismissable `Adw.Toast` with localized text "Launched <game name>".

### Implementation for User Story 5

- [X] T023 [US5] Implement centralized `play(game: Game) -> None` in `cartridges/ui/games.py` that invokes `game.play()` and dispatches `_window().send_toast(_("Launched {}").format(game.name))` with `# Translators:` comment
- [X] T024 [US5] Update `GameActions` in `cartridges/ui/games.py` to route `"play"` action to `play(self.game)`
- [X] T025 [US5] Update `Window._show_details` in `cartridges/ui/window.py` to call `games.play(game)` when `cover-launches-game` is true
- [X] T026 [US5] Run `ninja -C _build cartridges-pot` to extract the new translatable string and verify translator comment in `po/cartridges.pot`
- [X] T027 [US5] Run Pyright strict type check and Ruff linter on `cartridges/ui/games.py` and `cartridges/ui/window.py`
- [X] T028 [US5] Run `ninja -C _build test` and verify Constitution Principle VI (Emoji-Free Standard) across all files

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
- **User Story 5 (Phase 8)**: Depends on Phase 3 and Phase 4 - delivers launch toast feedback.

### Parallel Opportunities

- T001 and T002 can run in parallel during Setup.
- T012 and T014 can be validated in parallel with User Story 1 work.
- T018, T019, T020, and T022 can run as parallel verification checks in Polish.
- T026 and T027 can run in parallel during Phase 8.

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
7. User Story 5 -> Game launch toast notification with full gettext translation
