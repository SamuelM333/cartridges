# Feature Specification: Game Details View

**Feature Branch**: `feat/012-game-details-view`

**Created**: 2026-10-11

**Status**: Draft

**Input**: User description: "Game details view: capture the current implementation of the game details page in a spec. New requirement: the \"Launched <game name>\" toast must show in the game details view when the game is launched from there, and each notification must remain in the view it was shown in (a details-page toast does not appear on the grid after going back, and a grid toast does not appear over the details page)."

## Overview

The game details view is the page a player opens from a game in the library to see it on its own, launch it, change it, or manage it. This specification does two things:

1. It records how the details view already behaves (user stories 1, 3, and 4), so later changes can be checked against it.
2. It fixes one gap (user story 2, marked **New**): today a game launched from the details view shows no "Launched <game name>" notification, because notifications are only shown in the library view. After this change a notification appears in the view the player is looking at, and it stays in that view.

Current behavior, in short:

- **Opening**: The details view opens from a game in the library (clicking its cover, or its Info button when "Cover image launches game" is on); "Edit" in a game's options menu opens it straight in edit mode. It slides in over the library; the back button or Escape returns to the library.
- **Content**: A blurred, more saturated version of the game's cover fills the background, faded in the light style and darkened in the dark style (more so with high contrast). In front of it are the cover, the game's title, its developer (only when there is one), "Last played: {}" and "Added: {}" as relative dates (for example "Today", "Yesterday", "Last Week", "Never"), and a row of actions.
- **Actions**: Play, Edit, Collections, Hide or Unhide (whichever applies), Remove, and Search On (HowLongToBeat, IGDB, Lutris, PCGamingWiki, ProtonDB, SteamGridDB). Each icon button has a tooltip naming its action.
- **Editing**: Edit switches the page to a form with Title, Developer (optional), and Executable, plus cover buttons (browse files, browse SteamGridDB, delete cover). Nothing changes until Apply; Cancel or Escape throws the changes away.
- **Narrow windows**: Below 700 pixels wide, the cover and the text stack vertically and are centered.

Adding a new game manually uses the same page in edit mode with the title "Add Game"; that flow is specified in `specs/009-manual-game-add/`. Choosing a cover from SteamGridDB is specified in `specs/004-steamgriddb-picker/`. Both are referred to here, not specified again.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See a game's details (Priority: P1)

A player wants to look at one game: its cover, full title, developer, and when they last played it and added it.

**Why this priority**: It is the reason the page exists, and every other story starts from it.

**Independent Test**: Open the details of a game that has a developer and has been played, then of one without a developer that was never played, and compare what is shown.

**Acceptance Scenarios**:

1. **Given** the library, **When** the user clicks a game's cover (with "Cover image launches game" off), **Then** the details view of that game opens over the library with its cover, title, and dates.
2. **Given** "Cover image launches game" is on, **When** the user clicks the game's Info button, **Then** the details view of that game opens.
3. **Given** a game with a developer, **When** its details view is open, **Then** the developer is shown under the title; **Given** a game without one, **Then** no developer line is shown.
4. **Given** a game that was never launched, **When** its details view is open, **Then** it shows "Last played: Never".
5. **Given** the details view, **When** the user presses the back button or Escape, **Then** the library is shown again as it was.
6. **Given** a window narrower than 700 pixels, **When** the details view is open, **Then** the cover, text, and actions are stacked vertically and centered.

---

### User Story 2 - Launch a game from its details and see it confirmed there (Priority: P1) **New**

A player opens a game's details, reads them, and presses Play. They expect the same "Launched <game name>" notification they get in the library, shown where they are looking.

**Why this priority**: Launching is the main thing players do, and today a launch from the details view gives no feedback at all, so a player cannot tell whether the click worked.

**Independent Test**: Launch a game from its details view and check that the notification appears there; go back and check it is not in the library; launch from the library and check the notification appears there and not on a details view opened afterwards.

**Acceptance Scenarios**:

