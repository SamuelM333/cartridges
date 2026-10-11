# Feature Specification: Collections

**Feature Branch**: `feat/011-collections`

**Created**: 2026-10-11

**Status**: Draft

**Input**: User description: "new feat: Collections. Capture the current implementation in a spec. New Settings toggle: \"Hidden games show in Collections\" tooltip: \"Useful for hiding launchers and tools\""

## Overview

Collections let a player group games from any source under a name and an icon, and browse each group from the sidebar. This specification does two things:

1. It records how Collections work today, so later changes can be checked against it (user stories 1 to 3, marked **Implemented**).
2. It adds one new preference, **Hidden games show in Collections**, so a player can hide a game from the main library and still find it in a collection (user story 4, marked **New**). The preference's tooltip is "Useful for hiding launchers and tools", because launchers and tools are the games players most often want out of the way yet within reach.

### Current Behavior (baseline)

- **Where collections appear**: The sidebar has a "Collections" section below "Sources". It lists the collections in alphabetical order by name, ignoring case. Each entry shows its icon and name, and its name appears as a tooltip. Below the list is a "New Collection" entry that opens the creation dialog instead of showing a view.
- **Creating**: A collection is created from the "New Collection" sidebar entry, with the keyboard shortcut for adding a collection (Ctrl+Shift+N, listed in the shortcuts dialog), or from the "New Collection" entry in a game's options menu or its details page. The last way puts that game in the new collection straight away.
- **The collection dialog**: It has a "Name" field, a grid of 21 icons (7 columns by 3 rows), a Cancel button, and an Apply button. A new collection starts with the default "collection" icon and the dialog is titled "New Collection"; an existing collection's dialog is titled with its name. Apply stays disabled until the name is not empty (a name made only of spaces counts as not empty), and pressing Enter in the name field applies. Cancel discards the changes. The name field has the focus when the dialog opens.
- **Editing and removing**: "Edit" and "Remove" are in the sidebar entry's context menu. The edit dialog also has a destructive "Remove" button, and the Delete key removes the collection from inside the dialog. Renaming a collection moves it to its new alphabetical place in the sidebar.
- **Removing**: A removed collection leaves the sidebar immediately and a toast "{name} removed" offers Undo. If the removed collection was open, the view returns to "All Games"; if its dialog was open, the dialog closes. After Undo the collection is back, with its games. Once the app restarts, a removed collection is gone for good.
- **Adding games**: A game's options menu (the three-dots button on its card) and its details page each have a "Collections" section with one toggle button per collection (icon and name). Toggling buttons does not change anything until the menu is closed; closing it adds the game to the collections that are on and takes it out of the ones that are off. The section is hidden while there are no collections.
- **Browsing**: Selecting a collection shows the games in it, from all sources together. Search, sorting, the cover grid, and hover controls work as in "All Games". "Show Hidden Games" (Ctrl+H) switches the view to list only the games the user hid; with it off, hidden games are not listed. An empty collection shows a status page with the collection's icon and "No Games in {name}"; a search with no matches shows "No Games Found".
- **Membership**: A collection refers to games by identity, so a game keeps its places when it is renamed or its details change. A launcher game that is not installed at the moment keeps its places and returns to them when it is back. A manually added game that no longer exists is dropped from the collection when the app starts.
- **Persistence**: Collections (name, icon, games, and whether removed) are saved with the app's preferences after each change and survive restarts. A stored collection that cannot be read is skipped and a warning is written to the log; the others still load.
- **Gamepad**: The back button of a connected gamepad closes the collection dialog.
- **No limits**: There is no maximum number of collections or of games in one, and two collections may have the same name.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create and manage collections (Priority: P1) **Implemented**

A player with a large library wants named groups such as "Co-op" or "Finished". They create a collection with a name and an icon, change either later, and remove it if they no longer want it.

**Why this priority**: Without collections existing, nothing else in this feature has any value.

**Independent Test**: Create a collection from the sidebar, rename it and change its icon, then remove it and undo the removal; check the sidebar after each step.

**Acceptance Scenarios**:

1. **Given** the sidebar, **When** the user chooses "New Collection", types a name, picks an icon, and applies, **Then** a collection with that name and icon appears in the sidebar in alphabetical order, and the sidebar selection stays where it was.
2. **Given** the creation dialog with an empty name, **When** the user looks at Apply, **Then** it is disabled until a name is typed.
3. **Given** an existing collection, **When** the user edits its name, **Then** the sidebar shows the new name in its new alphabetical place; **When** they change its icon, **Then** the sidebar and any open view show the new icon.
4. **Given** an existing collection, **When** the user removes it from the context menu or the dialog, **Then** it leaves the sidebar, a toast offers Undo, and Undo brings it back with its games.
5. **Given** the removed collection was the open view, **When** it is removed, **Then** the view returns to "All Games".
6. **Given** the creation dialog is open, **When** the user presses Cancel, **Then** no collection is created and nothing changes.

