# Tasks: Port Legacy Preferences, Flatpak Discovery, and SteamGridDB Support

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, GSettings schema alignment, and resource registration.

- [x] T001 Define all preference options and keys in `data/page.samuelm333.Cartridges.gschema.xml.in` matching the GSettings preference schema model.
- [x] T002 Update Meson build settings in `data/meson.build` and `cartridges/meson.build` to compile and bundle the new Preferences UI assets.
- [x] T003 Ensure development profile schemas are aligned in `data/page.samuelm333.Cartridges.Devel.gschema.xml.in`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core Preferences Dialog skeleton and application menu triggers.

**IMPORTANT**: The Preferences Dialog skeleton must be established before any settings page logic can be wired up.

- [x] T004 Create GNOME Blueprint declaration `cartridges/ui/preferences.blp` establishing the skeleton of `CartridgesPreferences` as an `Adw.PreferencesDialog`.
- [x] T005 Create code-behind template class in `cartridges/ui/preferences.py` loading `preferences.blp` as its template child.
- [x] T006 [P] Add menu item for "Preferences" to the primary header bar hamburger menu inside `cartridges/ui/window.blp`.
- [x] T007 Register a GActions action named `preferences` in `cartridges/application.py` or `cartridges/ui/window.py` that instantiates and presents the `CartridgesPreferences` dialog.

**Checkpoint**: Foundation ready - the Preferences Dialog can be successfully opened from the primary application menu.

---

## Phase 3: User Story 3 - Configure Application Preferences and SteamGridDB Key (Priority: P0) MVP

**Goal**: Establish GSettings property bindings for main switches and text fields.

**Independent Test**: Open Preferences, toggle the general options or input text, and run `gsettings get` to verify changes are instantly written to the system database.

### Implementation for User Story 3

- [x] T008 [US3] Bind basic behavior switches in `cartridges/ui/preferences.py` using `SETTINGS.bind()`.
- [x] T009 [US3] Add the SteamGridDB API Key entry row to `cartridges/ui/preferences.blp`.
- [x] T010 [US3] Wire the SteamGridDB entry row value changes to save to `sgdb-key` GSettings key in `cartridges/ui/preferences.py`.
- [x] T011 [US3] Dynamically lock/unlock the general SteamGridDB switch row based on whether an API key is present in `cartridges/ui/preferences.py`.

**Checkpoint**: Core GSettings configuration is fully functional.

---

## Phase 4: User Story 1 - Discover and Import Flatpak Games (Priority: P1)

**Goal**: Implement the Flatpak modular game source scanning.

**Independent Test**: Toggle Flatpak scanning, run library import, and check that Flatpak-installed games populate the grid.

### Implementation for User Story 1

- [x] T012 [P] [US1] Create the Flatpak source provider in `cartridges/sources/flatpak.py` scanning `/var/lib/flatpak/app` and `~/.local/share/flatpak/app`.
- [x] T013 [US1] Parse exported `.desktop` files in `cartridges/sources/flatpak.py` to fetch application names and execution strings.
- [x] T014 [US1] Filter out non-game software, runtimes, and launchers from flatpak scanning in `cartridges/sources/flatpak.py`.
- [x] T015 [US1] Register `FlatpakSource` in `cartridges/sources/__init__.py` to integrate with dynamic source discovery.
- [x] T015a [P] [US1] Copy and register Flatpak symbolic icon `flatpak-symbolic.svg` in `data/icons/icons.gresource.xml.in`.
- [x] T015b [US1] Filter out Flatpak desktop entries in `cartridges/sources/desktop.py` by checking the X-Flatpak key to avoid duplicate game imports.

**Checkpoint**: Flatpak games are fully discoverable and launchable.

---

## Phase 5: User Story 4 - Application Behavior Customization (Priority: P1)

**Goal**: Enable closing on game launch and cover-image trigger swap.

**Independent Test**: Enable behavior options, launch games, and verify that the app closes or that cover clicks launch the game directly.

### Implementation for User Story 5

