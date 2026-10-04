# Tasks: SteamGridDB Cover Picker and Credentials UX

**Feature**: SteamGridDB Cover Picker and Credentials UX
**Branch**: `004-steamgriddb-picker`
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)
**Status**: Completed

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, template verification, and environment check

- [x] T001 Setup verification and blueprint compiler check in `cartridges/ui/preferences.blp` and `cartridges/ui/cover_picker.blp`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core caching and storage path infrastructure needed by cover picker and lifecycle management

- [x] T002 Verify XDG preview cache directory path conventions (`GLib.get_user_cache_dir() / "cartridges" / "previews"`) in `cartridges/utils/steamgriddb.py` and `cartridges/application.py`

---

## Phase 3: User Story 1 - Mask API Key with Visibility Toggle (Priority: P1)

**Goal**: Obscure the SteamGridDB API key input by default in Preferences and provide an eye icon toggle button to reveal/hide plaintext credentials.

**Independent Test**: Open Preferences -> SteamGridDB, verify the API key characters are masked with dots, click the eye icon to reveal plaintext, and click it again to re-mask.

### Implementation for User Story 1

- [x] T003 [US1] Change `sgdb_key_entry_row` from `Adw.EntryRow` to `Adw.PasswordEntryRow` in `cartridges/ui/preferences.blp`
- [x] T004 [US1] Update `sgdb_key_entry_row` type annotation to `Adw.PasswordEntryRow` and preserve GSettings binding in `cartridges/ui/preferences.py`
- [x] T024 [US1] Display a fixed set amount of masked characters (20 dots) fitting the input field instead of matching real string length in `cartridges/ui/preferences.py`
- [x] T025 [US1] Release focus from `sgdb_key_entry_row` when clicking away or pressing Enter/Escape in `cartridges/ui/preferences.py`
- [x] T026 [US1] Validate focus loss and fixed mask display against `specs/004-steamgriddb-picker/quickstart.md`

**Checkpoint**: User Story 1 functional and independently testable in Preferences.

---

## Phase 4: User Story 2 - Initial Loading Spinner and Dialog Presentation (Priority: P1)

**Goal**: Display an expanded cover picker dialog (at least 760x520 content area) with an immediate centered loading spinner while the first batch of candidate images is queried and downloaded, switching to a 2:3 aspect ratio candidate grid when ready, or an empty status page if no results are found.

**Independent Test**: In Game Details edit mode, click the globe button. Verify the dialog opens sized to 800x580 with a centered loading spinner immediately visible. Once the initial batch arrives, verify the spinner disappears and candidates display in 2:3 ratio without border clipping.

### Implementation for User Story 2

- [x] T005 [US2] Size cover picker dialog to 800x580 content width and height in `cartridges/ui/cover_picker.blp`
- [x] T006 [US2] Render candidate cover thumbnails in 2:3 aspect ratio (140x210) with CONTAIN fit in `cartridges/ui/cover_picker.py`
- [x] T007 [US2] Add `Gtk.Stack` with `loading` page (`Adw.Spinner initial_spinner`), `empty` page (`Adw.StatusPage status_page`), and `results` page in `cartridges/ui/cover_picker.blp`
- [x] T008 [US2] Wire stack child transitions (`loading` -> `results` or `empty`) and initial spinner display during SteamGridDB query in `cartridges/ui/cover_picker.py`

**Checkpoint**: User Story 2 displays centered loading state on launch and cleanly transitions to results.

---

## Phase 5: User Story 3 - Progressive Batch Loading Spinner (Priority: P2)

**Goal**: Display a horizontally centered loading spinner at the bottom of the candidate list while subsequent image batches are being fetched, dismissing it when fetching concludes.

**Independent Test**: Open the cover picker for a game with multiple candidate covers. Scroll down to verify a loading spinner is visible and horizontally centered below the list while further images load, and disappears once all candidates are loaded.

### Implementation for User Story 3

- [x] T009 [US3] Add vertical `Gtk.Box` holding `flowbox` and centered `Adw.Spinner bottom_spinner` in `cartridges/ui/cover_picker.blp`
- [x] T010 [US3] Control `bottom_spinner` visibility and animate during progressive candidate batch fetches in `cartridges/ui/cover_picker.py`

**Checkpoint**: User Story 3 provides progressive loading feedback without displacing existing covers.

---

## Phase 6: User Story 4 - Cover Image Caching and Expiration Management (Priority: P2)

**Goal**: Cache downloaded cover picker preview thumbnails under `$XDG_CACHE_HOME/cartridges/previews/` to enable instant subsequent loads, and purge transient cache files on application shutdown or upon TTL expiration (7 days).