1. **Given** a game's details view, **When** the user presses Play, **Then** the game launches and a dismissable notification "Launched <game name>" appears in the details view.
2. **Given** that notification is showing in the details view, **When** the user goes back to the library, **Then** the notification is not shown in the library.
3. **Given** a game was launched from the library and its notification is showing there, **When** the user opens a game's details view, **Then** that notification is not shown over the details view.
4. **Given** a notification was shown in the details view of one game, **When** the user goes back and opens the details view of the same or another game, **Then** the earlier notification is no longer shown.
5. **Given** the details view, **When** the user hides or removes the game, **Then** the view returns to the library and the "{name} hidden" or "{name} removed" notification with Undo appears in the library, as it does today.

---

### User Story 3 - Edit a game (Priority: P2)

A player corrects a game's title, adds its developer, fixes its executable, or changes its cover.

**Why this priority**: Imported data is sometimes wrong or missing, and this is the only place to fix it, but it is needed less often than viewing and launching.

**Independent Test**: Edit each field and the cover, apply, and check the result; edit again and cancel, and check nothing changed.

**Acceptance Scenarios**:

1. **Given** the details view, **When** the user presses Edit, **Then** a form with Title, Developer (optional), and Executable appears, filled with the game's current values, and the Title field has focus.
2. **Given** the form, **When** Title or Executable is empty, **Then** Apply is not available.
3. **Given** valid changes, **When** the user presses Apply or Enter in a field, **Then** the changes are kept, the page shows the details again, and the library reflects the new title.
4. **Given** the form with changes, **When** the user presses Cancel or Escape, **Then** the changes are discarded and the details are shown unchanged.
5. **Given** the form, **When** the user chooses a cover from files or SteamGridDB, or deletes the cover, **Then** the new cover is previewed but only takes effect on Apply; Cancel restores the previous cover.
6. **Given** the form, **When** the user browses SteamGridDB with an empty Title, **Then** the Title field is marked as an error and focused; **Given** no SteamGridDB API key is set, **Then** a dialog explains that a key is required and offers to open Preferences.
7. **Given** the form, **When** the user opens the Executable info button, **Then** a short explanation shows how to write a command for an executable and for a file opened with the default application, for the current operating system.
8. **Given** a manually added game whose changes cannot be saved, **When** the user applies, **Then** a notification says the game could not be saved and will be lost when Cartridges closes, shown in the details view.

---

### User Story 4 - Manage a game from its details (Priority: P2)

A player hides, unhides, removes, or files a game into collections, or looks it up on a game website, without going back to the library.

**Why this priority**: These actions are also in the library's options menu, so the details view is a convenience rather than the only way.

**Independent Test**: From a details view, use each action and check the result in the library.

**Acceptance Scenarios**:

1. **Given** a visible game's details view, **When** the user presses Hide, **Then** the game is hidden, the view returns to the library, and a notification offers Undo.
2. **Given** a hidden game's details view, **Then** Unhide is shown instead of Hide, and pressing it unhides the game.
3. **Given** a game's details view, **When** the user presses Remove or the Delete key, **Then** the game is removed, the view returns to the library, and a notification offers Undo.
4. **Given** a game's details view, **When** the user opens Collections, **Then** it offers "New Collection" and one toggle per collection, as specified in `specs/011-collections/`.
5. **Given** a game's details view, **When** the user picks a site from Search On, **Then** the site's search for the game's title opens in the default web browser.

---

### Edge Cases

- **Several launches in a row**: Pressing Play repeatedly in the details view shows a notification for each launch in that view, as the library does.
- **Notification from a different source while on the details view**: Any notification raised while the details view is showing (for example the "could not be saved" warning after Apply) appears in the details view, not in the hidden library.
- **Leaving with a notification showing**: Going back to the library dismisses the details view's notifications; they are not shown again when a details view is next opened.
- **Library notifications while the details view is open**: A notification that was showing in the library when the details view opened is not shown over the details view. When the user returns to the library it may still be showing if its normal display time has not run out.
- **Hide or remove from the details view**: The view returns to the library first, so these notifications, with their Undo button, appear in the library, where the change is visible.
- **Game removed elsewhere while its details are open**: The view returns to the library, as it does today.
- **Game title with special characters**: The notification shows the title as plain text, never interpreted as markup.