- [x] T016 [US4] Bind `exit-after-launch` switch row in `cartridges/ui/preferences.blp`.
- [x] T017 [US4] Intercept game launch in `cartridges/ui/games.py` or the main game action controller to check `exit-after-launch` and close the window if enabled.
- [x] T018 [US4] Bind `cover-launches-game` switch row in `cartridges/ui/preferences.blp`.
- [x] T019 [US4] Update library grid click handlers in `cartridges/ui/game_item.py` or the grid controller to swap cover click play actions with play button details trigger when `cover-launches-game` is true.

**Checkpoint**: Application behaviors adapt perfectly to user configurations.

---

## Phase 6: User Story 7 - Modular Source Settings (Priority: P1)

**Goal**: Add expander rows and file/folder paths pickers for all game sources.

**Independent Test**: Navigate to the Import tab, edit directories, and verify changes persist and that directory validation notices trigger.

### Implementation for User Story 6

- [x] T020 [US7] Add the standard layout of source-specific ExpanderRows and Gtk.Button folder choosers in `cartridges/ui/preferences.blp` for all supported sources (Steam, Lutris, Heroic, Itch, Legendary, Flatpak).
- [x] T021 [US7] Implement `init_source_row` in `cartridges/ui/preferences.py` to bind expansion, load and format paths, and link file pickers.
- [x] T022 [US7] Implement unresolvable path detection and warning popovers using GTK Popovers and MenuButtons in `cartridges/ui/preferences.py` (specifically matching `resolve_locations`).
- [x] T023 [US7] Handle path selection responses and display directory validation error dialogs for incorrect inputs in `cartridges/ui/preferences.py`.

**Checkpoint**: Import sources settings have 100% design and functional parity with legacy main.

---

## Phase 7: User Story 8 - Comprehensive SteamGridDB Configuration (Priority: P1)

**Goal**: Integrate full SteamGridDB settings and async bulk cover update button.

**Independent Test**: Fill in the key, click "Update Covers", and check that the spinner runs and the asynchronous process executes without blocking the UI.

### Implementation for User Story 7

- [x] T024 [US8] Add SteamGridDB toggles (Prefer SGDB, Animated) and the manual "Update Covers" row with Gtk.Stack and Adw.Spinner in `cartridges/ui/preferences.blp`.
- [x] T025 [US8] Bind the new SteamGridDB GSettings switches in `cartridges/ui/preferences.py`.
- [x] T026 [US8] Implement `update_sgdb` in `cartridges/ui/preferences.py` to process bulk cover updates asynchronously using background GLib/Python thread pools.
- [x] T027 [US8] Create and display download progress Adw.Toast indicators during bulk fetching in `cartridges/ui/preferences.py`.

**Checkpoint**: SteamGridDB preferences page is fully implemented.

---

## Phase 8: User Story 2 - Fetch and Choose Cover Art from SteamGridDB (Priority: P1)

**Goal**: Implement individual cover picker and API query operations.

**Independent Test**: Open individual cover picker, search results, select one, and check that the grid refreshes.

### Implementation for User Story 8

- [x] T028 [US2] Create or adapt the SteamGridDB client queries (autocomplete search, grid retrieval, file download) asynchronously in `cartridges/utils/steamgriddb.py`.
- [x] T029 [US2] Create the Cover Selector layout in `cartridges/ui/cover_picker.blp` to browse retrieved images.
- [x] T030 [US2] Implement the selection actions and image caching callbacks in `cartridges/ui/cover_picker.py`.

**Checkpoint**: Individual cover selection and download is fully operational.

---

## Phase 9: User Story 5 - Image Quality Control (Priority: P2)

**Goal**: Respect high quality setting when saving artwork.

**Independent Test**: Save a cover with high-quality off and on, and inspect file size and compression formats in the local directory.

### Implementation for User Story 9

- [x] T031 [US5] Bind `high-quality-images` switch row in `cartridges/ui/preferences.blp`.
- [x] T032 [US5] Update the image conversion and saving logic (e.g. in `cartridges/utils/save_cover.py` or cover loading utilities) to apply optimization compression levels when `high-quality-images` is disabled.

