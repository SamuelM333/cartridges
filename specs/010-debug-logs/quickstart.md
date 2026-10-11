# Quickstart: Validating Debug Logs

**Feature**: [spec.md](spec.md) | **Contracts**: [contracts/](contracts/)

All build and check commands run inside the `gtk-dev` Distrobox container.

## Prerequisites

```sh
meson setup _build -Dprofile=development   # or reuse an existing _build
ninja -C _build
```

Set a throwaway state folder so checks do not touch your real logs:

```sh
export XDG_STATE_HOME="$(mktemp -d)"
LOGS="$XDG_STATE_HOME/cartridges/logs"
```

## Automated checks

```sh
python3 tests/test_logs.py      # rotation, redaction, toggling, unwritable folder
python3 tests/test_settings.py  # schema now contains debug-logs
pre-commit run --all-files
pyright
```

Expected: all exit with status 0.

## Manual scenarios

Run the app with `meson devenv -C _build cartridges` (or the Devel Flatpak).

| # | Steps | Expected | Spec |
|---|-------|----------|------|
| 1 | Fresh state; open Preferences > General | "Debug Logs" is off; `ls "$LOGS"` shows nothing | FR-002, SC-007 |
| 2 | Turn "Debug Logs" on | `<APP_ID>.log` appears with one header line naming version and `development` | FR-005, FR-008 |
| 3 | Run Import Now | `DEBUG` lines from `cartridges.*` loggers with timestamps; terminal shows only what it did before | FR-004, FR-007, FR-017 |
| 4 | Quit and relaunch | Second header line; startup import lines follow it | FR-003, FR-006 |
| 5 | Turn the switch off; run an import | File size no longer grows; files still present | FR-012 |
| 6 | Click "Open Logs Folder" | File manager opens on `$LOGS` (create it first by deleting the folder to test the empty case) | FR-011 |
| 7 | Set an SGDB key, turn logging on, run "Update Covers" | `grep -r "<key>" "$LOGS"` finds nothing | FR-013, SC-005 |
| 8 | `chmod a-w "$LOGS"` and remove the log file, then turn logging on | One toast "Could not save debug logs"; app keeps working; switch stays on | FR-014, SC-004 |
| 9 | `gsettings set page.samuelm333.Cartridges.Devel debug-logs true` while running | Logging starts without restart | FR-005 |

Rotation at full size (1 MiB) is covered by the automated test with a small limit; to check manually, run with logging on and `du -sh "$LOGS"` after heavy use: never above about 5 MiB.

## Build types

- Development: `-Dprofile=development`, header says `development`.
- Nightly: `meson setup _build_nightly -Dnightly=true`, header says `nightly`.
- Release: defaults, header says `release`.
The switch and folder behave the same in all three (FR-015).