**Independent Test**: Open the cover picker to download thumbnails, confirm cache files exist on disk, reopen the picker and observe instant cache hits, then close Cartridges and verify preview cache cleanup.

### Implementation for User Story 4

- [x] T011 [P] [US4] Implement `get_cached_preview`, `save_cached_preview`, and `prune_expired_previews` in `cartridges/utils/steamgriddb.py`
- [x] T012 [P] [US4] Hook application shutdown cache cleanup (`do_shutdown`) in `cartridges/application.py`
- [x] T013 [US4] Integrate preview cache lookup before network fetch in `cartridges/ui/cover_picker.py`

**Checkpoint**: User Story 4 caches previews locally and cleanly purges on exit.

---

## Phase 7: User Story 5 - Search Triggering and Validation from Game Add/Edit (Priority: P2)

**Goal**: Enforce non-empty Title validation when triggering the SteamGridDB cover button, styling the Title entry with an error indicator if empty and preventing dialog launch until valid text is entered.

**Independent Test**: Clear Title in Add/Edit Game and click the SteamGridDB button. Verify the Title entry turns red with the error class and gains focus without opening the dialog. Enter text and verify the error style clears.

### Implementation for User Story 5

- [x] T014 [US5] Validate non-empty Title before opening SteamGridDB cover picker in `cartridges/ui/game_details.py`
- [x] T015 [US5] Add `error` CSS class to `name_entry` and focus field when Title is empty in `cartridges/ui/game_details.py`
- [x] T016 [US5] Clear `error` CSS class immediately when text is typed in `cartridges/ui/game_details.py`

**Checkpoint**: User Story 5 fully verified and functioning in codebase.

---

## Phase 8: User Story 6 - Cover Selection and Staging Feedback (Priority: P2)

**Goal**: Display an active centered loading spinner over the cover preview in Game Details while a selected cover is being downloaded and processed for staging.

**Independent Test**: Select a cover from the picker dialog. Verify the cover preview in Game Details displays a centered loading spinner until image processing completes, then updates the staged preview and hides the spinner.

### Implementation for User Story 6

- [x] T017 [US6] Add `cover_loading` GObject boolean property in `cartridges/ui/game_details.py`
- [x] T018 [US6] Display centered loading spinner over cover preview widget during background download in `cartridges/ui/game-details.blp`
- [x] T019 [US6] Reset `cover_loading` to False upon download completion, error, cancel, or apply in `cartridges/ui/game_details.py`

**Checkpoint**: User Story 6 fully verified and functioning in codebase.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Quality assurance, static typing verification, and HIG compliance check

- [x] T020 [P] Run `blueprint-compiler compile` on all modified `.blp` files in `cartridges/ui/`
- [x] T021 [P] Run Pyright type checking and Ruff lint verification across all modified files
- [x] T022 Validate end-to-end scenarios against `specs/004-steamgriddb-picker/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Complete (verified).
- **Foundational (Phase 2)**: Complete.
- **User Story 1 (Phase 3)**: Complete.
- **User Story 2 (Phase 4)**: Complete.
- **User Story 3 (Phase 5)**: Complete.
- **User Story 4 (Phase 6)**: Complete.
- **User Story 5 (Phase 7)**: Complete.
- **User Story 6 (Phase 8)**: Complete.
- **Polish (Phase 9)**: Complete.

### Parallel Opportunities

- T003 (`preferences.blp`) and T004 (`preferences.py`) can be done in tandem.
- T011 (`steamgriddb.py`) and T012 (`application.py`) can be implemented in parallel.
- T020 and T021 quality checks run in parallel.

---

## Implementation Strategy

### Incremental Delivery Order

1. **Sprint 1 (Credentials)**: Implement T003 and T004 (US1 API key masking with eye toggle in Preferences).
2. **Sprint 2 (Picker Stack & Spinners)**: Implement T007, T008 (US2 initial centered spinner), and T009, T010 (US3 progressive bottom spinner).
3. **Sprint 3 (Image Caching)**: Implement T002, T011, T012, T013 (US4 preview cache and cleanup on exit).
4. **Sprint 4 (QA)**: Execute T020, T021, T022 for compile, lint, type-check, and scenario verification.

---

## Phase 10: Convergence

**Purpose**: Address convergence findings identified during review

- [x] T023 Hide pen edit icon in API key entry row in `cartridges/ui/preferences.blp` or `cartridges/ui/style.css` per US1/AC1 (partial)