## Requirements *(mandatory)*

### Functional Requirements

**Current behavior (recorded)**

- **FR-001**: The details view MUST open for a game from the library's cover click (with "Cover image launches game" off), and from the Info button (with it on); "Edit" in the game's options menu MUST open it in edit mode; the view MUST return to the library with the back button or Escape.
- **FR-002**: The details view MUST show the game's cover, a blurred version of the cover as background, the title, the developer only when the game has one, and the last-played and added dates as relative dates ("Never" when never played).
- **FR-003**: The details view MUST offer Play, Edit, Collections, Hide or Unhide (only the one that applies), Remove, and Search On with the six sites HowLongToBeat, IGDB, Lutris, PCGamingWiki, ProtonDB, and SteamGridDB; icon-only buttons MUST have tooltips.
- **FR-004**: Below 700 pixels of window width, the details view MUST stack and center its cover, text, and actions.
- **FR-005**: Edit MUST show a form with Title, Developer (optional), and Executable filled with the current values; Apply MUST be unavailable while Title or Executable is empty; Apply or Enter MUST keep the changes; Cancel or Escape MUST discard them.
- **FR-006**: Cover changes (choose from files, choose from SteamGridDB, delete) MUST be previewed in the form and MUST take effect only on Apply.
- **FR-007**: Hide and Remove (button or Delete key) MUST return the view to the library and show a notification with Undo in the library.
- **FR-008**: Search On MUST open the chosen site's search for the game's title in the default web browser.

**Notifications (new)**

- **FR-009**: Launching a game from the details view MUST show the dismissable notification "Launched <game name>" in the details view, with the same translatable text as a launch from the library.
- **FR-010**: A notification MUST appear only in the view that is showing when it is raised: the details view or the library. It MUST NOT appear in the other view at any time.
- **FR-011**: Leaving the details view MUST dismiss the notifications shown in it, so they do not reappear when a details view is opened again.
- **FR-012**: Notifications raised by actions that return to the library first (Hide, Remove) MUST appear in the library with their Undo button, as today.
- **FR-013**: Launching from the library MUST keep its current behavior: the notification appears in the library.

### Key Entities

- **Game**: The game shown in the details view: title, developer, executable, cover, last-played and added dates, and its hidden and removed states.
- **Notification**: A short, dismissable message about an action the user just took, optionally with Undo. It belongs to the view it was shown in.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In 100% of launches from the details view, the "Launched <game name>" notification is visible in the details view within 100 milliseconds of pressing Play.
- **SC-002**: In 0 cases does a notification shown in one view appear in the other view, across launching, hiding, removing, and going back and forth between the views.
- **SC-003**: A player can launch a game from its details view and see confirmation in 1 action (press Play).
- **SC-004**: Every behavior recorded in FR-001 to FR-008 is unchanged after the notification change, checked by walking user stories 1, 3, and 4.

## Assumptions

- "Notification" means the in-app toast at the bottom of the view, as used in the library; no desktop notifications are involved.
- The rule applies to every notification, not only the launch one, because the user asked that each notification remain in its view. In practice the launch notification and the "could not be saved" warning are the ones raised while the details view is showing.
- Dismissing the details view's notifications when leaving it (FR-011) is the chosen reading of "remain in its view": a notification about one visit should not show up on the next one. The library keeps its notifications while the details view is open, because the library is still the page underneath and its Undo notifications must stay usable.
- Hide and Remove keep returning to the library before their notification is shown, so their Undo stays in the view where the change is visible.
- Adding a game manually (`specs/009-manual-game-add/`) and the SteamGridDB cover picker (`specs/004-steamgriddb-picker/`) are out of scope except where they share this page.
- The launch notification's wording and translation are defined in `specs/005-game-list-view/` (FR-012, FR-013) and are reused unchanged.
