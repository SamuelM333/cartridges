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

## 5. Automated Quality Gate Checks

```bash
# Code formatting, linting, and blueprint compilation checks
pre-commit run --all-files

# Pyright static analysis in strict mode
pyright

# Meson test suite execution
ninja -C _build test
```