**Checkpoint**: Cover image storage is correctly optimized based on quality settings.

---

## Phase 10: User Story 6 - Settings and Library Safety Control (Danger Zone) (Priority: P2)

**Goal**: Danger Zone destructive commands with verification modals.

**Independent Test**: Clear library, confirm deletion, verify database is cleared, and test Undo toast.

### Implementation for User Story 10

- [x] T033 [US6] Add the Danger Zone group containing **Remove All Games** and **Reset App** in `cartridges/ui/preferences.blp`.
- [x] T034 [US6] Implement **Remove All Games** logic in `cartridges/ui/preferences.py`, marking all games as removed and saving.
- [x] T035 [US6] Implement the Adw.Toast undo controller action and keybindings in `cartridges/ui/preferences.py` to reverse deletion.
- [x] T036 [US6] Implement **Reset App** logic in `cartridges/ui/preferences.py` to wipe user application folders, reset GSettings, and exit.
- [x] T037 [US6] Wire Gtk.AlertDialog confirmation prompts to both buttons to prevent accidental execution.

**Checkpoint**: Danger Zone commands are highly secure, undoable, and fully functional.

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Linting, typing correctness, and final scenario validations.

- [x] T038 Verify type correctness of all added/modified modules using Pyright.
- [x] T039 Clean up code formatting and run Ruff.
- [x] T040 Complete all manual validation test scenarios in `quickstart.md`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Can start immediately.
- **Foundational (Phase 2)**: Depends on Phase 1 - MUST complete before any user stories can be implemented.
- **User Story 3 (P0)**: Depends on Phase 2 - Blocking prerequisite for all remaining settings rows.
- **Remaining User Stories (Phases 4-10)**: Depend on User Story 3 completion.
- **Polish (Phase 11)**: Runs once all user stories are complete.

### Within Each User Story
- Models/logic layer implemented before controller/view bindings.
- Checkpoints completed and verified before proceeding to subsequent stories.

---

## Parallel Opportunities

- Within Phase 1, T002 and T003 can run in parallel.
- Within Phase 2, T006 and T007 can run in parallel.
- T012 (Flatpak source logic) is independent and can be developed in parallel with UI-only tasks.
- Static typing and formatting checks (Phase 11) can run continuously.

---

## Implementation Strategy

### MVP Scope (User Stories 3 & 1)
1. Complete Setup and Foundational skeleton.
2. Complete US3 (Basic switch bindings and API Key controls).
3. Complete US1 (Modular Flatpak Game Source discovery).
4. Run independent verification scans to confirm Flatpak games discover, launch, and settings save.
5. Incrementally add remaining behavior customization, modular directories, SteamGridDB asynchronous updates, and Danger Zone actions in subsequent steps.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

---

## Phase 12: Convergence

- [x] T041 Update source expander row icon names in `cartridges/ui/preferences.blp` from `*-source-symbolic` to `*-symbolic` per FR-023 (contradicts)
- [x] T042 Wire up `CoverPicker` entry point in `cartridges/ui/game_details.py` and `cartridges/ui/game-details.blp` with missing API key alert per FR-006, US2 (partial)
- [x] T043 Import gettext `_` and render cover thumbnail previews in `cartridges/ui/cover_picker.py` per FR-006, US2/AC1 (partial)
- [x] T044 Increment `success_count` on successful cover save in `cartridges/ui/preferences.py` per FR-020, US8/AC3 (partial)

---

## Phase 13: Convergence

