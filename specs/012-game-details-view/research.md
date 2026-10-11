# Research: Game Details View

## R1. Is the library the visible page as soon as the details page pops?

Hide and Remove set `game.hidden` or `game.removed`. The details page listens to those properties and activates `navigation.pop` (`cartridges/ui/game_details.py`, the `game_signals` loop in `__init__`). Then the action sends its toast. If the navigation view still reported the details page as visible during the pop animation, the Undo toast would go to the details overlay and be dismissed with it.

A prototype run in `gtk-dev` (libadwaita 1.9.4) pushed a details page onto an `Adw.NavigationView`, then activated `navigation.pop`, and printed this:

```text
after push: details
after pop (sync): games ['hiding']
after transition: games ['hiding', 'hidden']
```

- **Decision**: Pick the overlay from `navigation_view.props.visible_page` when `send_toast` is called. Do not special-case Hide or Remove.
- **Rationale**: `visible_page` switches when the pop happens, so toasts sent after a pop already go to the library (FR-012).
- **Alternatives considered**: Passing the target view from each caller. That touches every caller and duplicates what the navigation view already knows.

## R2. When should the details page dismiss its toasts?

The prototype shows `hiding` is emitted when the pop happens and `hidden` only after the slide animation ends.

- **Decision**: Dismiss on `hiding`, using `Adw.ToastOverlay.dismiss_all()`.
- **Rationale**: The toast leaves with the page instead of lingering during the slide, and nothing from the visit is left to show when a details page is opened again (FR-011). `dismiss_all()` exists since libadwaita 1.7; the Flatpak runtime is GNOME 50 (libadwaita 1.9).
- **Alternatives considered**: `hidden`, which leaves the toast on screen while the page slides away. Keeping the toasts and letting them time out, which can show "Launched A" when the details of game B open next. Tracking each toast and calling `Adw.Toast.dismiss()`, which needs bookkeeping that `dismiss_all()` already does.

## R3. Where does the details page's overlay go?

- **Decision**: Wrap the `content:` of the details page's `Adw.ToolbarView` (the `ScrolledWindow`) in `Adw.ToastOverlay toast_overlay`.
- **Rationale**: The library page puts its overlay in the same place, as the `Adw.ToolbarView` content (`window.blp`), so toasts sit at the same height on both pages, under the header bar. The blurred background picture stays behind everything.
- **Alternatives considered**: Wrapping the whole page (`Adw.BreakpointBin` child). That also works, but it places the overlay outside the toolbar view and differs from the library page.

## R4. Can the new behavior be tested automatically?

- **Decision**: No new automated test. Check it with quickstart scenarios 1 to 5.
- **Rationale**: The behavior is which widget shows a toast. Checking it needs real widgets, and `Window` and `GameDetails` load their templates from the compiled GResource. CI runs `ninja -C _build test` in a container with no display (`.github/workflows/ci.yml`), and no existing test creates widgets. The decision itself is a single comparison in `send_toast`, and R1 confirmed the one timing it depends on. `specs/005-game-list-view/` made the same choice for its widget-only user story 6.
- **Alternatives considered**: A test that loads `_build/cartridges/ui/ui.gresource` and creates the window. It would need a display server in CI (for example a headless Wayland compositor), which is a new CI dependency for one line of logic.

## R5. Other callers and the Undo shortcut

Callers of `send_toast`: `cartridges/ui/games.py` (launch, hide, unhide, remove, could-not-save), `cartridges/ui/collections.py` (collection removed), `cartridges/ui/preferences.py` (cover and library messages), and `cartridges/application.py` (debug logs).

- **Decision**: Leave them unchanged. Every toast follows the same rule, as the spec assumes.
- **Rationale**: The rule is about where the user is looking, not about who sent the toast. The Undo history (`Window._history`) and Ctrl+Z (`win.undo`) do not depend on the overlay, so Undo still works for a toast shown in either page.
- **Note**: A Preferences action with Undo (removing all games) while the details page is showing puts its toast in the details view; when the user leaves, the toast is dismissed, but Ctrl+Z still undoes it, as Undo works today after a toast times out.
