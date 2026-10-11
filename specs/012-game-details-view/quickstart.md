# Quickstart: Game Details View

Validation guide for [spec.md](spec.md). Routing rules are in [contracts/toast-routing.md](contracts/toast-routing.md).

## Prerequisites

Inside the `gtk-dev` container, from the repository root:

```sh
meson setup _build --reconfigure
ninja -C _build
ninja -C _build test
```

Run the development build with a library that has at least two games, one of them with a developer and a last-played date:

```sh
_build/cartridges/cartridges
```

Use a game whose executable is harmless to launch (for example a manually added game with the executable `true`), so launches can be repeated.

## Toast scenarios (user story 2)

1. **Launch from details**: Open a game's details (click its cover). Press Play. Expected: "Launched <game name>" appears at the bottom of the details view.
2. **Leave with a toast showing**: Right after scenario 1, press the back button. Expected: the toast leaves with the details page and is not shown in the library.
3. **Library toast stays in the library**: In the library, launch a game with its Play button, then open any game's details while the toast is still showing. Expected: no toast over the details view. Go back quickly: the library toast may still be showing if it has not timed out.
4. **No stale toast**: Launch from one game's details, go back, and open another game's details. Expected: no "Launched" toast about the first game.
5. **Hide and remove from details**: Open a visible game's details and press Hide. Expected: the view returns to the library and "{name} hidden" with Undo appears there; Undo brings the game back. Repeat with Remove (button, then the Delete key).
6. **Could not save**: Optional, needs a read-only data directory. Edit a manually added game and apply. Expected: the warning toast appears in the details view.

## Recorded behavior (user stories 1, 3, 4)

7. **View**: Open the details of the game with a developer, then of one without. Expected: developer shown only for the first; dates read "Last played: ..." and "Added: ..."; a never-played game shows "Never".
8. **Narrow window**: Resize below 700 pixels wide. Expected: cover, text, and actions stack vertically and are centered.
9. **Edit and apply**: Press Edit, change the title, press Enter. Expected: the details show the new title and so does the library. Clear Title or Executable: Apply becomes unavailable.
10. **Edit and cancel**: Press Edit, change fields and delete the cover, press Escape. Expected: nothing changed, the cover is back.
11. **Collections and Search On**: Open Collections (expected: "New Collection" and the collection toggles), then pick a site from Search On (expected: the site's search for the title opens in the browser).
12. **Back and Escape**: From the details view (not editing), press Escape. Expected: the library is shown again.

Record any scenario that fails or could not be performed in the pull request description.
