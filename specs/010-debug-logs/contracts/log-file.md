# Contract: Log Files

Readers of this contract: users attaching logs to bug reports, and maintainers reading them.

## Location

| Environment | Folder |
|-------------|--------|
| Flatpak | `~/.var/app/<APP_ID>/.local/state/cartridges/logs/` |
| Host, default | `~/.local/state/cartridges/logs/` |
| Host, `XDG_STATE_HOME` set | `$XDG_STATE_HOME/cartridges/logs/` |

Files: `<APP_ID>.log` (current) and `<APP_ID>.log.1` to `<APP_ID>.log.4` (archives, `.1` newest).

## Line format

```text
2026-10-11 14:03:27,512 [INFO] cartridges.logs: Cartridges nightly-abc1234 page.samuelm333.Cartridges, flatpak=yes, Python 3.13.5, GTK 4.20.1, Adwaita 1.8.0, linux
2026-10-11 14:03:27,640 [DEBUG] cartridges.sources: Read 12 games from steam
2026-10-11 14:03:28,101 [WARNING] cartridges.ui.preferences: Error fetching cover for Portal 2: HTTP Error 502
```

Guarantees:

1. Every run that has logging on starts with exactly one header line from `cartridges.logs` (FR-008). Turning the switch on mid-run writes a header at that point.
2. The stored SteamGridDB API key never appears; where it would, `[redacted]` appears instead (FR-013).
3. Terminal (stderr) output is unchanged in content and level by this feature (FR-017).
4. Total size per app ID stays at or below about 5 MiB (FR-010).
5. Unhandled exceptions from callbacks, worker threads, and unraisable errors are written at `CRITICAL` with their traceback while logging is on; the terminal still shows Python's usual report.

Not guaranteed: the wording of individual messages, which may change between versions.
