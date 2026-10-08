# Feature Specification: Game Import

**Feature Branch**: `008-game-import`

**Created**: 2026-10-08

**Status**: Draft

**Input**: User description: "Game import. Document the existing game import behavior as a spec, and add a new requirement: an "Import Now" action in Preferences (upstream Cartridges main had "Import" under the + button menu in the main window). Place it on the Import page, at the top, above the Behavior group."

## Overview

Cartridges builds its library by scanning the game launchers installed on the user's system ("sources") and combining what it finds with games the user added manually. This specification records how import works today, lists the known gaps between the Import preferences and actual behavior, and adds one new capability: an on-demand **Import Now** action in Preferences.

### Current Behavior (baseline)

- **Sources**: Steam, Lutris, Heroic, itch, Legendary, Flatpak, Desktop Entries, and "Added" (games the user created manually). Each source is discovered automatically and appears in the sidebar.
- **When import happens**: Every source is scanned exactly once, when the application starts. There is no way to re-scan without restarting the application.
- **Persistence**: Launcher games are not stored by Cartridges; they are read fresh from each launcher on every scan. Only manually added games are stored by Cartridges.
- **Last played**: For each scanned game, the last-played time is the more recent of the launcher-reported time and the time Cartridges recorded when it launched the game.
- **Date added**: If a launcher does not report when a game was added, the game is stamped with the time of the scan.
- **Failure handling**: If a source cannot be read (missing launcher, unreadable files), that source contributes zero games and the rest of the library still loads.
- **Import preferences**: The Import page contains a **Behavior** group ("Import Games Automatically", default off; "Remove Uninstalled Games", default on) and a **Sources** group with a per-source enable switch, install location, and sub-options (Lutris: Steam / Flatpak games; Heroic: Epic / GOG / Amazon / Sideloaded; Flatpak: system and user location, game launchers).

### Known Gaps (baseline)

- **G-1**: "Import Games Automatically" is saved but has no effect; the startup scan always runs. (Resolved by FR-017 and FR-018.)
- **G-2**: "Remove Uninstalled Games" is saved but has no effect. (Resolved by FR-016: the switch is removed.)
- **G-3**: Only the Flatpak source honors its enable switch, locations, and sub-options. Steam, Lutris, Heroic, itch, Legendary, and Desktop Entries ignore their switches, install locations, and sub-options.

## Clarifications

### Session 2026-10-08

- Q: What should happen to uninstalled games when "Remove Uninstalled Games" is off? -> A: Remove the "Remove Uninstalled Games" switch. Uninstalled games always disappear on the next import, which is what happens today.
- Q: What should "Import Games Automatically" do? -> A: It controls the startup scan. When off, launcher games are not scanned at startup and appear only after Import Now. Rename it to "Import Games on Startup".

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Import games on demand from Preferences (Priority: P1)

A user installs a new game in Steam (or another launcher) while Cartridges is open. Instead of restarting Cartridges, they open Preferences, go to the Import page, and press **Import Now** at the top of the page. Cartridges re-scans the sources and the new game appears in the library.

**Why this priority**: This is the new requirement. Today the only way to pick up newly installed or uninstalled games is to restart the application. Upstream Cartridges offered this from the "+" menu in the main window; this fork moves it into Preferences next to the settings that control import.

**Independent Test**: With Cartridges running, install (or simulate by adding a launcher manifest for) a game in any enabled source. Open Preferences > Import, press Import Now, and verify the game appears in the library without restarting.

**Acceptance Scenarios**:

1. **Given** the Preferences dialog is open on the Import page, **When** the user looks at the page, **Then** an "Import Now" control is the first item on the page, above the Behavior group.
2. **Given** a game was installed in a launcher after Cartridges started, **When** the user presses Import Now, **Then** the game appears in the library and under its source in the sidebar without restarting the application.
3. **Given** an import is running, **When** the user looks at the Import Now control, **Then** it shows that an import is in progress and cannot be started a second time until the current one finishes.
4. **Given** an import finishes, **When** the result is shown, **Then** the user sees a brief, non-blocking notification stating how many new games were found (or that no new games were found).
5. **Given** the user changed a source's install location or sub-option, **When** they press Import Now, **Then** the scan uses the updated settings (for every source that honors its settings, see User Story 3).
6. **Given** the main window "+" button, **When** the user opens it, **Then** it still adds a game manually; import is not offered there.

