# Quickstart: Validating Collections

**Feature**: [spec.md](spec.md) | **Contracts**: [contracts/](contracts/)

All build and check commands run inside the `gtk-dev` container.

## Automated checks

```sh
meson setup _build -Dprofile=development && ninja -C _build
env -u DISPLAY -u WAYLAND_DISPLAY ninja -C _build test   # runs test_collections with the others
uv run pre-commit run --all-files
```

Expected: every meson test passes, including `test_collections`, and every hook passes.

## Manual scenarios

Run the development build from a scratch install, with scratch settings and data folders, so your real library is not touched. The keyfile settings backend keeps settings across restarts (needed for scenario 13):

```sh
PREFIX="$(mktemp -d)"
meson setup _build_run -Dprofile=development --prefix="$PREFIX" && ninja -C _build_run install
export PYTHONPATH="$(dirname "$(find "$PREFIX" -type d -name cartridges -path '*site-packages*' | head -1)")"
export XDG_DATA_DIRS="$PREFIX/share:${XDG_DATA_DIRS:-/usr/share}" GSETTINGS_SCHEMA_DIR="$PREFIX/share/glib-2.0/schemas" GSETTINGS_BACKEND=keyfile
export XDG_CONFIG_HOME="$(mktemp -d)" XDG_DATA_HOME="$(mktemp -d)" XDG_CACHE_HOME="$(mktemp -d)"
"$PREFIX/bin/cartridges"
```

Start the app again with the last line, in the same shell, whenever a scenario says to restart.

Add three games (Ctrl+N): "Steam Tool", "Lutris Tool", and "Normal Game".

| # | Steps | Expected | Spec |
|---|-------|----------|------|
| 1 | Sidebar "New Collection", name it "Launchers", pick an icon, Apply | "Launchers" appears under Collections with that icon; the selection stays where it was | US1 |
| 2 | Leave the name empty in the dialog | Apply stays disabled | US1 |
| 3 | On "Steam Tool" open the three-dots menu, turn "Launchers" on, close the menu; do the same for "Lutris Tool" | Both appear in "Launchers"; "Normal Game" does not | US2 |
| 4 | Hide "Steam Tool" and "Lutris Tool" (menu, Hide) | They leave All Games; a toast offers Undo | baseline |
| 5 | Open "Launchers" with the preference off (default) | "No Games in Launchers" | US4/2 |
| 6 | Preferences > General > Behavior: hover "Hidden games show in Collections" | Tooltip "Useful for hiding launchers and tools"; the switch is off | US4/1 |
| 7 | Turn the switch on while "Launchers" is open | Both tools appear at once, without a restart | US4/3 |
| 8 | Open All Games | Neither tool is listed | US4/4 |
| 9 | In "Launchers" search for "Steam" | "Steam Tool" is listed | US4/6 |
| 10 | In "Launchers" open the menu of "Steam Tool" | It offers Unhide, not Hide; Unhide keeps it in "Launchers" and shows it in All Games | US4/7 |
| 11 | Hide "Normal Game" after adding it to "Launchers" | It stays listed in "Launchers" and leaves All Games | US4/8 |
| 11b | With the preference on and "Launchers" open, turn on Show Hidden Games (Ctrl+H) | Only the hidden games of "Launchers" are listed ("Normal Game" leaves the view); turn it off again and it returns | US4/5 |
| 12 | Turn the switch off while "Launchers" is open | The hidden games leave the view at once | edge case |
| 13 | Turn it on, quit, and start again | The switch is still on and "Launchers" still lists the hidden games | US3, US4/9 |
| 14 | Remove "Launchers" (context menu), then Undo | It leaves and comes back with both tools | US1 |
| 15 | Preferences > Danger Zone > Reset App (development builds); the app closes; start it again and open Preferences | The switch is off and the collections are gone | edge case |

The real window matters for scenarios 7, 11b, 12, and 13 because `tests/test_collections.py` builds the filter tree in Python; a mismatch with `window.blp` would show up only here.