- [x] T045 Initialize standard logging in `cartridges/__main__.py` and log requests/failures in `cartridges/utils/steamgriddb.py` and `cartridges/ui/preferences.py` per Constitution I (missing)
- [x] T046 Add progress box with progress bar and status label under "Update Covers" in `cartridges/ui/preferences.blp` per FR-025, US8/AC3 (missing)
- [x] T047 Update `_update_sgdb_covers` in `cartridges/ui/preferences.py` to update the progress bar and current game label in real time as each game is scanned per FR-025, US8/AC3 (missing)
- [x] T048 Handle SteamGridDB authentication (401) and network errors with specific toasts/alerts instead of silent swallow in `cartridges/ui/preferences.py` per FR-020, US8/AC3 (partial)
- [x] T049 Implement background automatic cover fetching on game discovery/startup in `cartridges/sources/__init__.py` when SteamGridDB is enabled per FR-005, US8/AC1 (missing)

---

## Phase 14: Cover Management Panel & Preferences Status Banner

- [x] T050 [US2] Revert `cartridges/ui/game-details.blp` to legacy cover overlay layout with direct action buttons: pencil button (`document-edit-symbolic`), globe button (`globe-symbolic`), and trash button (`user-trash-symbolic`, revealed when a cover is present) per FR-006, FR-026, SC-013.
- [x] T051 [US2] Implement staged cover editing in `cartridges/ui/game_details.py`: stage local image selection, SGDB selection, and cover removal in memory so preview updates immediately in Edit mode; commit changes to disk only upon `details.apply`; cleanly revert without disk changes upon `details.cancel` per FR-006, FR-026, FR-028, SC-013.
- [x] T052 [US2] Limit SteamGridDB cover candidate queries to 10 images in `cartridges/ui/cover_picker.py` per US2.
- [x] T053 [US8] Add dismissable `sgdb_status_row` under Update Covers in `cartridges/ui/preferences.blp` and `cartridges/ui/preferences.py` per FR-027.
- [x] T054 Preserve original cover art prior to overwriting in `cartridges/utils/steamgriddb.py` `save_cover_from_url` per FR-028.

---

## Phase 15: Convergence

- [x] T055 [US2] Update cover overlay buttons in `cartridges/ui/game-details.blp`: change pencil icon to folder icon (`folder-symbolic`) with tooltip "Browse files", and change globe tooltip to "Browse SteamGridDB" per FR-006, SC-013 (contradicts)
- [x] T056 [US2] Ensure the Browse files folder button remains always active in Edit mode, including when adding a new game, supporting local image selection before a game instance is committed per FR-026, FR-029, SC-015 (missing)
- [x] T057 [US2] Enforce Title requirement for SteamGridDB cover button in `cartridges/ui/game_details.py` and `cartridges/ui/game-details.blp`: only activate SteamGridDB search when the Title field is non-empty; if clicked without Title, add `error` CSS styling to `name_entry` and focus it, removing the error style once Title has text per FR-029, SC-015 (missing)
- [x] T058 [US2] Fix cover image staging persistence on apply in `cartridges/ui/game_details.py`: guard `_on_game_changed` during `_apply()` to prevent synchronous reset of staged cover, ensuring staged file is moved to final covers directory and linked to game before exiting apply per FR-026, SC-013 (bugfix)

---

## Phase 16: Convergence - Cover Picker Sizing & Full Image Framing

- [x] T059 [US2] Increase CoverPicker dialog dimensions in `cartridges/ui/cover_picker.blp` to `content-width: 800; content-height: 580;` relative to the main app window (920x700) per FR-030, SC-016.
- [x] T060 [US2] Ensure complete cover image and border visibility in `cartridges/ui/cover_picker.py`: set picture size request to 140x210 (2:3 aspect ratio), use `Gtk.ContentFit.CONTAIN` or padding so that borders are never cut/clipped, and keep the full artwork perimeter cleanly visible per FR-030, SC-016.

---

## Phase 17: Convergence - Cover Overlay Loading Spinner

- [x] T061 [US2] Add centered `Adw.Spinner` child to cover `Overlay` in `cartridges/ui/game-details.blp`, bound to `template.cover-loading` with `halign: center; valign: center;` per FR-031, SC-017.
- [x] T062 [US2] Add `cover_loading` GObject boolean property in `cartridges/ui/game_details.py`, set to `True` during SteamGridDB background download and reset to `False` upon completion, failure, cancel, or apply per FR-031, SC-017.
