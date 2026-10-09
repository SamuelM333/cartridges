# Feature Specification: Desktop Entries

**Feature Branch**: `009-desktop-entries`

**Created**: 2026-10-09

**Status**: Implemented

**Input**: User description: "new spec: desktop entries. create spec with current implementation in code. bug fix: desktop entries load broken icons. expected behaviour is to load the default desktop icon"

## Overview

On Linux, Cartridges can import games from the desktop entries (application launchers) installed on the user's system. This is the "Desktop Entries" source. This specification records how the source works today and fixes one bug: some desktop entry games are shown with a broken-image icon instead of a usable icon. When a desktop entry's own icon cannot be shown, the game must show the default application icon instead.

### Current Behavior (baseline)

- **Availability**: The source exists only on Linux. On other platforms its switch is hidden in Preferences > Import. It can be turned on or off with the "Desktop Entries" switch; when off, it contributes no games.
- **Where entries are found**: The user's Desktop folder, then the `applications` folder of the user's data directory, then the `applications` folder of each system data directory. Inside Flatpak, the host's system data directories and the Flatpak export directories (system and user) are searched instead of the sandbox's own.
- **Duplicates**: When the same file name exists in more than one location, only the first one found is used, in the order above.
- **What counts as a game**: An entry is imported only if its categories include "Game".
- **What is skipped**:
  - Entries marked as hidden or not to be displayed.
  - Entries that belong to another source or to Cartridges itself (Cartridges' own entries and Lutris entries, matched by file name).
  - Entries that launch through Steam, Heroic, or the Bottles command line, since those games are imported by their own sources.
  - Entries exported by Flatpak, since Flatpak apps are imported by the Flatpak source.
  - Entries whose "try executable" program is declared but not installed.
  - Entries that cannot be read or are missing a required field (name or launch command).
- **What is imported for each game**: The entry's name as the title; a launch command that opens the entry through the system's standard launcher (so the entry's own launch rules apply); and an identifier derived from the entry's file name, so the same entry is recognized as the same game across imports.
- **Cover**: Desktop entries have no cover art. The entry's icon is centered on a blank cover-sized canvas and used as the cover. When the entry has no icon field, the default application icon is used. Icons are looked up in the icon themes of the user and system data directories.
- **Saved library**: The cover produced at import time is saved with the library (see `specs/008-game-import`). On later imports, a game already in the library keeps its saved cover; a scanned cover is only used if the game had none.

### Known Gaps (baseline)

- **G-1**: When an entry names an icon that cannot be found or cannot be displayed, the game's cover shows a broken-image icon. The fallback to the default application icon only applies when the icon field is missing entirely, and does not reliably produce a visible icon. (Resolved by FR-012 to FR-015.)
- **G-2**: Because existing games keep their saved cover on later imports, games already imported with a broken icon stay broken even after G-1 is fixed. (Resolved by FR-016.)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Desktop entry games show a usable icon (Priority: P1)

A user has a game installed through a desktop entry whose icon is missing (for example, an icon name that is not installed in any icon theme, or a path to an image file that was deleted). They open Cartridges. Instead of a broken-image icon, the game's cover shows the default application icon, so the library looks intentional and the game is still recognizable by its title.

**Why this priority**: This is the bug fix. A broken-image icon looks like an application error and degrades the whole library grid.

**Independent Test**: Create a desktop entry in the user's applications folder with `Categories=Game;` and `Icon=` set to a name that does not exist. Import, and verify the game's cover shows the default application icon, not a broken-image icon.

**Acceptance Scenarios**:

1. **Given** a game desktop entry whose icon name is not found in any icon theme, **When** the library is imported, **Then** the game's cover shows the default application icon.
2. **Given** a game desktop entry whose icon is a path to a file that does not exist, **When** the library is imported, **Then** the game's cover shows the default application icon.
3. **Given** a game desktop entry whose icon is a file that exists but is not a readable image, **When** the library is imported, **Then** the game's cover shows the default application icon.
4. **Given** a game desktop entry with no icon field, **When** the library is imported, **Then** the game's cover shows the default application icon.
5. **Given** a game desktop entry whose icon is found and valid (by theme name or by file path), **When** the library is imported, **Then** the game's cover shows that icon, not the default.
6. **Given** any of the above, **When** the user restarts Cartridges with "Import Games on Startup" off, **Then** the cover saved with the library is the same as the one shown before the restart.

---

### User Story 2 - Previously broken icons are repaired on the next import (Priority: P1)

A user already imported desktop entry games before this fix, and some of them were saved with a broken-image icon. After updating Cartridges, they run an import (at startup or with Import Now). The broken icons are replaced with the default application icon (or the entry's real icon, if it is now available).

**Why this priority**: Without this, the fix is invisible to every existing user, because saved covers are kept across imports.

**Independent Test**: Import a desktop entry game with a missing icon using the current version, so its broken cover is saved. Update to the fixed version and run Import Now. Verify the cover now shows the default application icon.

**Acceptance Scenarios**:

1. **Given** a desktop entry game saved in the library with a cover produced from its icon, **When** the library is imported again, **Then** the cover is replaced by the cover produced by the new scan.
2. **Given** the user has chosen a custom cover for a desktop entry game, **When** the library is imported again, **Then** the custom cover is kept.

---

### User Story 3 - Games from desktop entries appear in the library (Priority: P2)

A user installs a game that adds a desktop entry with the "Game" category (for example, a native Linux game or a game set up with a custom launcher). With the Desktop Entries source on, the game appears in the library under "Desktop" and launches through its entry.

**Why this priority**: This is the baseline behavior being documented. It already works and must keep working.

**Independent Test**: Add a game desktop entry to the user's applications folder, run Import Now, and verify the game appears with the entry's name and launches when played.

**Acceptance Scenarios**:

1. **Given** a desktop entry with the "Game" category in any searched location, **When** the library is imported, **Then** the game appears under the Desktop source with the entry's name.
2. **Given** an imported desktop entry game, **When** the user plays it, **Then** the entry is launched the same way the system's application launcher would launch it.
3. **Given** a desktop entry without the "Game" category, **When** the library is imported, **Then** it does not appear.
4. **Given** a desktop entry that is hidden, belongs to Steam, Heroic, Bottles, Lutris, Flatpak, or Cartridges, or whose declared "try executable" program is not installed, **When** the library is imported, **Then** it does not appear.
5. **Given** two entries with the same file name in the user's and the system's applications folders, **When** the library is imported, **Then** only the user's entry appears.
6. **Given** the Desktop Entries switch is off, **When** the library is imported, **Then** no desktop entry games are imported.
7. **Given** a desktop entry that cannot be read, **When** the library is imported, **Then** it is skipped and every other entry still imports.

---

### Edge Cases

- **Icon name with a file extension** (e.g. `Icon=mygame.png`): treated like any other name; if not found, the default application icon is used.
- **Icon is a scalable or very large image**: shown at the normal icon size, centered on the cover.
- **Default application icon itself is not available in the user's icon theme**: Cartridges still shows a usable generic application icon (bundled with Cartridges if needed), never a broken-image icon.
- **Inside Flatpak**: icons referenced by entries on the host (by name or by host path) are found the same way as outside Flatpak; if they cannot be reached from the sandbox, the default application icon is used.
- **Entry icon becomes available later** (the user installs the missing icon): on the next import, the game shows the real icon.
- **Entry icon becomes unavailable later** (the icon was uninstalled): on the next import, the game falls back to the default application icon instead of keeping or producing a broken icon.

## Requirements *(mandatory)*

### Functional Requirements

**Baseline (current behavior, must be preserved)**

- **FR-001**: The Desktop Entries source MUST be available only on Linux, and its Preferences switch MUST be hidden on other platforms.
- **FR-002**: When the Desktop Entries switch is off, the source MUST contribute no games.
- **FR-003**: The source MUST search, in order: the user's Desktop folder, the user data `applications` folder, and each system data `applications` folder (inside Flatpak: the host's system data folders and the Flatpak export folders).
- **FR-004**: When the same entry file name exists in more than one searched location, only the first found MUST be imported.
- **FR-005**: Only entries whose categories include "Game" MUST be imported.
- **FR-006**: Entries marked hidden or not-to-be-displayed MUST be skipped.
- **FR-007**: Entries belonging to Cartridges, Lutris (by file name), Steam, Heroic, Bottles (by launch command), and Flatpak exports MUST be skipped.
- **FR-008**: Entries whose declared "try executable" program is not installed MUST be skipped.
- **FR-009**: An entry that cannot be read or is missing its name or launch command MUST be skipped without affecting other entries.
- **FR-010**: Each imported game MUST use the entry's name as its title and MUST be launched by opening the entry through the system's standard application launcher.
- **FR-011**: Each imported game's identifier MUST be derived from the entry's file name, so the same entry is the same game across imports.

**Icon and cover (bug fix)**

- **FR-012**: A desktop entry game's cover MUST show the entry's icon, centered on a cover-sized canvas, when the icon can be found and displayed.
- **FR-013**: The icon MUST be found whether the entry gives it as an icon name (looked up in the installed icon themes and the user and system icon folders) or as a path to an image file.
- **FR-014**: When the entry has no icon, or its icon cannot be found, cannot be read, or is not a valid image, the cover MUST show the default application icon.
- **FR-015**: A desktop entry game's cover MUST never show a broken-image or "missing image" icon. If the default application icon is not available from the user's icon theme, Cartridges MUST use its own copy of a generic application icon.
- **FR-016**: On each import, a desktop entry game whose cover came from its entry's icon MUST have that cover replaced by the cover from the new scan, so previously saved broken icons are repaired. A cover the user chose themselves MUST NOT be replaced.
- **FR-017**: The cover saved with the library MUST match the cover shown at import time, including when the default application icon is used.

### Key Entities

- **Desktop entry**: A launcher file installed on the system. Relevant attributes: file name, location, name, launch command, categories, icon (name or path), hidden flags, "try executable" program.
- **Desktop entry game**: A library game created from a desktop entry. Attributes: title (entry name), launch command (open the entry), identifier (from the file name), cover (entry icon or default application icon, centered on a blank cover).
- **Default application icon**: The generic icon used for applications without a usable icon of their own.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 0 desktop entry games show a broken-image icon after an import, across entries with a missing icon name, a missing icon file, an invalid image file, and no icon field.
- **SC-002**: 100% of desktop entry games whose icon is installed (by name or by path) show that icon after import.
- **SC-003**: 100% of desktop entry games previously saved with a broken icon show a usable icon after one import with the fixed version, with no other user action.
- **SC-004**: 100% of custom covers chosen by the user for desktop entry games remain after an import.
- **SC-005**: The set of desktop entry games imported (which entries are included and skipped) is unchanged from the baseline for the same set of installed entries.

## Assumptions

- "Default desktop icon" means the generic application icon that the desktop shows for applications without their own icon (the freedesktop `application-x-executable` icon or its theme equivalent). If the active icon theme does not provide it, a generic application icon bundled with Cartridges is used.
- Likely causes of the broken icon, to be confirmed during planning: icon lookup returns the toolkit's "missing image" placeholder when neither the named icon nor the fallback is in the searched themes (current icon themes no longer ship a full-color `application-x-executable`); and icons given as absolute file paths are looked up as theme names rather than loaded as files.
- Telling an entry-icon cover apart from a user-chosen cover for FR-016 is a planning decision; the requirement is only that user-chosen covers survive and entry-icon covers are refreshed.
- Only the cover of desktop entry games is changed. Titles, launch commands, filtering rules, and other sources are out of scope.
- Desktop entry translations (localized names) and per-entry launch actions are out of scope; behavior stays as it is today.
