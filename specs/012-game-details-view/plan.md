# Implementation Plan: Game Details View

**Branch**: `feat/012-game-details-view` | **Date**: 2026-10-11 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/012-game-details-view/spec.md`

## Summary

The details view already works (spec user stories 1, 3, and 4), so this plan only records it and changes one thing: where toasts are shown (user story 2). Today the window has a single `Adw.ToastOverlay`, inside the library page, so a toast raised while the details page is showing (most visibly "Launched <game name>") is added behind the details page and never seen.

The change gives the details page its own `Adw.ToastOverlay` around its scrolled content, the same place the library page has one. `Window.send_toast` stays the only entry point and picks the overlay of the page that is visible when it is called. When the details page starts to leave (`hiding`), it dismisses its toasts with `Adw.ToastOverlay.dismiss_all()`. Hide and Remove already pop the details page before they send their toast, and a prototype confirmed that the navigation view reports the library as visible as soon as the pop happens (research R1), so their Undo toasts keep appearing in the library with no extra code.

No caller of `send_toast` changes, and nothing new is stored.

## Technical Context

**Language/Version**: Python 3 (the GNOME 50 runtime's), Blueprint for UI templates

**Primary Dependencies**: GTK 4, libadwaita 1.9 (GNOME 50 runtime; `Adw.ToastOverlay.dismiss_all()` needs 1.7 or later), PyGObject

**Storage**: N/A (toasts are not stored)

**Testing**: The existing meson test scripts under `tests/` still run. No new automated test: see research R4. The new behavior is checked with quickstart scenarios in a development build.

**Target Platform**: Linux desktop (Flatpak first), GNOME HIG

**Project Type**: Desktop application

**Performance Goals**: The launch toast is visible in the details view within 100 ms of pressing Play (SC-001); choosing the overlay is a single comparison per toast

**Constraints**: One toast entry point (`Window.send_toast`) for all callers; the details page keeps its current layout; no change to the Undo shortcut (`win.undo`, Ctrl+Z)

**Scale/Scope**: 3 source files changed (`cartridges/ui/game-details.blp`, `cartridges/ui/game_details.py`, `cartridges/ui/window.py`)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Assessment | Status |
|-----------|------------|--------|
| I. Strict typing and QA | The new template child is annotated (`Adw.ToastOverlay`); `send_toast` keeps its signature. Pyright strict and Ruff run on the changed files. | PASS |
| II. Modular game sources | Not touched. | PASS |
| III. Blueprint-driven UI | The overlay is declared in `game-details.blp` and bound with `Gtk.Template.Child()`; the `hiding` handler is a template callback. No procedural widget construction. | PASS |
| IV. Libadwaita patterns and GNOME HIG | One `Adw.ToastOverlay` per page, wrapping the `Adw.ToolbarView` content, is the same structure the library page already uses and the pattern in `adwaita-1-demo`. Toasts stay non-blocking. | PASS |
| V. Resource and asset sandboxing | Not touched. | PASS |
| VI. Restrained emoji use | No emoji in code or documents; `check-emojis.py` runs before commit. | PASS |
| VII. No silent failures | No new `except` clauses. | PASS |
| Quality gates item 5 (tests) | Every existing test stays registered. The new behavior is widget state that needs a display; CI has none (research R4), so it is covered by quickstart scenarios, as `specs/005-game-list-view/` did for user story 6. | PASS (justified) |
| Workflow | Branch `feat/012-game-details-view` from `main`; commits with `uv run git commit`; pull request into `main`. | PASS |

Re-check after Phase 1: the contract and quickstart add no new dependency, storage, or public surface beyond one template child. Still PASS.

## Project Structure

### Documentation (this feature)

```text
specs/012-game-details-view/
├── spec.md
├── plan.md              # This file
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/
│   └── toast-routing.md # Phase 1
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 (/speckit-tasks, not created here)
```

### Source Code (repository root)

```text
cartridges/ui/
├── game-details.blp   # add Adw.ToastOverlay toast_overlay around the ToolbarView content; hiding => $_dismiss_toasts()
├── game_details.py    # toast_overlay template child; _dismiss_toasts() callback calls dismiss_all()
└── window.py          # send_toast() adds the toast to the visible page's overlay
```

Unchanged on purpose: `cartridges/ui/games.py`, `collections.py`, `preferences.py`, and `cartridges/application.py` keep calling `send_toast` as they do now.

**Structure Decision**: The window owns toasts today and stays the single entry point, because every caller already goes through it and the Undo history (`_history`, Ctrl+Z) lives there. Each page owns the overlay it shows toasts in, because that overlay is part of the page's layout. The window only decides which page is visible, which it already knows through `navigation_view`.

## Complexity Tracking

No constitution violations to justify.