---

### User Story 2 - Put games in collections and browse them (Priority: P1) **Implemented**

A player wants to find a group of games quickly. They add games to collections from a game's menu or details page and open a collection to see only its games.

**Why this priority**: This is what collections are for; creating empty collections alone does not help the player find anything.

**Independent Test**: Add two games to a collection from their options menus, open the collection, search and sort inside it, then open an empty collection.

**Acceptance Scenarios**:

1. **Given** a game and at least one collection, **When** the user opens the game's options menu, turns a collection on, and closes the menu, **Then** the game appears in that collection; **When** they turn it off again, **Then** it leaves the collection.
2. **Given** no collections, **When** the user opens a game's options menu, **Then** the "Collections" section is not shown, and "New Collection" is.
3. **Given** a game's options menu, **When** the user chooses "New Collection", names it, and applies, **Then** the new collection contains that game.
4. **Given** a collection with games from several sources, **When** the user selects it, **Then** all of those games are listed, and search and sort apply only to them.
5. **Given** an empty collection, **When** the user selects it, **Then** a status page shows its icon and "No Games in {name}".
6. **Given** a collection that contains hidden games and "Show Hidden Games" is off, **When** the user selects it, **Then** the hidden games are not listed; **When** "Show Hidden Games" is on, **Then** only the hidden games of the collection are listed.

---

### User Story 3 - Collections last and stay correct (Priority: P2) **Implemented**

A player expects their groups to still be there tomorrow and not to break when games come and go.

**Why this priority**: Losing groups would make the feature untrustworthy, but it only matters once the first two stories work.

**Independent Test**: Create collections with games, restart the app, and compare. Then uninstall a launcher game and restore it.

**Acceptance Scenarios**:

1. **Given** collections with games, **When** the app is restarted, **Then** every collection, its icon, and its games are as they were.
2. **Given** a launcher game in a collection that is uninstalled, **When** it is installed again, **Then** it is back in the collection.
3. **Given** a stored collection that is damaged, **When** the app starts, **Then** the other collections load normally and a warning is written to the log.
4. **Given** a removed collection and no Undo, **When** the app restarts, **Then** it does not come back.

---

### User Story 4 - Keep hidden games reachable through collections (Priority: P2) **New**

A player hides launchers and tools such as Steam, Lutris, or a Windows compatibility tool so they do not crowd the library. They still want to open them in one click, so they put them in a collection called "Launchers". They turn on **Hidden games show in Collections** in Preferences so that collection lists the games they hid, while "All Games" stays tidy.

**Why this priority**: It is the only change in this specification, and the baseline works without it, so it ranks after the core stories while being the work to be done.

**Independent Test**: Hide a game and put it in a collection. With the preference off, the collection does not list it. Turn the preference on, and the collection lists it while "All Games" still does not.

**Acceptance Scenarios**:

1. **Given** Preferences, **When** the user opens the General page, **Then** there is a switch "Hidden games show in Collections", off by default, with the tooltip "Useful for hiding launchers and tools".
2. **Given** a hidden game in a collection and the preference off, **When** the user opens the collection, **Then** the game is not listed (same as today).
3. **Given** a hidden game in a collection, **When** the user turns the preference on, **Then** the open collection immediately lists the game, without a restart.
4. **Given** the preference on, **When** the user opens "All Games" or a source with "Show Hidden Games" off, **Then** hidden games are still not listed there.
5. **Given** the preference on and a collection open, **When** the user turns "Show Hidden Games" on, **Then** only the hidden games of the collection are listed, as they are with the preference off.
6. **Given** the preference on, **When** the user searches inside a collection, **Then** hidden games in it are matched like any other game.
7. **Given** the preference on and a hidden game listed in a collection, **When** the user opens its options menu, **Then** it offers "Unhide" (not "Hide"), and unhiding it keeps it in the collection.
8. **Given** the preference on and a visible game in a collection, **When** the user hides it, **Then** a toast confirms with Undo and the game stays listed in the collection.
9. **Given** the preference on, **When** the app is restarted, **Then** it is still on.

---

### Edge Cases

