# Quickstart: Validating Game Import

**Feature**: [spec.md](spec.md) | **Contracts**: [contracts/ui-contracts.md](contracts/ui-contracts.md)

## Prerequisites

- Work inside the `gtk-dev` Distrobox container (Constitution: Development Environment).
- Build and run the development profile:

```sh
meson setup _build -Dprofile=development   # first time only
ninja -C _build
meson devenv -C _build cartridges
```

- At least one launcher with installed games (Steam is easiest). For removal checks, a launcher where you can install and uninstall a small game, or a `.desktop` file you can create and delete in `~/.local/share/applications/` with `Categories=Game;`.
- To reset settings between scenarios: `gsettings reset-recursively page.samuelm333.Cartridges.Devel` (use `GSETTINGS_SCHEMA_DIR=_build/data` if the schema is not installed).

## Automated checks

```sh
pre-commit run --all-files
pyright
ninja -C _build test
python tests/test_importer.py
python tests/test_settings.py
```

Expected: all pass. `test_importer.py` covers the reconciliation invariants in [data-model.md](data-model.md) section 4 and the location rules in section 6.

## Scenario 1: Import Now picks up a new game (US1, FR-006, FR-007, SC-001)

1. Start Cartridges. Note the number of games under one source in the sidebar.
2. Create a new desktop entry game (or install a game in a launcher).
3. Open Preferences (Ctrl+,) > Import.
4. Expected: "Import Now" is the first row on the page, above Behavior.
5. Press **Import**.
6. Expected: the button becomes a spinner, then returns. A toast says "1 new game imported". The game is in the library and its source's sidebar count went up. No restart.

## Scenario 2: Running state and no double start (FR-008, edge case "Preferences closed")

1. Press **Import** and immediately try to press it again.
2. Expected: the button is replaced by a spinner and cannot be pressed.
3. Press Import again, then close Preferences right away.
4. Expected: the toast still appears in the main window when the import finishes.
5. Reopen Preferences during a long import (Steam with many games).
6. Expected: the row shows the spinner.

## Scenario 3: Idempotence and user state (FR-011, SC-003)

1. Hide one launcher game and edit another game's name in the details page.
2. Press **Import** 10 times, waiting for each to finish.
3. Expected: each toast says "No new games found". Game count unchanged, no duplicates, the hidden game stays hidden, the edited name stays.
4. Expected: manually added games ("Added" source) are unchanged.

## Scenario 4: Uninstalled games disappear (FR-016)

1. Delete the desktop entry created in Scenario 1 (or uninstall the game).
2. Press **Import**.
3. Expected: the game is gone from the library. The Behavior group has no "Remove Uninstalled Games" switch.

## Scenario 5: Import Games on Startup (US2, FR-017, FR-018, SC-006)

1. Reset settings. Open Preferences > Import.
2. Expected: "Import Games on Startup" is on by default.
3. Turn it off and restart Cartridges.
4. Expected: only manually added games are shown (or the empty state). Launcher sources are absent from the sidebar.
5. Optional: run with `strace -f -e trace=openat` and confirm no launcher paths (for example `steamapps`, `pga.db`) are opened at startup.
6. Press **Import** in Preferences.
7. Expected: launcher games appear.
8. Turn the switch back on and restart. Expected: launcher games appear at startup, as before this feature.

## Scenario 6: Source settings take effect (US3, FR-013, FR-014, FR-015, SC-004)

For each row below, change the setting, press **Import**, and check the library. Then revert and import again to confirm the games return.

| Setting | Expected after Import |
|---------|-----------------------|
| Steam off | No Steam games, Steam leaves the sidebar. |
| Steam location set to a second, valid Steam data directory | Games from that directory only. |
| Lutris "Import Steam Games" on | Lutris games using the Steam runner appear under Lutris. |
| Heroic "Import Amazon Games" off | No Amazon games under Heroic. |
| Flatpak "Import Game Launchers" on | Launchers such as Steam or Lutris Flatpaks appear. |
| Desktop Entries off | No desktop-entry games. |

## Scenario 7: Responsiveness (FR-009, SC-002)

1. With a large Steam library, press **Import**, then immediately scroll the main window and type in the search field.
2. Expected: no visible freeze. To measure, open the GTK Inspector (Ctrl+Shift+D), enable Visual > Show frame rate, and confirm no stall longer than 250 ms.
3. If Steam's metadata parse exceeds the budget, record the duration in research.md section 4 and apply the noted follow-up.

## Scenario 8: Failure isolation (FR-005, edge case "one source fails")

1. Make a source unreadable, for example `chmod 000` on the Lutris `pga.db`.
2. Press **Import**.
3. Expected: other sources import normally; Lutris keeps the games it had; a toast appears. Restore permissions afterward.

## Scenario 9: Regression check (SC-005)

1. On `main` before this feature, start Cartridges with default settings and note per-source counts and a few games' "last played" and "added" values.
2. On the feature branch, reset settings and start again.
3. Expected: same games, same counts, same "last played" values. "Added" values for launcher games that do not report one are the scan time, so they differ between runs on both branches; compare only games whose launcher reports a date.
