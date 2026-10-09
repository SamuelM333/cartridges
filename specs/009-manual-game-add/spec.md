# Feature Specification: Manual Game Add

**Feature Branch**: `feat/009-manual-game-add`

**Created**: 2026-10-09

**Status**: Draft

**Input**: User description: "new feat: manual game add. manually added games must persist app restarts like game imports"

## Overview

Users can add a game by hand: they choose "Add Game", type a name and the command that starts it, optionally add a developer and a cover, and apply. The game then appears in the library like any other. This specification defines that flow and, above all, the requirement that a manually added game is still there, with everything the user entered, after the application is closed and reopened, just as games found by an import are.

Today the game appears in the library for the current session, but nothing records the name, command, developer, or later edits of a manually added game at the moment the user applies them. A manually added game can therefore be lost on restart, and a second game added in the same session can be mistaken for the first. This feature closes that gap.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A Manually Added Game Survives a Restart (Priority: P1)

As a player whose game is not found by any launcher, I want to add it by hand and find it in my library every time I open Cartridges, so that I do not have to add it again.

**Why this priority**: A manual game that disappears on restart makes the feature unusable. Persistence is the whole point of this request.

**Independent Test**: Add a game with a name, command, developer, and cover; close and reopen the application; confirm the game is in the library with all of those values and launches.

**Acceptance Scenarios**:

1. **Given** the library has no manually added games, **When** the user adds a game with a name and a command and applies, **Then** the game appears in the library immediately.
2. **Given** the user has just added a game, **When** the application is closed and reopened, **Then** the game is in the library with the same name, command, developer, cover, and date added.
3. **Given** a manually added game was restored after a restart, **When** the user launches it, **Then** it runs the saved command and the launch toast and "Last Played" sorting behave as for any other game.
4. **Given** the user adds a game and the application is closed right away (including by "Exit After Launching Games" or a forced quit after the game was applied), **When** the application is reopened, **Then** the game is still there.
5. **Given** "Import Games on Startup" is turned off, **When** the application is reopened, **Then** manually added games are still shown, since they do not depend on any launcher or import.
6. **Given** the user runs "Import Now" or a startup import, **When** the import finishes, **Then** manually added games are unchanged and are not duplicated or removed.

---

### User Story 2 - Edits and State Changes Persist (Priority: P1)

As a player who corrected a typo in a game's command or gave it new artwork, I want those changes to be remembered, so that I do not have to fix the game again after every restart.

**Why this priority**: A game that returns to its old values after a restart is as frustrating as one that disappears, and it is the same persistence gap.

**Independent Test**: Edit a manually added game's name, command, developer, and cover; reopen the application; confirm every edit is still applied.

**Acceptance Scenarios**:

1. **Given** a manually added game, **When** the user edits its name, command, or developer and applies, **Then** after a restart the new values are shown and the old ones are gone.
2. **Given** a manually added game with a cover, **When** the user replaces or removes the cover and applies, **Then** after a restart the change is still in effect.
3. **Given** the user edits a game but cancels, **When** the application is reopened, **Then** the game has its previous values.
4. **Given** a manually added game, **When** the user hides it, plays it, or adds it to a collection, **Then** after a restart it is still hidden, still ordered by its last-played time, and still in that collection.
5. **Given** a manually added game, **When** the user removes it, **Then** it stays removed after a restart, and "Undo" in the removal toast restores it, also across a restart.

---

### User Story 3 - Several Added Games Stay Distinct (Priority: P2)

As a player adding a handful of games in one sitting, I want each one to be remembered separately, so that adding one game never overwrites or replaces another.

**Why this priority**: Without this, adding several games in a row can silently merge them into one, which loses data and is hard to notice. It follows from correct persistence, but it is a separate failure that needs its own check.

**Independent Test**: Without restarting, add three games with different names and commands, restart, and confirm all three are present with the right values.

**Acceptance Scenarios**:

1. **Given** the user adds game A and then game B in the same session, **When** the application is restarted, **Then** both A and B are in the library with their own names and commands.
2. **Given** the user removed a manually added game earlier, **When** they add a new game, **Then** the new game does not take over the removed game's identity, so the removed game cannot reappear with the new game's details.
3. **Given** two games are added in quick succession, **When** both are applied, **Then** both are saved and neither overwrites the other.

---

### User Story 4 - A Failed Save Is Visible and Harmless (Priority: P3)

As a player whose data folder is full, read-only, or restricted by the sandbox, I want to be told when a game I added could not be saved, so that I know it will not be there next time and can fix the problem.

**Why this priority**: Failures are rare, but silently losing something the user just typed is worse than for background data such as play times. It is a safeguard, not the main flow.

**Independent Test**: Make the data folder unwritable, add a game, and confirm the game is usable for the session, a clear notice appears, and nothing else breaks.

**Acceptance Scenarios**:

1. **Given** the game cannot be saved, **When** the user applies a new game, **Then** the game still appears and works for the rest of the session, and a dismissable in-app notice says it could not be saved and will be lost when the application closes.
2. **Given** a failed save, **When** the user applies another change to the same game after the problem is fixed, **Then** the next save writes the full current state of the game.
3. **Given** a failed save, **When** the application is reopened, **Then** any previously saved games are intact and readable, and no partial or temporary files are left behind.

---

### Edge Cases

