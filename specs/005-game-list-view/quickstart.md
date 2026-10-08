# Quickstart Validation Guide: Main Game List View

**Branch**: `feat/005-game-list-view`
**Feature**: `specs/005-game-list-view`
**Date**: 2026-10-06

## 1. Overview
This guide provides step-by-step instructions for running and validating the main game list view and cover hover interactions.

## 2. Prerequisites & Environment
Ensure compilation and validation run in the `gtk-dev` Distrobox container or with native development dependencies installed:
- Python 3.12+
- GTK 4 and Libadwaita 1.6+
- Blueprint Compiler
- Meson & Ninja

## 3. Build & Run Application

```bash
# Setup build directory
meson setup _build

# Compile UI blueprints and resources
ninja -C _build

# Run application locally
_build/cartridges/cartridges
```

## 4. End-to-End Validation Scenarios

### Scenario 1: Default Hover Controls (Play & Three-Dots)
1. Launch Cartridges with at least one game added.
2. Hover pointer over any game card.
3. **Verify**:
   - Two circular buttons fade in at the top corners of the cover image:
     - Top-left: Circular Play button (`media-playback-start-symbolic`).
     - Top-right: Circular Three-dots menu button (`view-more-symbolic`).
   - The buttons are neatly aligned at `margin: 6px` from top corners.
4. Move pointer outside the game card.
5. **Verify**: Both buttons smoothly fade out.

### Scenario 2: Default Launch and Details Activation
1. With "Cover Image Launches Game" disabled:
2. Hover over a game card and click the top-left Play button.
3. **Verify**: The game launch action triggers.
4. Click anywhere on the cover image directly.
5. **Verify**: The application navigates to the game details page.

### Scenario 3: Toggle "Cover Image Launches Game" Setting
1. Open Main Menu -> Preferences (`Ctrl+,`).
2. Locate the "Cover Image Launches Game" switch under the Behavior group.
3. Toggle the switch to ON.
4. Close Preferences and observe the game grid.
5. **Verify**:
   - Hovering over any game card now reveals an Info ("I") button (`help-about-symbolic`) at the top-left instead of Play.
   - The tooltip displays "Details".

### Scenario 4: Inverted Launch and Details Activation
1. With "Cover Image Launches Game" enabled:
2. Hover over a game card and click the top-left Info button.
3. **Verify**: The application navigates to the game details page.
4. Return to the grid and click the cover image directly.
5. **Verify**: The game launch action triggers directly.

### Scenario 5: Game Launch Toast Notification and Localization
1. In default mode, hover over a game (e.g. "Celeste") and click the Play button.
2. **Verify**:
   - A dismissable toast notification appears at the bottom of the window: "Launched Celeste".
   - The toast automatically fades after standard duration or can be dismissed immediately.
3. Toggle "Cover Image Launches Game" ON in Preferences.
4. Click directly on the cover of "Celeste".
5. **Verify**:
   - The game launches and the dismissable toast "Launched Celeste" appears identically.
6. Open game details for "Celeste" and click the "Play" button.
7. **Verify**:
   - The game launches and the dismissable toast "Launched Celeste" appears.
8. Verify gettext extraction via `ninja -C _build cartridges-pot`:
   - Check `cartridges.pot` contains `msgid "Launched {}"` with translator context comment.

### Scenario 6: Contextual Menu Operations
1. Hover over a game card and click the top-right Three-dots button.
2. Move pointer away from the card while the popover menu is visible.
3. **Verify**: The popover menu stays open and the menu button remains visible.
4. Select "Edit".
5. **Verify**: Navigates to details view in edit mode.
6. Return to grid, open menu again, and select "Hide".
7. **Verify**: Game is hidden from primary grid and an "Undo" toast notification appears.

### Scenario 7: Empty Status Pages
1. Type a random string in the search bar that matches no games.
2. **Verify**: "No Games Found" status page is displayed.
3. Clear search and toggle "Show Hidden Games" with no hidden games.
4. **Verify**: "No Hidden Games" status page is displayed.

### Scenario 8: Launched Game Moves First (Amendment)
Covers User Story 5 scenarios 1-3 and 7, FR-014, FR-016 to FR-018, SC-007, SC-008.
1. Select sort mode "Last Played" from the main menu.
2. Pick two games that are not near the top, e.g. "Zelda" and "Astro". Use harmless executables (for example an imported game with executable `true`) so nothing actually starts.
3. Launch "Zelda" from its hover Play button. **Verify**: within 1 second "Zelda" is in the first position.
4. Wait at least one second, then launch "Astro" by opening its details page and pressing Play. Go back. **Verify**: "Astro" is first and "Zelda" second.
5. Launch "Astro" again. **Verify**: the order does not change and the grid does not flicker.
6. Type part of "Zelda" into the search bar, then launch "Zelda" from the results. **Verify**: "Zelda" is first in the results and the search text is still there.
7. Inspect `~/.local/share/cartridges/last-played.json` (or the Flatpak equivalent under `~/.var/app/<app-id>/data/cartridges/`). **Verify**: both `game_id` keys are present with timestamps one or more seconds apart.