---

### User Story 2 - Library is populated at startup (Priority: P1, existing)

When the user opens Cartridges with "Import Games on Startup" on, every source is scanned and the library shows all installed games from all launchers plus manually added games. With it off, only manually added games are shown until the user runs Import Now.

**Why this priority**: This is the core existing behavior that the library depends on; it must not regress.

**Independent Test**: Install games in two or more launchers, start Cartridges, and verify all of them appear, each under its own source in the sidebar.

**Acceptance Scenarios**:

1. **Given** games installed in several launchers and "Import Games on Startup" on, **When** Cartridges starts, **Then** every game appears in the library and under its source.
2. **Given** a launcher that is not installed or whose files cannot be read, **When** Cartridges starts, **Then** that source shows no games and every other source loads normally.
3. **Given** a game that Cartridges launched more recently than the launcher reports, **When** the library loads, **Then** the more recent time is shown as last played.
4. **Given** a launcher that does not report when a game was added, **When** the library loads, **Then** the game's date added is the time of the scan.
5. **Given** "Import Games on Startup" is off, **When** Cartridges starts, **Then** no launcher is scanned, only manually added games are shown, and launcher games appear after the user presses Import Now.

---

### User Story 3 - Import preferences control what is imported (Priority: P2)

A user disables a source they do not use, points a source at a non-default install location, or turns off a sub-option (for example, Heroic's Amazon games). The next import respects those choices.

**Why this priority**: The settings are already visible to the user; today most of them do nothing (G-1 to G-3), which is misleading. Import Now makes the mismatch more noticeable, since users will change a setting and immediately re-import.

**Independent Test**: Disable a source, press Import Now, and verify its games are no longer listed; re-enable it, press Import Now, and verify they return.

**Acceptance Scenarios**:

1. **Given** a source's enable switch is off, **When** an import runs, **Then** no games from that source appear.
2. **Given** a source's install location was changed, **When** an import runs, **Then** games are read from the new location.
3. **Given** a sub-option is off (e.g., Heroic "Import Amazon Games"), **When** an import runs, **Then** games in that category are not imported.
4. **Given** a game was uninstalled from its launcher, **When** an import runs, **Then** the game no longer appears in the library.
5. **Given** the Import page, **When** the user looks at the Behavior group, **Then** it contains "Import Games on Startup" and no "Remove Uninstalled Games" switch.

---

### Edge Cases

- **Import while a game is running or being edited**: Re-scanning must not interrupt a running game, close an open game details view, or discard unsaved edits.
- **User state across re-import**: A game the user hid, removed, or edited keeps that state after Import Now, to the same extent it is kept today across a restart.
- **Manually added games**: Import Now never removes or duplicates manually added games.
- **Duplicate games**: A game already in the library is updated in place on re-import, not added a second time.
- **One source fails**: If one source cannot be read during Import Now, the others still import and the notification still reports the result.
- **Preferences closed during import**: Closing Preferences while an import is running does not cancel or corrupt the import; the library updates when it finishes.
- **Startup import off, first launch**: The library shows only manually added games (or the empty state if there are none) until the user runs Import Now. Nothing is scanned in the background.
- **Previously saved "Remove Uninstalled Games" value**: Ignored after the switch is removed; it has no effect and does not cause an error.
- **No sources enabled**: Import Now completes immediately and reports that no new games were found.
- **Cover art**: Games newly found by Import Now get covers by the same rules as games found at startup, including SteamGridDB if it is enabled.

## Requirements *(mandatory)*

### Functional Requirements

**Existing behavior (must not regress)**

- **FR-001**: When "Import Games on Startup" is on, the system MUST scan every available source when the application starts and show the combined results in the library and in the per-source sidebar. Manually added games MUST always load at startup, whatever this setting is.
- **FR-002**: The system MUST read launcher games from the launchers on each scan rather than from its own stored copy; only manually added games are stored by Cartridges.
- **FR-003**: The system MUST set a game's last-played time to the more recent of the launcher-reported time and the time Cartridges last launched it.
- **FR-004**: The system MUST set a game's date added to the scan time when the launcher does not provide one.
- **FR-005**: A source that cannot be read MUST contribute zero games without preventing other sources from loading.

**New: Import Now**

- **FR-006**: The Import page of Preferences MUST show an "Import Now" control as its first item, above the Behavior group.
- **FR-007**: Activating Import Now MUST re-scan all sources and update the library, sidebar source lists, and counts without restarting the application.
- **FR-008**: While an import runs, the control MUST show a progress indicator and MUST NOT allow a second import to start.
- **FR-009**: The application MUST remain responsive (scrolling, launching games, navigating Preferences) while an import runs.
- **FR-010**: When an import finishes, the system MUST show a non-blocking notification with the number of newly found games, or a message that none were found.
- **FR-011**: Re-importing MUST update existing games in place, MUST NOT duplicate games, and MUST NOT remove or alter manually added games.
- **FR-012**: The "+" button in the main window MUST continue to add a game manually only; import is offered in Preferences, not in that menu.

**Settings honored by import (closes G-1 to G-3)**

- **FR-013**: Every source MUST honor its enable switch: when off, the source contributes no games.
- **FR-014**: Every source with an install location setting MUST read from that location.
- **FR-015**: Every sub-option (Lutris Steam / Flatpak games; Heroic Epic / GOG / Amazon / Sideloaded; Flatpak launchers and locations) MUST include or exclude the matching games.
- **FR-016**: The "Remove Uninstalled Games" switch MUST be removed from the Import page. Games no longer installed in their launcher MUST disappear from the library on the next import.
- **FR-017**: "Import Games Automatically" MUST be renamed "Import Games on Startup". When off, the system MUST NOT scan any launcher at startup; launcher games appear only after Import Now.
- **FR-018**: "Import Games on Startup" MUST default to on, so that users who never change it keep today's behavior of seeing their launcher games at startup.

### Key Entities

- **Source**: A launcher or origin of games (Steam, Lutris, Heroic, itch, Legendary, Flatpak, Desktop Entries, Added). Has a name, an icon, an enabled state, optional install location(s), and optional sub-options.
- **Game**: An entry in the library. Belongs to exactly one source. Has a title, launch command, cover, date added, last-played time, and user state (hidden, removed).
- **Import run**: One scan of all sources, either at startup or from Import Now. Produces the current set of games per source and a count of newly found games.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can make a newly installed game appear in the library in under 15 seconds from opening Preferences, without restarting the application.
- **SC-002**: Import Now on a library of 500 games across all sources completes in under 10 seconds on typical hardware, and the interface never freezes for more than a quarter of a second during it.
- **SC-003**: Re-running Import Now 10 times in a row with no launcher changes produces zero duplicate games and leaves the library unchanged.
- **SC-004**: For every switch, location, and sub-option on the Import page, changing it and pressing Import Now produces the corresponding visible change in the library (100% of Import settings have an observable effect).
- **SC-005**: Zero regressions in startup import: with "Import Games on Startup" at its default, all games that appeared before this feature still appear afterward with the same last-played and date-added values.
- **SC-006**: With "Import Games on Startup" off, starting the application reads no launcher data.

## Assumptions

- The user's note "Under Import, on top of behavior" means the Import Now control sits on the Import preferences page above the Behavior group.
- Import Now re-scans all sources together; per-source import buttons are out of scope.
- The control follows the existing Preferences pattern for long-running actions (the SteamGridDB "Update Covers" row): an action row with a button that switches to a spinner while working, with results reported as a toast.
- Closing the gaps G-1 to G-3 is in scope because Import Now makes it immediately visible when a setting has no effect. If the user prefers, User Story 3 can be split into a separate feature.
- Persistence of hidden/removed/edited state for launcher games is unchanged by this feature; Import Now keeps such state exactly as well as a restart does today.
- "Import Games on Startup" defaults to on (the old "Import Games Automatically" setting defaulted to off). A default of off would hide every launcher game on first launch, which would be a regression. Any value saved under the old setting is not carried over, because the old switch never had any effect.
- Upstream Cartridges' "Import" entry under the main window "+" menu is not restored; the "+" button stays a direct "Add Game" action.