- A game entered with an empty name or an empty command is rejected by the existing form and nothing is saved.
- A name or command with accents, non-Latin scripts, quotes, or very long text is saved and restored exactly as typed.
- A game file that is damaged, unreadable, or from an unknown newer format is skipped on startup without preventing the other games from loading, and without being overwritten.
- A game file edited by hand while the application is closed (for example to fix a command) is read as edited on the next start.
- A manually added game placed in a collection and then restarted keeps its collection membership; membership is not dropped because the game was only added during the session.
- Cover chosen but the application is closed before the user applies: no game and no cover are saved.
- A game added in one session and the data folder deleted before the next: the game is gone, and the library loads normally without errors.
- Upgrading from a version where a manually added game was never written to disk: games added before the upgrade that were not saved cannot be recovered; games already on disk keep working.
- "Remove All Games" in Danger Zone also removes manually added games and their saved data, as already specified in feature 002.
- Adding a game while an import is running: the game is saved, and the import neither removes nor changes it.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The user MUST be able to add a game by hand by providing a name and a command, and optionally a developer and a cover; the game MUST appear in the library as soon as the user applies.
- **FR-002**: When the user applies a new manually added game, the system MUST save the game's name, command, developer, date added, and identity, so that it is available after the application is closed and reopened.
- **FR-003**: When the user applies edits to a manually added game (name, command, developer, or cover), the system MUST save the changes at that moment; cancelling an edit MUST NOT change what is saved.
- **FR-004**: Saving MUST happen when the user applies, not only when the application closes, so that a crash, forced quit, or "Exit After Launching Games" cannot lose the game.
- **FR-005**: On every start, the system MUST load all saved manually added games and show them, regardless of the "Import Games on Startup" setting, and without depending on any launcher or on an import having run.
- **FR-006**: A restored manually added game MUST behave identically to the one the user added: it launches with its saved command, shows its saved cover, and is sorted, searched, hidden, and collected like any other game.
- **FR-007**: Whether a manually added game is hidden, removed, and its last-played time MUST persist across restarts, and its membership in collections MUST be preserved even if the game was added in the same session.
- **FR-008**: Each manually added game MUST have an identity that is unique among all manually added games, including ones that were removed, so that adding a game can never overwrite, merge with, or revive another game; this MUST hold when several games are added in one session without a restart.
- **FR-009**: Imports (startup import, "Import Now") MUST NOT remove, duplicate, or change manually added games.
- **FR-010**: Removing a manually added game MUST be permanent across restarts, and undoing the removal MUST restore it, also across restarts (as defined in feature 008).
- **FR-011**: If a game cannot be saved when the user applies an add or an edit, the game MUST still work for the current session, the application MUST show one dismissable in-app notice that explains it was not saved, a warning with the reason MUST be written to the application log, and no error dialog or crash may occur.
- **FR-012**: A failed save MUST leave all previously saved games unchanged and readable and MUST NOT leave temporary or partially written files; the next successful save of that game MUST write its complete current state.
- **FR-013**: A saved game that is unreadable, damaged, or from a newer unsupported format MUST be skipped without preventing other games from loading, and MUST NOT be deleted or overwritten by the application.
- **FR-014**: Saved manually added games MUST remain readable and writable by the user outside the application, so a user can back them up or edit them by hand while the application is closed.
- **FR-015**: The notice text of FR-011 MUST be translatable and use a placeholder for the game name so translators can order the sentence naturally.

### Key Entities

- **Manually Added Game**: A game the user created by hand. Attributes: unique identity, name, launch command, developer (optional), cover (optional), date added, and the states shared with all games (hidden, removed, last played). It belongs to the "Added" source, not to any launcher.
- **Saved Game Record**: The durable copy of one manually added game, kept in the application's data folder, one per game, readable and editable outside the application.
- **Cover**: The artwork of a game, stored separately from its record and linked to it by the game's identity.
- **Collection Membership**: The list of games a collection holds; it refers to games by identity and must keep manually added games across restarts.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In 100% of tests, a manually added game is present after closing and reopening the application, with every entered value (name, command, developer, cover) unchanged.
- **SC-002**: In 100% of tests, edits applied to a manually added game are shown after a restart, and cancelled edits are never shown.
- **SC-003**: When 10 games are added in one session without a restart, 100% of them are present after the restart, each with its own values.
- **SC-004**: A manually added game remains after a forced quit of the application within 1 second of the user applying it.
- **SC-005**: With "Import Games on Startup" off, 100% of manually added games are shown on start.
- **SC-006**: When the data folder is full, read-only, or access-denied, 100% of attempts to add a game keep the game working for the session, show the notice within 1 second, and leave no temporary files and no damage to already saved games.
- **SC-007**: A user can add a game and see it in the library in under 1 minute, without leaving the Add Game form for any other step.

## Assumptions

- "Manual game add" refers to the existing Add Game flow (the Added source). This feature does not redesign the form, add new fields, or change the existing rules for which fields are required.
- "Like game imports" means the same expectations the user has of imported games: present after a restart, edits kept, and not affected by later imports. It does not mean manually added games are re-scanned from a launcher.
- Manually added games are saved one record per game in the data folder, in the same readable format already used for them, so existing saved games keep working and need no migration.
- Games added before this feature, but never saved, cannot be recovered; this is accepted.
- A failed save is reported with a notice in the app because the user just typed the data themselves. This differs from background history such as play times, which are reported only in the log (feature 005).
- A failed save caused by hiding, removing, or undoing a removal is reported only in the application log, as in feature 008; the in-app notice is for adding and editing, where the user has just typed data that would be lost.
- Hidden state, removal, and last-played time of these games already persist through their own mechanisms (features 005 and 008); this feature relies on them and only verifies the combined behavior.
- Cover storage and the "Remove All Games" action already exist (features 002 and 008); this feature does not change them.
- Syncing manually added games between computers is out of scope.
