# Technical Research: Main Game List View and Cover Interactions

**Branch**: `feat/005-game-list-view`
**Feature**: `specs/005-game-list-view`
**Date**: 2026-10-06

## 1. Hover Action Buttons Layout and Transition

### Problem Statement
In `cartridges-main`, hovering over a game card revealed two circular floating buttons at the top of the cover: a top-left action button (play/info) and a top-right contextual menu button ("three dots"). In the current codebase, the primary action button was temporarily replaced with a centered pill button at the bottom of the card. We need to restore the original, proven hover button design while integrating with the current Blueprint architecture.

### Research & Decisions
- **Decision**: Position two circular overlay buttons at the top corners of the cover overlay in `cartridges/ui/game-item.blp`:
  - Top-left (`halign: start`, `valign: start`, `margin-top: 6`, `margin-start: 6`): Action button (Play / Info).
  - Top-right (`halign: end`, `valign: start`, `margin-top: 6`, `margin-end: 6`): MenuButton with `view-more-symbolic` icon.
- **Rationale**: Restores visual harmony and unifies the top bar of the cover image. Placing buttons at the top prevents obscuring the bottom half of vertical artwork and maintains consistency with GNOME card patterns.
- **Alternatives Considered**:
  - *Bottom pill button (current)*: Rejected because it obscures the bottom center of the artwork, creates a heavier visual footprint, and diverges from the user-requested `cartridges-main` design.
  - *Revealer widgets vs. CSS transition*: In `cartridges-main`, `Gtk.Revealer` widgets with `crossfade` were used inside the overlay. In the current rewrite, CSS transitions (`opacity` and `transform`) via the `.hidden` style class are utilized on `#game-item overlay > button` and `#game-item overlay > menubutton > button`. Both achieve smooth fading without extra widget nesting; keeping the CSS transition pattern or aligning with revealer child properties maintains responsiveness and high performance.

## 2. Dynamic Action and Icon Swapping ("Cover image launches game")

### Problem Statement
When the user toggles "Cover Image Launches Game" in Preferences (`cover-launches-game` GSettings key), the behavior of clicking the cover and clicking the hover action button must invert immediately without needing an app restart:
- When disabled (default): Cover click opens details; hover button displays Play icon (`media-playback-start-symbolic`) and launches the game.
- When enabled: Cover click launches game; hover button displays Info icon (`help-about-symbolic`) and opens game details.

### Research & Decisions
- **Decision**: Update `GameItem._update_action_button` in `cartridges/ui/game_item.py`:
  - When `cover-launches-game` is true:
    - Button icon: `help-about-symbolic`
    - Button tooltip: `_("Details")`
    - Button action name: `game.details`
  - When `cover-launches-game` is false:
    - Button icon: `media-playback-start-symbolic`
    - Button tooltip: `_("Play")`
    - Button action name: `game.play`
- **Cover Click Binding**: Already implemented in `Window._show_details` in `cartridges/ui/window.py` where `single-click-activate` on the `GridView` checks `SETTINGS.get_boolean("cover-launches-game")` and either invokes `game.play()` or navigates to details.
- **Alternatives Considered**:
  - *Hardcoding two separate button widgets in the template and toggling visibility*: Rejected as unnecessary duplication; changing the icon, tooltip, and action-name on a single button widget is cleaner, less memory-intensive, and eliminates widget sync bugs.

## 3. Popover Menu Persistence on Hover Exit

### Problem Statement
When the user clicks the three-dots menu button, the pointer might drift outside the game item card boundaries while selecting a menu entry. The menu button must not disappear or collapse while its popover menu remains open.

### Research & Decisions
- **Decision**: Track `options.props.active` in `GameItem._reveal_buttons`.
  - The reveal condition for the menu button evaluates `contains_pointer or self.options.props.active`.
  - As long as `options.props.active` is true, the menu button remains visible and interactive.
- **Rationale**: Matches the implementation in `cartridges/ui/game_item.py` and `cartridges-main`, preventing sudden dismissal of controls during contextual interactions.

## 4. Accessibility, Focus Outlines, and Controller Navigation

### Problem Statement
Users navigating via keyboard or connected gamepads must be able to focus cards and trigger primary and secondary actions without requiring mouse hover.

### Research & Decisions
- **Decision**:
  - The `GridView` handles focus navigation across game cards with visible focus outlines (`focus-visible`).
  - Activating a focused item via keyboard (`Return` / `Space`) triggers `GridView` item activation, respecting `cover-launches-game`.
  - Contextual actions remain accessible via standard keyboard shortcuts (`Ctrl+N`, `Delete` for remove where applicable) and context menu keys (`Menu` key or `Shift+F10`).
  - Gamepad navigation leverages the existing `gamepads.py` monitor and directional navigation.

## 5. Dismissable Game Launch Toast Notification & Internationalization

### Problem Statement
When a game is launched from the UI, the user needs clear, non-intrusive feedback confirming that the launch command was dispatched, without blocking the interface. The notification must display the localized message "Launched <game name>" and support translation across diverse grammatical structures.

### Research & Decisions
- **Decision**:
  - Introduce a centralized `play(game: Game) -> None` function in `cartridges/ui/games.py`.
  - When invoked, it calls `game.play()` and dispatches an in-app toast via `_window().send_toast(_("Launched {}").format(game.name))`.
  - Provide an explicit translation comment `# Translators: {} is the name of the game that was launched` immediately before the gettext call so that GNU gettext extracts context for translators.
  - Update `GameActions` (`"play"` action entry) and `Window._show_details` (cover click when `cover-launches-game` is true) to call `games.play(game)`.
- **Rationale**:
  - `Window.send_toast` already integrates with `Adw.ToastOverlay` and creates an `Adw.Toast(title=title, use_markup=False)`.
  - In Libadwaita, `Adw.Toast` is dismissable by default (via user swipe/interaction or automatically fading after the system timeout).
  - Placing `play(game)` in `cartridges/ui/games.py` follows the established pattern of `hide(game)`, `unhide(game)`, and `remove(game)` in the same module.
  - Using `{}` placeholder formatting is consistent with existing localized toast strings in Cartridges (`_("{} hidden")`, `_("{} unhidden")`, `_("{} removed")`), allowing translators to position the game name at the beginning, middle, or end of the translated sentence.
- **Alternatives Considered**:
  - *Dispatching toast from domain model (`cartridges/games.py`)*: Rejected because domain model objects should not import UI widgets or window controllers, preserving clean architecture (Constitution Principle II).
  - *Displaying system desktop notifications via libnotify/portal*: Rejected as too disruptive for standard game launches where the main application window is already in focus.
