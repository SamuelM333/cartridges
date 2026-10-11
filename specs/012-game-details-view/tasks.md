# Tasks: Game Details View

**Input**: Design documents from `specs/012-game-details-view/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/toast-routing.md, quickstart.md

**Tests**: No new automated test (plan and research R4: the behavior is widget state, and CI has no display). Every story is checked with the quickstart scenarios named in its phase. The existing meson tests must keep passing.

**Organization**: User stories 1, 3, and 4 record existing behavior, so their phases only verify it. User story 2 is the only code change.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: The user story the task belongs to (US1 to US4)

## Path Conventions

Single desktop app: source in `cartridges/ui/`, tests in `tests/`, build in `_build/`. Run every command inside the `gtk-dev` Distrobox container.

---

## Phase 1: Setup

**Purpose**: A working build and a hook that runs in the project environment.

- [X] T001 Inside `gtk-dev`, run `uv run pre-commit install`, then `meson setup _build --reconfigure && ninja -C _build && ninja -C _build test`, and confirm all tests pass on the unchanged branch `feat/012-game-details-view` (constitution: Hook Setup, Failures Already on main). If a test already fails, stop and report it before changing code

---

## Phase 2: Foundational

None. The only shared piece, the details page's toast overlay, is used by user story 2 alone and is built there.

---

## Phase 3: User Story 1 - See a game's details (Priority: P1)

**Goal**: Confirm the recorded viewing behavior (FR-001, FR-002, FR-004).

**Independent Test**: quickstart scenarios 7, 8, and 12.

- [ ] T002 [US1] (not done in the implementing session: needs a person at the keyboard) With the build from T001, run `_build/cartridges/cartridges` and walk `specs/012-game-details-view/quickstart.md` scenarios 7 (developer line only when set, "Last played: Never" for a never-played game), 8 (below 700 pixels the cover, text, and actions stack and center), and 12 (Escape returns to the library). Write down any difference from `spec.md` user story 1; do not change code for it in this feature without asking

**Checkpoint**: User story 1 behavior is confirmed as recorded.

---

## Phase 4: User Story 2 - Launch from details and see it confirmed there (Priority: P1) MVP

**Goal**: A toast appears only in the view that was showing when it was raised, and the details view's toasts leave with it (FR-009 to FR-013), per `contracts/toast-routing.md`.

**Independent Test**: quickstart scenarios 1 to 6.

- [X] T003 [P] [US2] In `cartridges/ui/game-details.blp`, change the details page's `Adw.ToolbarView` content (line 82, `content: ScrolledWindow {`) so the existing `ScrolledWindow` becomes the child of a new overlay: `content: Adw.ToastOverlay toast_overlay { child: ScrolledWindow { ... }; };`, keeping every property and child of the `ScrolledWindow` unchanged. In the template header, add `hiding => $_dismiss_toasts();` on the line after `hidden => $_cancel();`. Then run `blueprint-compiler format --fix --no-diff cartridges/ui/game-details.blp` (research R2, R3)
- [X] T004 [US2] In `cartridges/ui/game_details.py`, add the template child `toast_overlay: Adw.ToastOverlay = Gtk.Template.Child()` next to `name_entry`, and add a template callback before `_cancel` (line 176): `@Gtk.Template.Callback()` `def _dismiss_toasts(self, *_args: Any) -> None:` whose body is `self.toast_overlay.dismiss_all()`. Do not change `_cancel`. Depends on T003 (the template must define `toast_overlay` and `_dismiss_toasts`), per FR-011
- [X] T005 [P] [US2] In `cartridges/ui/window.py`, in `Window.send_toast` (line 127), replace `self.toast_overlay.add_toast(toast)` with a choice of overlay: use `self.details.toast_overlay` when `self.navigation_view.props.visible_page is self.details`, otherwise `self.toast_overlay`, then call `add_toast(toast)` on it. Keep the signature, the docstring's meaning, `use_markup=False`, the Undo button, priority, and the `self._history[toast] = undo` entry exactly as they are. Do not change any caller of `send_toast` (research R1, R5; FR-010, FR-012, FR-013). The attribute is only read at call time, so this can be written in parallel with T003 and T004, but it needs both before it runs
- [X] T006 [US2] (done 2026-10-11 by driving the installed development build from a script, `/tmp/h012/harness.py`, not by hand: scenarios 1 to 5 gave the expected overlay for every toast and printed no GTK warning; scenario 6 was not performed) Rebuild with `ninja -C _build && ninja -C _build test`, run `_build/cartridges/cartridges`, and walk `specs/012-game-details-view/quickstart.md` scenarios 1 to 5 (and 6 if a read-only data directory is practical). Expected results are in the quickstart. Note any GTK warning printed to the terminal. Depends on T003, T004, T005

**Checkpoint**: Launching from the details view shows "Launched <game name>" there, and no toast crosses between the two views.

---

## Phase 5: User Story 3 - Edit a game (Priority: P2)

**Goal**: Confirm editing still behaves as recorded after the overlay was added around the scrolled content (FR-005, FR-006).

**Independent Test**: quickstart scenarios 9 and 10.

- [ ] T007 [US3] (not done in the implementing session: needs a person at the keyboard) In the build from T006, walk quickstart scenarios 9 (Enter applies, the library shows the new title, Apply unavailable with an empty Title or Executable) and 10 (Escape discards field changes and restores a deleted cover). Also open the Executable info popover and the SteamGridDB button with an empty Title, per `spec.md` user story 3 scenarios 6 and 7. Depends on T006

---

## Phase 6: User Story 4 - Manage a game from its details (Priority: P2)

**Goal**: Confirm Hide, Unhide, Remove, Collections, and Search On behave as recorded (FR-003, FR-007, FR-008).

**Independent Test**: quickstart scenarios 5 and 11.

- [ ] T008 [US4] (not done in the implementing session: needs a person at the keyboard) In the build from T006, walk quickstart scenario 11 (Collections shows "New Collection" and the toggles; Search On opens the site in the browser), and check that a hidden game's details show Unhide instead of Hide (`spec.md` user story 4 scenario 2). Scenario 5 was already walked in T006. Depends on T006

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T009 Run `uv run ruff check cartridges/ui/game_details.py cartridges/ui/window.py`, `uv run ruff format --check cartridges/ui/game_details.py cartridges/ui/window.py`, and `uv run pyright cartridges/ui/game_details.py cartridges/ui/window.py` inside `gtk-dev`; fix every finding (constitution I). Depends on T004, T005
- [X] T010 [P] Run `python3 .specify/scripts/bash/check-emojis.py` and `uv run pre-commit run --all-files` inside `gtk-dev`; both must pass (constitution VI and Quality Gates). Depends on T003 to T005
- [X] T011 Commit with `uv run git commit` inside `gtk-dev` (never `--no-verify`), each message ending with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`: one commit for the spec artifacts under `specs/012-game-details-view/` (`docs: Add the game details view specification, plan, and tasks`) and one for the code (`fix: Show toasts in the view they were sent from`). Push with `git push -u origin feat/012-game-details-view`. Depends on T006 to T010
- [X] T012 (done 2026-10-11: pull request #27) Open the pull request into `main` with `gh pr create` (constitution: Pull Request on Implementation). The body summarizes the change, links `specs/012-game-details-view/`, lists the quickstart scenarios walked and their results, states which were not performed, and states that there is no new automated test (research R4). End the body with the line stating it was generated with Claude Code and linking to the tool. Depends on T011

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Empty.
- **US1 (Phase 3)**: Depends on T001. Can run before or after US2; if before, it checks the page before the overlay change, so repeat scenario 8 after T006.
- **US2 (Phase 4)**: Depends on T001.
- **US3 (Phase 5)** and **US4 (Phase 6)**: Depend on T006, because they check that the overlay change did not break the page.
- **Polish (Phase 7)**: Depends on all user story phases.

### Within User Story 2

```text
T003 (blp) -> T004 (game_details.py) -\
T005 (window.py) ----------------------+-> T006 (build + quickstart 1-6)
```

### Parallel Opportunities

- T003 and T005 touch different files and can be written at the same time.
- T002 (US1 walk-through) can run while T003 to T005 are written, on the build from T001.
- T007 and T008 can be walked in the same session after T006.
- T009 and T010 can run in parallel.

### Parallel Example: User Story 2

```text
Agent A: T003 then T004  (cartridges/ui/game-details.blp, cartridges/ui/game_details.py)
Agent B: T005            (cartridges/ui/window.py)
Then:    T006            (build and quickstart scenarios 1-6)
```

---

## Implementation Strategy

### MVP First (User Story 2)

User story 2 is the only code change and fixes the reported problem. The smallest shippable slice is T003 to T006: the overlay, the dismiss on leaving, and the routing in `send_toast`, checked with quickstart scenarios 1 to 5.

### Incremental Delivery

1. T001: build and tests green on the unchanged branch.
2. T003 to T006: toasts follow the view (MVP).
3. T002, T007, T008: confirm the recorded behavior of user stories 1, 3, and 4 still holds.
4. T009 to T012: gates, commits, pull request.