- **A collection holds only hidden games** and the preference is off: the collection shows "No Games in {name}", the same as an empty collection.
- **Both "Show Hidden Games" and the new preference are on**: the collection lists only its hidden games, as it does with the preference off. The preference adds nothing in that view, and games that are not hidden stay out of it.
- **A game in several collections**: it is listed in each of them, and hiding it affects them all in the same way.
- **The preference is switched off while a hidden game is shown in an open collection**: the game leaves the view immediately.
- **A manually added game** that is hidden and in a collection behaves the same as any other hidden game with the preference on.
- **A very long collection name**: its full name is always available as a tooltip in the sidebar.
- **Reset App**: it returns the preference to off together with the other preferences.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The sidebar MUST list collections alphabetically by name, ignoring case, each with its icon, and MUST show the full name as a tooltip.
- **FR-002**: Users MUST be able to create a collection from the sidebar, from the add-collection shortcut, and from a game's options menu and details page; creating one from a game MUST put that game in it.
- **FR-003**: The collection dialog MUST offer a name field, a choice of the 21 icons, Cancel, and Apply; Apply MUST be disabled while the name is empty; a new collection MUST default to the "collection" icon.
- **FR-004**: Users MUST be able to edit a collection's name and icon, and renaming MUST update its place in the sidebar.
- **FR-005**: Users MUST be able to remove a collection from its sidebar context menu and from its dialog (button or Delete key); a toast MUST offer Undo, and removing the open collection MUST return the view to "All Games" and close its dialog.
- **FR-006**: A game's options menu and details page MUST list every collection as a toggle in a "Collections" section, MUST apply the choices when the menu closes, and MUST hide the section while no collections exist.
- **FR-007**: Selecting a collection MUST list the games it holds from all sources, with search, sorting, and the cover grid working as in "All Games".
- **FR-008**: An empty collection MUST show a status page with its icon and "No Games in {name}", and a search with no match MUST show "No Games Found".
- **FR-009**: A collection MUST refer to games by identity; a game that is temporarily absent MUST keep its places, and a manually added game that no longer exists MUST be dropped when the app starts.
- **FR-010**: Collections (name, icon, games, removed state) MUST be saved after each change and MUST survive restarts; a removed collection MUST stay removed after a restart unless the removal was undone first.
- **FR-011**: A stored collection that cannot be read MUST be skipped with a warning in the debug log, and the remaining collections MUST load.
- **FR-012**: Preferences MUST offer a switch "Hidden games show in Collections" on the General page with the tooltip "Useful for hiding launchers and tools".
- **FR-013**: The switch MUST be off by default, MUST be remembered across restarts, MUST take effect immediately without a restart, and MUST be reset by "Reset App".
- **FR-014**: With the switch on and "Show Hidden Games" off, a collection view MUST list the hidden games it holds together with its other games. With "Show Hidden Games" on, a collection view MUST list only its hidden games, whatever the switch says. With the switch off, a collection view MUST behave as before.
- **FR-015**: The switch MUST NOT change what "All Games" and the source views list, nor which games are hidden.
- **FR-016**: With the switch on, searching, sorting, the hide and unhide actions, and the Undo toasts MUST work for hidden games in a collection as they do for other games, and hiding a game MUST NOT remove it from its collections.

### Key Entities

- **Collection**: A named, iconed group of games. Attributes: name (not empty), icon (one of 21 choices), the set of game identities it holds, and whether it was removed. It never copies games; it only refers to them.
- **Hidden game**: A game the user hid; its state is kept across restarts. It is left out of the main views, listed alone when "Show Hidden Games" is on, and, with the new switch on, listed together with the other games in the collections that hold it.
- **Hidden games show in Collections preference**: A single on/off preference, off by default, stored with the app's other preferences and kept per build.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can create a collection with a name and icon in under 30 seconds and add a first game to it in under 15 more seconds.
- **SC-002**: After any change to collections, 100% of collections, icons, and memberships are the same after a restart.
- **SC-003**: With the new preference on, 100% of hidden games that belong to a collection are listed when that collection is opened, and 0 hidden games appear in "All Games" or a source view because of it.
- **SC-004**: With the new preference off, collection views list exactly the games they list today, in every case.
- **SC-005**: Turning the preference on or off changes the open collection view in under 1 second, with no restart.
- **SC-006**: A user who hides a launcher and puts it in a collection can open that launcher from the collection in at most 3 actions (open collection, hover, play).

## Assumptions

- The preference is off by default, so that nothing changes for existing users until they choose it.
- The preference lives on the General page of Preferences, in the Behavior group, next to the other behavior switches. Its label and tooltip are exactly the texts given above. Other switches use a subtitle, but this one uses the tooltip as requested.
- A hidden game listed in a collection looks like any other game; no extra marker is added. A marker could be a later improvement.
- "Show Hidden Games" keeps its present meaning in every view: it lists only the hidden games. The new preference only adds hidden games to a collection view that is not in that mode.
- The 21 icons, the dialog layout, and the alphabetical order stay as they are; changing them is out of scope.
- Collections stay a per-build preference with no import, export, or sharing between devices.
- Nothing is added to the debug log for the new preference beyond the existing logging rules.