### Scenario 9: Persistence, Merge, and Other Sort Modes (Amendment)
Covers User Story 5 scenarios 4-6 and 8, FR-015, FR-019, FR-021, SC-009.
1. Note the "Last Played" order, close Cartridges, and reopen it. **Verify**: the order is identical.
2. Enable "Exit After Launching Games" in Preferences, launch a game, and reopen Cartridges. **Verify**: that game is first.
3. With a Steam game whose manifest `LastPlayed` is older than a Cartridges launch of the same game, restart. **Verify**: the game keeps the newer Cartridges time. Then play it from Steam directly so Steam writes a newer `LastPlayed`, restart Cartridges, and **verify** the newer Steam time is used.
4. Switch to sort mode "A-Z" and launch a game in the middle of the list. **Verify**: its position does not change.
5. Replace `last-played.json` with invalid content (e.g. `not json`) and start Cartridges. **Verify**: the library loads normally with no error; launched games simply start without recorded times.

### Scenario 10: Scroll and Focus Stability (Amendment)
Covers the spec edge case "Launching a game while scrolled far down the library".
1. With "Last Played" sort and a library large enough to scroll, scroll far down.
2. Focus a card with the keyboard (Tab / arrow keys) and press Enter with "Cover Image Launches Game" enabled.
3. **Verify**: the grid does not jump to the top, and keyboard focus is not moved to an unrelated card. Record the observed behavior; if focus is lost, follow the fallback in research.md section 9.

### Scenario 11: Launch Survives a Failed Save (Follow-up)
Covers User Story 5 scenarios 9-11, FR-022 to FR-025, SC-010.
1. Make the data directory unwritable (for example `chmod a-w ~/.local/share/cartridges`, or a Flatpak override that makes it read-only). Select sort mode "Last Played".
2. Launch a game that is not first, using a harmless executable. **Verify**: the game starts, the "Launched <name>" toast appears, no error dialog is shown, and the game moves to the first position.
3. Open that game's details. **Verify**: the "Last played" label reads as recent.
4. Run Cartridges from a terminal and check the output. **Verify**: exactly one warning per failed launch naming the file and the reason, and no `last-played.json.tmp` in the data directory.
5. Enable "Exit After Launching Games" and launch again. **Verify**: the game starts and the application exits normally.
6. Restore write permission, launch another game, and reopen Cartridges. **Verify**: both the earlier and the new game appear in the saved file and the order matches.
7. With a valid `last-played.json` present, repeat step 2 with the directory unwritable and restart. **Verify**: the earlier history is unchanged.

### Scenario 12: Show or Hide Game Titles (Amendment)
Covers User Story 6, FR-026 to FR-030, SC-011, SC-012.
1. Start with a fresh settings state (`gsettings reset page.samuelm333.Cartridges show-game-titles`, adjusting the schema path for a local build). **Verify**: titles are shown under every cover.
2. Open Preferences, General. **Verify**: a "Show Game Titles" switch with its subtitle is present in an "Appearance" group and is on.
3. Turn the switch off while the library is visible behind the dialog. **Verify**: titles disappear from all covers immediately, except for any game without a cover (its title stays).
4. Hover a card, launch a game, search, change the sort mode, and open a collection. **Verify**: everything behaves exactly as with titles shown; open a game's details and **verify** its name is still shown.
5. With Orca or the GTK inspector accessibility view, focus a card. **Verify**: the card reports the game name.
6. Close and reopen Cartridges. **Verify**: titles are still hidden. Turn the switch on and **verify** titles return immediately.
7. With a library large enough to scroll, toggle the switch. **Verify**: the grid reflows evenly with no flicker or lost scroll position (see research.md section 11 for the fallback).

## 5. Automated Quality Gate Checks

```bash
# Code formatting, linting, and blueprint compilation checks
pre-commit run --all-files

# Pyright static analysis in strict mode
pyright

# Meson test suite execution
ninja -C _build test

# Play-history unit checks, including save-failure cases (no GTK needed)
python3 tests/test_play_history.py
```
